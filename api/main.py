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
import json
import requests
from typing import Optional,Tuple
from fastapi.middleware.cors import CORSMiddleware
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
import tempfile
from utils import parse_and_validate_test_json
from fastapi import Request
from google_auth import router as google_auth_router


def markdown_to_pdf(markdown_text, filename="test.pdf"):
    """Конвертирует Markdown текст в PDF файл"""
    try:
        # Создаем PDF в памяти
        buffer = BytesIO()
        
        try:
            # Попробуем зарегистрировать Arial (нужен файл arial.ttf в директории)
            pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
            font_name = "Arial"
        except:
            # Используем стандартный шрифт
            font_name = "Helvetica"
        
        # Создаем canvas
        p = canvas.Canvas(buffer, pagesize=letter)
        p.setFont(font_name, 12)
        
        # Разбиваем текст на строки
        lines = markdown_text.split("\n")
        y = 750
        line_height = 20
        page_number = 1
        
        # Добавляем заголовок страницы
        p.drawString(50, 780, f"Тест: {filename}")
        p.drawString(500, 780, f"Страница {page_number}")
        p.line(50, 775, 550, 775)
        y -= 40  # Отступ после заголовка
        
        for line in lines:
            # Пропускаем пустые строки
            if not line.strip():
                y -= line_height
                continue
                
            # Обрабатываем длинные строки
            words = line.split()
            current_line = []
            line_width = 0
            
            for word in words:
                word_width = len(word) * 7  # Примерная ширина символа
                if line_width + word_width > 500:  # Ширина страницы
                    # Рисуем текущую строку
                    p.drawString(50, y, " ".join(current_line))
                    y -= line_height
                    current_line = [word]
                    line_width = word_width
                else:
                    current_line.append(word)
                    line_width += word_width + 7  # +7 за пробел
            
            # Рисуем последнюю строку
            if current_line:
                p.drawString(50, y, " ".join(current_line))
                y -= line_height
            
            # Проверка на конец страницы
            if y < 50:
                p.showPage()
                page_number += 1
                p.setFont(font_name, 12)
                # Заголовок новой страницы
                p.drawString(50, 780, f"Тест: {filename} (продолжение)")
                p.drawString(500, 780, f"Страница {page_number}")
                p.line(50, 775, 550, 775)
                y = 750 - 40  # Отступ после заголовка
        
        p.save()
        buffer.seek(0)
        print(f"✅ PDF создан: {filename}, размер: {len(buffer.getvalue())} байт")
        return buffer
        
    except Exception as e:
        print(f"❌ Error converting markdown to PDF: {e}")
        # Возвращаем простой PDF в случае ошибки
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        p.setFont("Helvetica", 12)
        p.drawString(100, 700, "Тест")
        p.drawString(100, 680, f"Ошибка при создании PDF: {str(e)[:50]}")
        p.save()
        buffer.seek(0)
        return buffer
   


# Добавляем путь к папке app в Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

logging.basicConfig(filename='app.log', level=logging.INFO)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(google_auth_router)

@app.get("/")
def read_root():
    return {"message": "OneClickTest API is running", "status": "OK"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "OneClickTest API"}

# XML-based endpoints removed — XML functionality deprecated and deleted

@app.get("/difficulty-levels")
def get_difficulty_levels():
    """Получить доступные уровни сложности"""
    return [{"value": level.value, "label": level.value} for level in DifficultyLevel]

@app.get("/question-types")
def get_question_types():
    """Получить доступные типы вопросов"""
    return [{"value": qtype.value, "label": qtype.value} for qtype in QuestionType]

# XML-based endpoints removed — XML functionality deprecated and deleted

# XML-based endpoints removed — XML functionality deprecated and deleted

