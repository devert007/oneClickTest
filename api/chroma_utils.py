from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, UnstructuredHTMLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_chroma import Chroma
from typing import List, Tuple
from langchain_core.documents import Document
import numpy as np
import logging

from docling.document_converter import DocumentConverter

# Настройка логирования
logging.basicConfig(filename='app.log', level=logging.DEBUG)

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len)

embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

import os
if not os.path.exists("./chroma_db"):
    os.makedirs("./chroma_db")
vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embedding_function)


#devert007################
def load_and_split_document(file_path: str) -> List[Document]:
    """
    Универсальная функция загрузки документов с использованием Docling
    Поддерживает: PDF, DOCX, HTML, PPTX, XLSX и другие форматы
    """
    try:
        # Инициализация конвертера Docling
        converter = DocumentConverter()
        
        # Конвертация документа
        result = converter.convert(file_path)
        
        if not result.documents:
            logging.error(f"No content extracted from {file_path}")
            return []
        
        # Извлечение текста из всех документов
        all_texts = []
        for doc in result.documents:
            # Экспорт в Markdown для сохранения структуры
            markdown_content = doc.export_to_markdown()
            all_texts.append(markdown_content)
        
        # Объединение всего текста
        full_text = "\n\n".join(all_texts)
        
        # Создание Langchain Document
        documents = [Document(page_content=full_text, metadata={"source": file_path})]
        
        logging.debug(f"Loaded document from {file_path} using Docling")
        print(f"Loaded document from {file_path} using Docling")
        
        # Разбиение на чанки
        splits = text_splitter.split_documents(documents)
        logging.debug(f"Split document into {len(splits)} chunks")
        print(f"Split document into {len(splits)} chunks")
        
        return splits
        
    except Exception as e:
        logging.error(f"Error loading document {file_path} with Docling: {e}")
        print(f"Error loading document {file_path} with Docling: {e}")
        
        # Fallback на старые методы при ошибке
        return load_with_fallback(file_path)

def load_with_fallback(file_path: str) -> List[Document]:
    """Fallback метод для загрузки документов старыми способами"""
    try:
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.pdf':
            loader = PyPDFLoader(file_path)
        elif file_extension == '.docx':
            loader = Docx2txtLoader(file_path)
        elif file_extension == '.html':
            loader = UnstructuredHTMLLoader(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path}")

        documents = loader.load()
        logging.debug(f"Loaded {len(documents)} document(s) from {file_path} using fallback")
        splits = text_splitter.split_documents(documents)
        return splits
        
    except Exception as e:
        logging.error(f"Error in fallback loading for {file_path}: {e}")
        return []


def index_document_to_chroma(file_path: str, file_id: int) -> bool:
    try:
        splits = load_and_split_document(file_path)
        if not splits:
            logging.error(f"No splits generated for file_id {file_id}")
            print(f"No splits generated for file_id {file_id}")
            return False

        for split in splits:
            split.metadata['file_id'] = file_id

        vectorstore.add_documents(splits)
        logging.info(f"Successfully indexed document with file_id {file_id}")
        print(f"Successfully indexed document with file_id {file_id}")
        return True
    except Exception as e:
        logging.error(f"Error indexing document with file_id {file_id}: {e}")
        print(f"Error indexing document with file_id {file_id}: {e}")
        return False

def delete_doc_from_chroma(file_id: int):
    try:
        docs = vectorstore.get(where={"file_id": file_id})
        logging.debug(f"Found {len(docs['ids'])} document chunks for file_id {file_id}")
        print(f"Found {len(docs['ids'])} document chunks for file_id {file_id}")

        vectorstore._collection.delete(where={"file_id": file_id})
        logging.info(f"Deleted all documents with file_id {file_id}")
        print(f"Deleted all documents with file_id {file_id}")
        return True
    except Exception as e:
        logging.error(f"Error deleting document with file_id {file_id} from Chroma: {str(e)}")
        print(f"Error deleting document with file_id {file_id} from Chroma: {str(e)}")
        return False

