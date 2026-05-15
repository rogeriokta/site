from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models import CorrectionStatus


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    email: str


class UserOut(BaseModel):
    id: str
    username: str
    full_name: str
    email: str
    is_active: bool

    class Config:
        from_attributes = True


class CorrectionOut(BaseModel):
    id: str
    student_name: str
    student_id: str
    class_name: str
    discipline: str
    status: CorrectionStatus
    confidence: Optional[float] = None
    result_json: Optional[str] = None
    error_message: Optional[str] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CorrectionResult(BaseModel):
    id: str
    status: CorrectionStatus
    confidence: Optional[float] = None
    answers: Optional[dict] = None
    details: Optional[list] = None
    total_questions: Optional[int] = None
    correct_answers: Optional[int] = None
    score: Optional[float] = None
    processed_image_url: Optional[str] = None
    error_message: Optional[str] = None


class CorrectionList(BaseModel):
    items: list[CorrectionOut]
    total: int
    page: int
    page_size: int