# Новый эндпоинт для генерации тестов
@app.post("/generate-test")
def generate_test(request: TestGenerationRequest):
    try:
        session_id = request.session_id or str(uuid.uuid4())
        
        print(f"Generating test with params: {request.dict()}") 
        
        # XML support removed; generating AI-based questions only
      
         
        ai_questions_content = ""
        ai_questions_count = request.question_count
        
        
        document_text = get_document_text(request.document_id)

        print(document_text)
        if document_text and ai_questions_count > 0:
                answer_field = '"answer": "Правильный ответ"' if request.include_answers else ''
                prompt = f"""
                Сгенерируй тест на основе текста документа.
                ВАЖНО: Используй ТОЛЬКО информацию, которая есть в предоставленном тексте. НЕ галюцинируй!
                
                Текст документа:
                {document_text}
                
                ТРЕБОВАНИЯ:
                - Сгенерируй РОВНО {ai_questions_count} РАЗНЫХ вопросов
                - КАЖДЫЙ вопрос должен быть УНИКАЛЬНЫМ и охватывать РАЗНЫЕ части документа
                - ЗАПРЕЩЕНО создавать одинаковые или похожие вопросы
                - ЗАПРЕЩЕНО повторяться
                - Уровень сложности: {request.difficulty}
                - Формат вопросов: {request.question_type}
                - {"Включать ответы" if request.include_answers else "Не включать ответы"}
                
                ПРАВИЛА ЭКСТРАКЦИИ ИНФОРМАЦИИ:
                - Извлекай факты, данные, цифры, имена, события из текста
                - Если информации недостаточно для {ai_questions_count} разных вопросов, используй разные аспекты одной информации
                - Проверь что каждый ответ базируется только на тексте документа
                - НЕ добавляй внешние знания или предположения
                
                ПРАВИЛА ДЛЯ ВАРИАНТОВ ОТВЕТОВ:
                - Создавай правдоподобные неправильные ответы (которые похожи на правильные)
                - Убедись что правильный ответ явно указан в документе
                - Минимум 3 варианта ответа на вопрос
                
                ФОРМАТ JSON (строго соблюдать):
                {{
                  "questions": [
                    {{
                      "question": "Первый уникальный вопрос из документа",
                      "choices": ["Вариант А из документа", "Вариант Б похожий но неправильный", "Вариант В похожий но неправильный"],
                      "answer": "Вариант А из документа"
                    }},
                    {{
                      "question": "Второй СОВЕРШЕННО ДРУГОЙ вопрос про другую часть",
                      "choices": ["Ответ 1", "Ответ 2", "Ответ 3"],
                      "answer": "Ответ 1"
                    }}
                  ]
                }}
                
                ПРИМЕРЫ РАЗНЫХ вопросов (они разные!):
                1. Факты: "Когда произошло событие?"
                2. Определения: "Что такое понятие X?"
                3. Причины: "Почему произошло Y?"
                4. Характеристики: "Какие свойства имеет объект Z?"
                5. Последовательность: "Какой порядок действий?"
                
                ФИНАЛЬНАЯ ПРОВЕРКА:
                - Все данные из документа ✓
                - Все вопросы разные ✓
                - JSON корректный и парсируемый ✓
                - Без комментариев, только JSON ✓
                - БЕЗ markdown кода (без ```, без ```json, без ```python) ✓
                - Ровно {ai_questions_count} вопросов ✓
                
                ВАЖНО: Возвращай ТОЛЬКО чистый JSON, начинающийся с {{ и заканчивающийся }}
                БЕЗ каких-либо комментариев, объяснений, markdown блоков или дополнительного текста!
                """
                print(prompt)
                chat_history = get_chat_history(session_id)
                rag_chain = get_rag_chain(request.model.value)
    
                ai_response = rag_chain.invoke({
                        "input": prompt,
                        "chat_history": chat_history
                })
                ai_questions_content = ai_response['answer']
                
                # Валидация и парсинг JSON ответа
                try:
                    test_data = parse_and_validate_test_json(
                        ai_questions_content,
                        ai_questions_count,
                        request.include_answers
                    )
                    # Преобразуем обратно в JSON для сохранения
                    ai_questions_content = json.dumps(test_data, ensure_ascii=False, indent=2)
                    
                except ValueError as e:
                    logging.error(f"Error validating test JSON: {e}")
                    raise HTTPException(status_code=500, detail=f"Ошибка валидации теста: {str(e)}")
                
       # Объединяем содержимое
        print(f"AI Questions Content: {ai_questions_content}")
        combined_content = ai_questions_content

        # Логируем генерацию теста
        insert_application_logs(
            session_id, 
            f"Generate test: {request.question_count} questions", 
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
                "ai_question_count": ai_questions_count
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
async def upload_test_pdf(
    file: UploadFile = File(...),
    document_id: Optional[int] = Form(None),
    session_id: Optional[str] = Form(None)
):
    """Загружает тестовый PDF или конвертирует Markdown в PDF"""
    try:
        # Читаем содержимое файла
        file_content = await file.read()
        
        # Определяем тип файла по расширению
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        print(f"📥 Загрузка тестового файла: {file.filename}, расширение: {file_extension}")
        
        pdf_content = None
        final_filename = file.filename
        
        if file_extension == '.md':
            # Декодируем Markdown текст
            markdown_text = file_content.decode('utf-8', errors='ignore')
            print(f"📝 Markdown текст (первые 500 символов): {markdown_text[:500]}...")
            
            # Конвертируем в PDF
            pdf_buffer = markdown_to_pdf(markdown_text, file.filename)
            pdf_content = pdf_buffer.read()
            
            # Обновляем имя файла
            final_filename = file.filename.replace('.md', '.pdf')
            print(f"✅ Markdown конвертирован в PDF: {final_filename}")
            
        elif file_extension == '.pdf':
            # Уже PDF файл
            pdf_content = file_content
            print(f"✅ Получен готовый PDF: {file.filename}")
            
        else:
            raise HTTPException(
                status_code=400, 
                detail="Поддерживаются только PDF и Markdown (.md) файлы"
            )
        
        if not pdf_content or len(pdf_content) == 0:
            raise HTTPException(
                status_code=400, 
                detail="Пустой PDF контент после конвертации"
            )
        
        # Сохраняем в базу данных
        file_id = insert_test_pdf_record(
            filename=final_filename,
            document_id=document_id,
            session_id=session_id or "default_session",
            pdf_content=pdf_content
        )
        
        print(f"🎉 Test PDF сохранен в БД: ID={file_id}, filename={final_filename}")
        
        return {
            "message": f"Test PDF {final_filename} has been successfully uploaded.",
            "file_id": file_id,
            "filename": final_filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"❌ Error uploading test PDF: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Ошибка при загрузке тестового PDF: {str(e)}"
        )

@app.post("/save-test")
async def save_test_endpoint(
    test_content: str = Form(...),
    filename: str = Form("test.md"),
    document_id: Optional[int] = Form(None),
    session_id: Optional[str] = Form(None)
):
    """Специальный эндпоинт для сохранения сгенерированных тестов"""
    try:
        print(f"💾 Сохранение теста: {filename}, длина контента: {len(test_content)} символов")
        
        # Конвертируем Markdown в PDF
        pdf_buffer = markdown_to_pdf(test_content, filename)
        pdf_content = pdf_buffer.read()
        
        # Обновляем имя файла
        pdf_filename = filename.replace('.md', '.pdf')
        
        if not pdf_content or len(pdf_content) == 0:
            raise HTTPException(
                status_code=400, 
                detail="Ошибка при создании PDF: пустой контент"
            )
        
        # Сохраняем в базу данных
        file_id = insert_test_pdf_record(
            filename=pdf_filename,
            document_id=document_id,
            session_id=session_id or f"session_{uuid.uuid4()}",
            pdf_content=pdf_content
        )
        
        print(f"✅ Тест сохранен: ID={file_id}, filename={pdf_filename}")
        
        return {
            "message": "Test saved successfully",
            "file_id": file_id,
            "filename": pdf_filename
        }
        
    except Exception as e:
        logging.error(f"❌ Error saving test: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Ошибка при сохранении теста: {str(e)}"
        )


# Прокси-эндпоинт для Google Apps Script — обходит CORS, выполняя запрос с сервера
@app.post("/proxy-google-form")
async def proxy_google_form(request: Request):
    """Принимает JSON от фронтенда и пересылает его на Google Apps Script с сервера.
    Тело запроса: { "test": <object с тестом> }
    Опционально можно задать переменную окружения GOOGLE_SCRIPT_URL или передать script_url в теле.
    """
    try:
        body = await request.json()
    except Exception as e:
        logging.error(f"proxy_google_form: invalid json body: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    test_payload = body.get("test") or body.get("testJson") or body
    script_url = body.get("script_url") or os.environ.get("GOOGLE_SCRIPT_URL")

    if not script_url:
        logging.error("proxy_google_form: GOOGLE_SCRIPT_URL not configured")
        raise HTTPException(status_code=500, detail="GOOGLE_SCRIPT_URL not configured on server")

    try:
        logging.info(f"Proxying request to Google Script: {script_url}")
        resp = requests.post(script_url, json=test_payload, timeout=15)
        resp.raise_for_status()
        try:
            data = resp.json()
        except Exception:
            data = resp.text
        return {"status": "ok", "script_response": data}
    except requests.exceptions.RequestException as e:
        logging.error(f"proxy_google_form: request to Google Script failed: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to call Google Script: {str(e)}")
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