def check_document_uniqueness(file_path: str, similarity_threshold: float = 0.8) -> Tuple[bool, float, str]:
    """
    Проверяет уникальность документа, сравнивая его с существующими в ChromaDB.
    Возвращает: (is_unique, max_similarity, similar_doc_id)
    """
    try:
        # Загружаем и разбиваем документ
        splits = load_and_split_document(file_path)
        if not splits:
            logging.error("No content extracted from document")
            print("No content extracted from document")
            return False, 0.0, "No content extracted from document"

        # Получаем эмбеддинги для всех чанков нового документа
        logging.debug(f"Generating embeddings for {len(splits)} document chunks")
        print(f"Generating embeddings for {len(splits)} document chunks")
        new_texts = [split.page_content for split in splits if split.page_content.strip()]
        if not new_texts:
            logging.error("No valid text content in document chunks")
            print("No valid text content in document chunks")
            return False, 0.0, "No valid text content in document chunks"

        new_embeddings = embedding_function.embed_documents(new_texts)
        logging.debug(f"Generated {len(new_embeddings)} embeddings with shape {np.array(new_embeddings).shape}")
        print(f"Generated {len(new_embeddings)} embeddings with shape {np.array(new_embeddings).shape}")

        # Проверяем размерность каждого эмбеддинга
        for i, emb in enumerate(new_embeddings):
            emb_array = np.array(emb, dtype=np.float32)
            if emb_array.shape != (384,):
                logging.error(f"Invalid embedding shape for chunk {i}: {emb_array.shape}")
                print(f"Invalid embedding shape for chunk {i}: {emb_array.shape}")
                return False, 0.0, f"Invalid embedding shape for chunk {i}"

        # Получаем все существующие документы из ChromaDB
        existing_docs = vectorstore.get(include=["embeddings", "metadatas"])
        logging.debug(f"Found {len(existing_docs['embeddings'])} existing embeddings in ChromaDB")
        print(f"Found {len(existing_docs['embeddings'])} existing embeddings in ChromaDB")
        if not existing_docs['embeddings']:
            logging.info("No existing documents in ChromaDB")
            print("No existing documents in ChromaDB")
            return True, 0.0, "No existing documents in ChromaDB"

        # Проверяем размерность существующих эмбеддингов
        valid_existing_embeddings = []
        valid_metadatas = []
        for i, emb in enumerate(existing_docs['embeddings']):
            emb_array = np.array(emb, dtype=np.float32)
            if emb_array.shape != (384,):
                logging.error(f"Invalid existing embedding shape at index {i}: {emb_array.shape}")
                print(f"Invalid existing embedding shape at index {i}: {emb_array.shape}")
                continue
            valid_existing_embeddings.append(emb_array)
            valid_metadatas.append(existing_docs['metadatas'][i])

        if not valid_existing_embeddings:
            logging.info("No valid existing embeddings in ChromaDB after filtering")
            print("No valid existing embeddings in ChromaDB after filtering")
            return True, 0.0, "No valid existing embeddings in ChromaDB"

        # Вычисляем максимальное косинусное сходство
        max_similarity = 0.0
        similar_doc_id = None
        for i, existing_embedding in enumerate(valid_existing_embeddings):
            for j, new_embedding in enumerate(new_embeddings):
                new_embedding = np.array(new_embedding, dtype=np.float32)
                # Косинусное сходство
                dot_product = float(np.dot(new_embedding, existing_embedding))  # Ensure scalar
                norm_new = float(np.linalg.norm(new_embedding))
                norm_existing = float(np.linalg.norm(existing_embedding))
                if norm_new == 0 or norm_existing == 0:
                    similarity = 0.0
                    logging.warning(f"Zero norm detected for chunk {j} or existing doc {i}")
                    print(f"Zero norm detected for chunk {j} or existing doc {i}")
                else:
                    similarity = dot_product / (norm_new * norm_existing)
                logging.debug(f"Similarity for chunk {j} with existing doc {i}: {similarity}")
                print(f"Similarity for chunk {j} with existing doc {i}: {similarity}")

                if not np.isscalar(similarity):
                    logging.error(f"Non-scalar similarity detected: {similarity}")
                    print(f"Non-scalar similarity detected: {similarity}")
                    return False, 0.0, f"Non-scalar similarity detected: {similarity}"

                if similarity > max_similarity:
                    max_similarity = float(similarity)
                    similar_doc_id = valid_metadatas[i].get('file_id', 'Unknown')
                    logging.debug(f"New max similarity: {max_similarity} with file_id {similar_doc_id}")
                    print(f"New max similarity: {max_similarity} with file_id {similar_doc_id}")

        # Документ считается уникальным, если максимальное сходство ниже порога
        is_unique = max_similarity < similarity_threshold
        logging.info(f"Document uniqueness check result: is_unique={is_unique}, max_similarity={max_similarity}, similar_doc_id={similar_doc_id}")
        print(f"Document uniqueness check result: is_unique={is_unique}, max_similarity={max_similarity}, similar_doc_id={similar_doc_id}")
        return bool(is_unique), float(max_similarity), str(similar_doc_id)

    except Exception as e:
        logging.error(f"Error checking document uniqueness: {e}")
        print(f"Error checking document uniqueness: {e}")
        return False, 0.0, f"Error: {str(e)}"
    