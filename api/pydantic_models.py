# pydantic_models.py
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional

class ModelName(str, Enum):
    # Новые легкие модели
    SMOL_LM_3B = "smol-lm-3b"
    SMOL_LM_1_7B = "smol-lm-1.7b"
    
    # Существующие модели
    DEEPSEEK_R1 = "deepseek-r1"
    LLAMA_3_70B = "llama-3-70b"
    MIXTRAL_8X7B = "mixtral-8x7b"
    ZEPHYR_7B = "zephyr-7b"
    
    # Русскоязычные модели
    RUSSIAN_SAIGA = "russian-saiga"
    RUSSIAN_GPT = "russian-gpt"
    
    # Базовые модели
    GPT2 = "gpt2"
    MISTRAL_7B = "mistral-7b"

class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    OPEN_ENDED = "open_ended"

class DifficultyLevel(str, Enum):
    ELEMENTARY = "elementary"
    MIDDLE = "middle" 
    HIGH = "high"
    UNIVERSITY = "university"

class QueryInput(BaseModel):
    question: str
    session_id: Optional[str] = Field(default=None)
    model: ModelName = Field(default=ModelName.SMOL_LM_3B)

class QueryResponse(BaseModel):
    answer: str
    session_id: str
    model: ModelName

class DocumentInfo(BaseModel):
    id: int
    filename: str
    upload_timestamp: datetime

class TestPDFInfo(BaseModel):
    id: int
    filename: str
    document_id: Optional[int] = Field(default=None)
    session_id: Optional[str] = Field(default=None)
    upload_timestamp: datetime

class DeleteFileRequest(BaseModel):
    file_id: int

class TestGenerationRequest(BaseModel):
    document_id: int
    question_count: int
    difficulty: str
    question_type: str
    include_xml_tasks: bool = False
    xml_subject: Optional[str] = None
    xml_topic: Optional[str] = None
    xml_task_count: int = 0