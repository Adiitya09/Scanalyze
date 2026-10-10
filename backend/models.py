from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Boolean, Float, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False, default="student")  # teacher, student
    full_name = Column(String(100), nullable=True)
    roll_number = Column(String(20), unique=True, index=True, nullable=True)  # Only for students, unique across all users
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    exams_created = relationship("Exam", back_populates="teacher")
    results = relationship("Result", back_populates="student")

class Exam(Base):
    __tablename__ = "exams"
    
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(String(20), unique=True, index=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_questions = Column(Integer, nullable=False)
    number_of_choices = Column(Integer, nullable=False, default=4)  # Number of choices per question (A, B, C, D or A, B, C, D, E, etc.)
    answer_key = Column(JSON, nullable=False)  # {"1": "A", "2": "B", ...}
    max_marks = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    teacher = relationship("User", back_populates="exams_created")
    results = relationship("Result", back_populates="exam")

class Result(Base):
    __tablename__ = "results"
    
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    roll_number = Column(String(20), nullable=False)
    student_answers = Column(JSON, nullable=False)  # {"1": "A", "2": "B", ...}
    correct_answers = Column(Integer, nullable=False, default=0)
    wrong_answers = Column(Integer, nullable=False, default=0)
    unanswered = Column(Integer, nullable=False, default=0)
    score = Column(Float, nullable=False, default=0.0)
    percentage = Column(Float, nullable=False, default=0.0)
    omr_file_path = Column(String(500), nullable=True)
    processing_confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    exam = relationship("Exam", back_populates="results")
    student = relationship("User", back_populates="results")

class OMRProcessingLog(Base):
    __tablename__ = "omr_processing_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    result_id = Column(Integer, ForeignKey("results.id"), nullable=True)
    file_path = Column(String(500), nullable=False)
    processing_status = Column(String(20), nullable=False)  # success, failed, processing
    error_message = Column(Text, nullable=True)
    processing_time = Column(Float, nullable=True)  # in seconds
    detected_bubbles = Column(JSON, nullable=True)
    confidence_scores = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# PostgreSQL-specific indexes for better performance
# These will be ignored by SQLite and improve PostgreSQL performance

# Index for faster user lookups
Index('idx_user_username', User.username)
Index('idx_user_email', User.email)
Index('idx_user_roll_number', User.roll_number)
Index('idx_user_role', User.role)

# Index for faster exam lookups
Index('idx_exam_exam_id', Exam.exam_id)
Index('idx_exam_teacher_id', Exam.teacher_id)
Index('idx_exam_created_at', Exam.created_at)
Index('idx_exam_active', Exam.is_active)

# Index for faster result queries
Index('idx_result_exam_student', Result.exam_id, Result.student_id)
Index('idx_result_roll_number', Result.roll_number)
Index('idx_result_created_at', Result.created_at)
Index('idx_result_score', Result.score)

# Index for faster log queries
Index('idx_omr_log_result_id', OMRProcessingLog.result_id)
Index('idx_omr_log_status', OMRProcessingLog.processing_status)
Index('idx_omr_log_created_at', OMRProcessingLog.created_at)
