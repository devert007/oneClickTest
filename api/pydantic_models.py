# pydantic_models.py
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional

class ModelName(str, Enum):
    VIKHR = "lakomoor/vikhr-llama-3.2-1b-instruct:1b"

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
    model: ModelName = Field(default=ModelName.VIKHR)  

class QueryResponse(BaseModel):
    answer: str
    session_id: str
    model: ModelName

class DocumentInfo(BaseModel):
    id: int
    filename: str
    client_id: int
    upload_timestamp: datetime

class TestPDFInfo(BaseModel):
    id: int
    filename: str
    document_id: Optional[int] = Field(default=None)
    document_name: Optional[str] = Field(default=None)
    session_id: Optional[str] = Field(default=None)
    client_id: Optional[int] = Field(default=None)
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
    model: ModelName = Field(default=ModelName.VIKHR)  