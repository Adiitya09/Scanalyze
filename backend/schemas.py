from pydantic import BaseModel, EmailStr, validator
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    TEACHER = "teacher"
    STUDENT = "student"

# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.STUDENT
    roll_number: Optional[str] = None  # Required for students, optional for teachers

    @validator('roll_number')
    def validate_roll_number(cls, v, values):
        # If role is student, roll_number is required
        if values.get('role') == UserRole.STUDENT and not v:
            raise ValueError('Roll number is required for students')
        # If role is teacher, roll_number should be None
        if values.get('role') == UserRole.TEACHER and v:
            raise ValueError('Teachers should not have a roll number')
        return v

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserInDB(User):
    hashed_password: str

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Exam Schemas
class ExamBase(BaseModel):
    title: str
    description: Optional[str] = None
    total_questions: int
    number_of_choices: int = 4  # Number of choices per question (A, B, C, D = 4, A, B, C, D, E = 5, etc.)
    answer_key: Dict[str, str]  # {"1": "A", "2": "B", ...}
    max_marks: int

class ExamCreate(ExamBase):
    exam_id: str

class ExamUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    number_of_choices: Optional[int] = None
    answer_key: Optional[Dict[str, str]] = None
    max_marks: Optional[int] = None
    is_active: Optional[bool] = None

class Exam(ExamBase):
    id: int
    exam_id: str
    teacher_id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

class ExamWithResults(Exam):
    total_submissions: int
    average_score: float

# Result Schemas
class ResultBase(BaseModel):
    roll_number: str
    student_answers: Dict[str, str]

class ResultCreate(ResultBase):
    exam_id: str

class ResultExamInfo(BaseModel):
    id: int
    exam_id: str
    title: str
    max_marks: int
    total_questions: int

    class Config:
        from_attributes = True

class Result(ResultBase):
    id: int
    exam_id: int
    student_id: int
    correct_answers: int
    wrong_answers: int
    unanswered: int
    score: float
    percentage: float
    processing_confidence: Optional[float] = None
    created_at: datetime
    exam: Optional[ResultExamInfo] = None
    
    class Config:
        from_attributes = True

class ResultWithExam(Result):
    exam_title: str
    total_questions: int
    max_marks: int

class ResultSummary(BaseModel):
    roll_number: str
    exam_title: str
    score: float
    percentage: float
    correct_answers: int
    wrong_answers: int
    unanswered: int
    total_questions: int
    max_marks: int
    answer_breakdown: List[Dict[str, str]]  # Question-wise comparison

# OMR Processing Schemas
class OMRUpload(BaseModel):
    exam_id: str
    # roll_number is now taken from the authenticated user

class OMRProcessingStatus(BaseModel):
    status: str
    message: str
    confidence: Optional[float] = None
    processing_time: Optional[float] = None

# Statistics Schemas
class ExamStatistics(BaseModel):
    exam_id: str
    exam_title: str
    total_students: int
    average_score: float
    highest_score: float
    lowest_score: float
    pass_rate: float
    question_wise_accuracy: Dict[str, float]

class TeacherDashboard(BaseModel):
    total_exams: int
    total_students: int
    recent_exams: List[Exam]
    recent_results: List[Result]

class StudentResultHistory(BaseModel):
    id: int
    exam_id: str
    exam_title: str
    roll_number: str
    score: float
    percentage: float
    correct_answers: int
    wrong_answers: int
    unanswered: int
    total_questions: int
    max_marks: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class StudentDashboard(BaseModel):
    total_exams_taken: int
    average_percentage: float
    highest_score: float
    recent_results: List[StudentResultHistory]
