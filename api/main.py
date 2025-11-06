from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Response
from pydantic import BaseModel, Field
from pydantic_models import QueryInput, QueryResponse, DocumentInfo, DeleteFileRequest, TestPDFInfo, TestGenerationRequest, TestGenerationResponse, DifficultyLevel, QuestionType
from langchain_utils import get_rag_chain
from db_utils import (
    insert_application_logs, get_chat_history, get_all_documents, insert_document_record, 
    delete_document_record, insert_test_pdf_record, get_all_test_pdfs, delete_test_pdf_record,
    get_test_pdf_content,check_filename_uniqueness
)
from chroma_utils import vectorstore,index_document_to_chroma, delete_doc_from_chroma,check_document_uniqueness, load_and_split_document
import os
import sys
import uuid
import logging
import shutil
from typing import Optional,Tuple
from fastapi.middleware.cors import CORSMiddleware

# Добавляем путь к папке app в Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from xml_utils import load_tasks_from_xml, get_tasks, get_preview_tasks

logging.basicConfig(filename='app.log', level=logging.INFO)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "OneClickTest API is running", "status": "OK"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "OneClickTest API"}

@app.get("/xml-subjects")
def get_xml_subjects():
    """Получить список всех предметов из XML базы"""
    try:
        tasks_dict = load_tasks_from_xml()
        subjects = list(tasks_dict.keys())
        print(f"Found subjects: {subjects}") 
        return {"subjects": subjects}
    except Exception as e:
        logging.error(f"Error getting XML subjects: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting XML subjects: {str(e)}")

@app.get("/xml-topics/{subject}")
def get_xml_topics(subject: str):
    """Получить список тем для указанного предмета"""
    try:
        tasks_dict = load_tasks_from_xml()
        if subject not in tasks_dict:
            print(f"Subject '{subject}' not found")
            return {"topics": []}
        topics = list(tasks_dict[subject].keys())
        print(f"Found topics for {subject}: {topics}") 
        return {"topics": topics}
    except Exception as e:
        logging.error(f"Error getting XML topics: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting XML topics: {str(e)}")

@app.get("/difficulty-levels")
def get_difficulty_levels():
    """Получить доступные уровни сложности"""
    return [{"value": level.value, "label": level.value} for level in DifficultyLevel]

@app.get("/question-types")
def get_question_types():
    """Получить доступные типы вопросов"""
    return [{"value": qtype.value, "label": qtype.value} for qtype in QuestionType]

@app.get("/available-xml-questions")
def get_available_xml_questions(
    subject: str, 
    topic: Optional[str] = None,
    difficulty: Optional[str] = None,
    question_type: Optional[str] = None
):
    """Получить количество доступных вопросов по параметрам"""
    try:
        tasks = get_tasks(
            subject=subject,
            topic=topic,
            difficulty=difficulty,
            task_type=question_type
        )
        return {"available_questions": len(tasks)}
    except Exception as e:
        logging.error(f"Error counting available XML questions: {e}")
        raise HTTPException(status_code=500, detail=f"Error counting available XML questions: {str(e)}")

@app.get("/xml-questions-preview")
def preview_xml_questions(
    subject: str,
    topic: Optional[str] = None,
    difficulty: Optional[str] = None,
    question_type: Optional[str] = None,
    limit: int = 3
):
    """Получить предпросмотр реальных вопросов из XML базы"""
    try:
        tasks = get_tasks(
            subject=subject,
            topic=topic,
            difficulty=difficulty,
            task_type=question_type,
            limit=limit
        )
        
        preview_tasks = []
        for task in tasks:
            preview_tasks.append({
                "question": task.question,
                "type": task.type,
                "difficulty": task.difficulty,
                "answer": task.answer,
                "subject": task.subject,
                "topic": task.topic
            })
        
        return {"preview_tasks": preview_tasks}
    except Exception as e:
        logging.error(f"Error previewing XML questions: {e}")
        raise HTTPException(status_code=500, detail=f"Error previewing XML questions: {str(e)}")

