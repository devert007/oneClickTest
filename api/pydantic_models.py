from pydantic import BaseModel, Field,EmailStr
from enum import Enum
from datetime import datetime
from typing import Optional

class ModelName(str, Enum):
    GPT4_O = "gpt-4o"
    GPT4_O_MINI = "gpt-4o-mini"
    LLAMA3_2 = "llama3.2"

class QueryInput(BaseModel):
    question: str
    session_id: str = Field(default=None)
    model: ModelName = Field(default=ModelName.LLAMA3_2)

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


class UserCreate(Basemodel):
    username: str = Field(..., min_length=2, max_length=50)
    email:EmailStr
    password:str = Field(...,min_length=6)

class UserLogin(BaseModel):
    username:str
    password:str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    username: Optional[str] = None


