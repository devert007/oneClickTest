from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Response, Query
from pydantic_models import QueryInput, QueryResponse, DocumentInfo, DeleteFileRequest, TestPDFInfo, TestGenerationRequest
from pydantic_models import TestGenerationRequest, QuestionType, DifficultyLevel
from langchain_utils import get_rag_chain
from db_utils import (
    insert_application_logs, get_chat_history, get_all_documents, insert_document_record, 
    delete_document_record, insert_test_pdf_record, get_all_test_pdfs, delete_test_pdf_record,
    get_test_pdf_content,check_filename_uniqueness
)
from langchain_utils import  get_rag_chain
from chroma_utils import vectorstore,index_document_to_chroma, delete_doc_from_chroma,check_document_uniqueness, load_and_split_document
import os
import uuid
import logging
import shutil
from typing import Optional,Tuple

logging.basicConfig(filename='app.log', level=logging.INFO)

app = FastAPI()

@app.post("/generate-test")
def generate_test(request: TestGenerationRequest):
    """
    Генерирует тест по заданным параметрам (совместимость с generate_page.py)
    """
    try:
        # Получаем текст документа
        docs = vectorstore.get(where={"file_id": request.document_id})
        if not docs or not docs.get('documents'):
            raise HTTPException(status_code=404, detail="Document not found")
        
        document_text = "\n\n".join(docs['documents'])
        
        # Создаем промпт для генерации теста
        prompt = f"""
        Сгенерируй тест на основе предоставленного документа.
        Тип вопросов: {request.question_type}
        Уровень сложности: {request.difficulty}
        Количество вопросов: {request.question_count}
        """
        
        # Получаем RAG цепочку с нужными параметрами для генерации теста
        rag_chain = get_rag_chain(
            model="smol-lm-3b",
            question_type=request.question_type,
            difficulty=request.difficulty,
            question_count=request.question_count
        )
        
        # Генерируем тест
        result = rag_chain.invoke({
            "input": prompt,
            "chat_history": [],
            "context": document_text
        })
        
        test_content = result['answer']
        
        # Логируем генерацию
        insert_application_logs(
            session_id=str(uuid.uuid4()),
            user_query=f"Generate test: {request.question_type}, {request.difficulty}, {request.question_count} questions",
            gpt_response=test_content,
            model="smol-lm-3b"
        )
        
        return {"test_content": test_content, "document_id": request.document_id}
        
    except Exception as e:
        logging.error(f"Error generating test: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating test: {str(e)}")



@app.post("/upload-doc")
def upload_and_index_document(file: UploadFile = File(...)):
    allowed_extensions = ['.pdf', '.docx', '.html']
    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed types are: {', '.join(allowed_extensions)}")

    temp_file_path = f"temp_{file.filename}"

    try:
        print(f"📥 Начало загрузки файла: {file.filename}")
        
        # Сохраняем файл временно
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = os.path.getsize(temp_file_path)
        print(f"📊 Размер файла: {file_size} bytes")

        print(f"🔍 Проверка уникальности файла: {file.filename}")
        
        # Проверка уникальности имени файла в PostgreSQL
        is_unique_filename, existing_filename = check_filename_uniqueness(file.filename)
        print(f"✅ Результат проверки уникальности: {is_unique_filename}, существующий файл: {existing_filename}")
        
        if not is_unique_filename:
            logging.warning(f"Document {file.filename} already exists in PostgreSQL.")
            raise HTTPException(
                status_code=400,
                detail=f"Document with filename {file.filename} already exists in the database."
            )

        # Если документ уникален, продолжаем индексацию
        print(f"➕ Вставка записи в БД для файла: {file.filename}")
        file_id = insert_document_record(file.filename)
        print(f"✅ Document record inserted with ID: {file_id}")
        
        print(f"🔍 Индексация документа в ChromaDB...")
        success = index_document_to_chroma(temp_file_path, file_id)

        if success:
            logging.info(f"File {file.filename} successfully uploaded and indexed with file_id {file_id}")
            print(f"🎉 Файл успешно загружен и проиндексирован! ID: {file_id}")
            
            # Проверим, что документ действительно добавлен в ChromaDB
            docs = vectorstore.get(where={"file_id": file_id})
            print(f"📚 Проверка ChromaDB: найдено {len(docs['ids'])} чанков для file_id {file_id}")
            
            return {"message": f"File {file.filename} has been successfully uploaded and indexed.", "file_id": file_id}
        else:
            # Откатываем запись в БД если индексация не удалась
            print(f"❌ Ошибка индексации, откатываем запись в БД...")
            delete_document_record(file_id)
            logging.error(f"Failed to index document {file.filename}, rolled back DB record")
            raise HTTPException(status_code=500, detail=f"Failed to index {file.filename}.")
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error in upload_and_index_document: {str(e)}")
        print(f"💥 Критическая ошибка в upload_and_index_document: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.post("/chat", response_model=QueryResponse)
def chat(query_input: QueryInput):
    session_id = query_input.session_id or str(uuid.uuid4())
    logging.info(f"Session ID: {session_id}, User Query: {query_input.question}, Model: {query_input.model.value}")
    
    chat_history = get_chat_history(session_id)
    rag_chain = get_rag_chain()  # Используем одну модель без параметров
    
    try:
        answer = rag_chain.invoke({
            "input": query_input.question,
            "chat_history": chat_history
        })['answer']
    except Exception as e:
        logging.error(f"Ошибка при вызове RAG цепи: {e}")
        answer = "Извините, произошла ошибка при генерации ответа."

    insert_application_logs(session_id, query_input.question, answer, query_input.model.value)
    logging.info(f"Session ID: {session_id}, AI Response: {answer}")
    return QueryResponse(answer=answer, session_id=session_id, model=query_input.model)


@app.post("/upload-test-pdf")
@app.post("/upload-test-pdf")
async def upload_test_pdf(
    file: UploadFile = File(...),
    document_id: int = Form(0),
    session_id: str = Form("default_session"),
    client_id: int = Form(None)  # Измените на None по умолчанию
):
    try:
        pdf_content = await file.read()
        
        # Если client_id не предоставлен, используем клиента по умолчанию
        if client_id is None:
            from db_utils import get_default_client_id
            client_id = get_default_client_id()
        
        print(f"📝 Загрузка тестового PDF: {file.filename}, document_id: {document_id}, client_id: {client_id}")
        
        file_id = insert_test_pdf_record(file.filename, document_id, session_id, pdf_content, client_id)
        
        return {"file_id": file_id, "filename": file.filename}
    except Exception as e:
        print(f"❌ Ошибка загрузки тестового PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки тестового PDF: {str(e)}")
    

@app.get("/list-docs", response_model=list[DocumentInfo])
def list_documents(client_id: int = Query(None)):
    return get_all_documents(client_id)

@app.get("/list-test-pdfs", response_model=list[TestPDFInfo])
def list_test_pdfs(client_id: int = Query(None)):
    return get_all_test_pdfs(client_id)

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