# Новый эндпоинт для генерации тестов
@app.post("/generate-test")
def generate_test(request: TestGenerationRequest):
    try:
        session_id = request.session_id or str(uuid.uuid4())
        
        print(f"Generating test with params: {request.dict()}") 
        
        # Получаем XML вопросы если указаны параметры
        xml_questions_content = ""
        xml_questions_count = 0
        
        if request.xml_subject and request.xml_question_count > 0:
            print(f"Getting XML tasks for subject: {request.xml_subject}, topic: {request.xml_topic}")
            xml_tasks = get_tasks(
                subject=request.xml_subject,
                topic=request.xml_topic if request.xml_topic else None,
                difficulty=request.difficulty.value,  # Используем .value для enum
                task_type=request.question_type.value,  # Используем .value для enum
                limit=request.xml_question_count
            )
            
            print(f"Found {len(xml_tasks)} XML tasks")
            
            if xml_tasks:
                xml_questions_count = len(xml_tasks)
                xml_questions_content = "# Вопросы из базы данных\n\n"
                for i, task in enumerate(xml_tasks, 1):
                    xml_questions_content += f"## Вопрос {i}\n{task.question}\n\n"
                    if request.include_answers:
                        xml_questions_content += f"**Ответ:** {task.answer}\n\n"

        # Генерируем вопросы через AI если указан документ
        ai_questions_content = ""
        ai_questions_count = 0
        
        if request.document_id and request.question_count > xml_questions_count:
            ai_questions_count = request.question_count - xml_questions_count
            document_text = get_document_text(request.document_id)
            
            if document_text and ai_questions_count > 0:
                prompt = f"""
                Сгенерируйте тест на основе документа.
                Требования:
                - ТОЛЬКО это количество вопросов: {ai_questions_count}
                - Уровень сложности: {request.difficulty}
                - Формат вопросов: {request.question_type}
                - {"Включать ответы" if request.include_answers else "Не включать ответы"}
                - Используй ТОЛЬКО предоставленный текст документа
                
                Текст документа:
                {document_text}
                
                Сгенерируй тест строго по требованиям.
                """
                
                chat_history = get_chat_history(session_id)
                rag_chain = get_rag_chain(request.model.value)
                
                ai_response = rag_chain.invoke({
                    "input": prompt,
                    "chat_history": chat_history
                })
                ai_questions_content = ai_response['answer']

       # Объединяем содержимое
        if xml_questions_content and ai_questions_content:
            combined_content = xml_questions_content + "\n\n# Сгенерированные вопросы\n\n" + ai_questions_content
        elif xml_questions_content:
            combined_content = xml_questions_content
        else:
            combined_content = ai_questions_content

        # Логируем генерацию теста
        insert_application_logs(
            session_id, 
            f"Generate test: {request.question_count} questions, {xml_questions_count} from XML", 
            combined_content, 
            request.model.value
        )
        
        return {
            "test_content": combined_content,
            "session_id": session_id,
            "parameters": {
                "question_count": request.question_count,
                "difficulty": request.difficulty.value,
                "question_type": request.question_type.value,
                "include_answers": request.include_answers,
                "document_id": request.document_id,
                "xml_question_count": xml_questions_count,
                "ai_question_count": ai_questions_count,
                "xml_subject": request.xml_subject,
                "xml_topic": request.xml_topic
            }
        }
        
    except Exception as e:
        logging.error(f"Error generating test: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating test: {str(e)}")


@app.post("/upload-doc")
def upload_and_index_document(file: UploadFile = File(...)):
    allowed_extensions = ['.pdf', '.docx', '.html']
    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed types are: {', '.join(allowed_extensions)}")

    # Создаем временную директорию если не существует
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, f"temp_{uuid.uuid4()}_{file.filename}")

    try:
        # Сохраняем файл временно с проверкой
        file_content = file.file.read()
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
            
        with open(temp_file_path, "wb") as buffer:
            buffer.write(file_content)

        # Проверка размера файла
        file_size = os.path.getsize(temp_file_path)
        logging.info(f"File {file.filename} saved, size: {file_size} bytes")

        # Проверка уникальности имени файла в SQLite
        is_unique_filename, existing_filename = check_filename_uniqueness(file.filename)
        if not is_unique_filename:
            logging.warning(f"Document {file.filename} already exists in SQLite.")
            raise HTTPException(
                status_code=400,
                detail=f"Document with filename {file.filename} already exists in the database."
            )

        # Если документ уникален, продолжаем индексацию
        file_id = insert_document_record(file.filename)
        success = index_document_to_chroma(temp_file_path, file_id)

        if success:
            logging.info(f"File {file.filename} successfully uploaded and indexed with file_id {file_id}")
            return {"message": f"File {file.filename} has been successfully uploaded and indexed.", "file_id": file_id}
        else:
            # Если индексация не удалась, удаляем запись из БД
            delete_document_record(file_id)
            raise HTTPException(status_code=500, detail=f"Failed to process and index {file.filename}. The file may be corrupted or in an unsupported format.")
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Unexpected error during upload: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error during file processing: {str(e)}")
    finally:
        # Всегда очищаем временные файлы
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as e:
                logging.warning(f"Could not remove temp file {temp_file_path}: {e}")

