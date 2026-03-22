from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional
from typing import List, Optional

class ModelName(str, Enum):
    GROQ_GPT_OSS = "openai/gpt-oss-120b"
    VIKHR = "bambucha/saiga-llama3:8b"

class DifficultyLevel(str, Enum):
    EASY = "Для средних классов"
    HARD = "Для старших классов"

class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    OPEN_ENDED = "open_ended"

class QueryInput(BaseModel):
    question: str
    session_id: str = Field(default=None)
    model: ModelName = Field(default=ModelName.GROQ_GPT_OSS)

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
    document_id: Optional[int] = Field(default=None)
    question_count: int = Field(default=5, ge=1, le=20)
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.EASY)
    question_type: QuestionType = Field(default=QuestionType.MULTIPLE_CHOICE)
    include_answers: bool = Field(default=True)
    session_id: Optional[str] = Field(default=None)
    model: ModelName = Field(default=ModelName.GROQ_GPT_OSS)
    # XML fields removed — XML support deprecated

class TestGenerationResponse(BaseModel):
    test_content: str
    session_id: str
    parameters: dict

class TestQuestion(BaseModel):
    question: str
    choices: List[str]
    answer: Optional[str] = True  # если include_answers=True

class TestContent(BaseModel):
    questions: List[TestQuestion]