@app.post("/chat", response_model=QueryResponse)
def chat(query_input: QueryInput):
    session_id = query_input.session_id or str(uuid.uuid4())
    logging.info(f"Session ID: {session_id}, User Query: {query_input.question}, Model: {query_input.model.value}")
    
    chat_history = get_chat_history(session_id)
    rag_chain = get_rag_chain(query_input.model.value)
    answer = rag_chain.invoke({
        "input": query_input.question,
        "chat_history": chat_history
    })['answer']

    insert_application_logs(session_id, query_input.question, answer, query_input.model.value)
    logging.info(f"Session ID: {session_id}, AI Response: {answer}")
    return QueryResponse(answer=answer, session_id=session_id, model=query_input.model)


@app.post("/upload-test-pdf")
def upload_test_pdf(
    file: UploadFile = File(...),
    document_id: Optional[int] = Form(None),
    session_id: Optional[str] = Form(None)
):
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension != '.pdf':
        raise HTTPException(status_code=400, detail="Only PDF files are allowed for test uploads.")

    pdf_content = file.file.read()
    file_id = insert_test_pdf_record(file.filename, document_id, session_id, pdf_content)
    return {"message": f"Test PDF {file.filename} has been successfully uploaded.", "file_id": file_id}

@app.get("/list-docs", response_model=list[DocumentInfo])
def list_documents():
    return get_all_documents()

@app.get("/list-test-pdfs", response_model=list[TestPDFInfo])
def list_test_pdfs():
    return get_all_test_pdfs()

@app.get("/download-test-pdf/{file_id}")
def download_test_pdf(file_id: int):
    pdf_content = get_test_pdf_content(file_id)
    if not pdf_content:
        raise HTTPException(status_code=404, detail="Test PDF not found.")
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=test_{file_id}.pdf"}
    )

@app.post("/delete-doc")
def delete_document(request: DeleteFileRequest):
    chroma_delete_success = delete_doc_from_chroma(request.file_id)

    if chroma_delete_success:
        db_delete_success = delete_document_record(request.file_id)
        if db_delete_success:
            return {"message": f"Successfully deleted document with file_id {request.file_id} from the system."}
        else:
            return {"error": f"Deleted from Chroma but failed to delete document with file_id {request.file_id} from the database."}
    else:
        return {"error": f"Failed to delete document with file_id {request.file_id} from Chroma."}

@app.post("/delete-test-pdf")
def delete_test_pdf(request: DeleteFileRequest):
    db_delete_success = delete_test_pdf_record(request.file_id)
    if db_delete_success:
        return {"message": f"Successfully deleted test PDF with file_id {request.file_id}."}
    else:
        return {"error": f"Failed to delete test PDF with file_id {request.file_id} from the database."}


@app.post("/check-uniqueness")
def check_document_uniqueness_endpoint(file: UploadFile = File(...)):
    temp_file_path = f"temp_{file.filename}"
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Проверка уникальности имени файла в SQLite
        is_unique_filename, existing_filename = check_filename_uniqueness(file.filename)
        if not is_unique_filename:
            return {
                "is_unique": False,
                "source": "SQLite",
                "message": f"Document with filename {file.filename} already exists"
            }

        # Проверка в ChromaDB
        # is_unique_chroma, max_similarity_chroma, similar_doc_id = check_document_uniqueness(temp_file_path)
        # if not is_unique_chroma:
        #     return {
        #         "is_unique": False,
        #         "source": "ChromaDB",
        #         "max_similarity": max_similarity_chroma,
        #         "similar_doc_id": similar_doc_id
        #     }

        return {"is_unique": True, "message": "Document is unique"}
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@app.get("/get-document-text/{file_id}")
def get_document_text(file_id: int):
    try:
        # Получаем документ из ChromaDB
        docs = vectorstore.get(where={"file_id": file_id})
        if not docs or not docs.get('documents'):
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Собираем весь текст документа
        document_text = "\n\n".join(docs['documents'])
        return {"text": document_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    print("Starting OneClickTest API server...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0", 
        port=8000,
        reload=True,
        log_level="info"
    )
