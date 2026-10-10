from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
import shutil
from datetime import datetime

from database import get_db, init_db
from models import User, Exam, Result, OMRProcessingLog
from schemas import (
    UserCreate, UserLogin, User as UserSchema, Token,
    ExamCreate, ExamUpdate, Exam as ExamSchema, ExamWithResults,
    ResultSummary, ExamStatistics, TeacherDashboard,
    StudentDashboard, StudentResultHistory
)
from auth import (
    authenticate_user, create_access_token, get_current_active_user,
    require_teacher, require_student, get_password_hash
)
from omr_processor import OMRProcessor, validate_omr_format
from config import settings

# Initialize FastAPI app
app = FastAPI(
    title="OMR Sheet Evaluator API",
    description="An intelligent OMR processing and evaluation system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OMR processor
omr_processor = OMRProcessor()

# Create upload directory
UPLOAD_DIR = settings.UPLOAD_DIR
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()
    print("Database initialized successfully!")

# Health check endpoints
@app.get("/", tags=["Health"])
async def root():
    return {"message": "OMR Sheet Evaluator API is running", "version": "1.0.0"}

@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy", "message": "OMR Sheet Evaluator API is running", "version": "1.0.0"}

# Authentication endpoints
@app.post("/api/auth/register", response_model=UserSchema, tags=["Authentication"])
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if username already exists
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    # Check if email already exists
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Check if roll number already exists (for students only)
    if user.role == "student" and user.roll_number:
        if db.query(User).filter(User.roll_number == user.roll_number).first():
            raise HTTPException(
                status_code=400,
                detail="Roll number already registered"
            )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        roll_number=user.roll_number if user.role == "student" else None,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@app.post("/api/auth/login", response_model=Token, tags=["Authentication"])
async def login(user: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return access token."""
    authenticated_user = authenticate_user(db, user.username, user.password)
    if not authenticated_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": authenticated_user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me", response_model=UserSchema, tags=["Authentication"])
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user

# Exam management endpoints (Teacher only)
@app.post("/api/exams/create", response_model=ExamSchema, tags=["Exams"])
async def create_exam(
    exam: ExamCreate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """Create a new exam (Teacher only)."""
    try:
        print(f"Creating exam: {exam.exam_id} by teacher ID: {current_user.id}")
        
        # Check if exam ID already exists
        if db.query(Exam).filter(Exam.exam_id == exam.exam_id).first():
            raise HTTPException(status_code=400, detail="Exam ID already exists")
        
        print(f"Exam data: title={exam.title}, questions={exam.total_questions}, choices={exam.number_of_choices}")
        
        db_exam = Exam(
            exam_id=exam.exam_id,
            title=exam.title,
            description=exam.description,
            teacher_id=current_user.id,
            total_questions=exam.total_questions,
            number_of_choices=exam.number_of_choices,
            answer_key=exam.answer_key,
            max_marks=exam.max_marks
        )
        db.add(db_exam)
        db.commit()
        db.refresh(db_exam)
        
        print(f"Exam created successfully with ID: {db_exam.id}")
        return db_exam
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        print(f"Error creating exam: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating exam: {str(e)}")

@app.get("/api/exams", response_model=List[ExamSchema], tags=["Exams"])
async def get_exams(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get list of active exams."""
    try:
        print(f"Getting exams for user: {current_user.username} (role: {current_user.role})")
        
        query = db.query(Exam).filter(Exam.is_active == True)
        
        # If teacher, show only their exams
        if current_user.role == "teacher":
            query = query.filter(Exam.teacher_id == current_user.id)
        
        exams = query.offset(skip).limit(limit).all()
        print(f"Found {len(exams)} exams")
        return exams
        
    except Exception as e:
        print(f"Error getting exams: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error retrieving exams: {str(e)}")

@app.get("/api/exams/{exam_id}", response_model=ExamSchema, tags=["Exams"])
async def get_exam(
    exam_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get exam details by exam ID."""
    exam = db.query(Exam).filter(
        Exam.exam_id == exam_id,
        Exam.is_active == True
    ).first()
    
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    return exam

@app.put("/api/exams/{exam_id}", response_model=ExamSchema, tags=["Exams"])
async def update_exam(
    exam_id: str,
    exam_update: ExamUpdate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """Update exam (Teacher only)."""
    exam = db.query(Exam).filter(
        Exam.exam_id == exam_id,
        Exam.teacher_id == current_user.id
    ).first()
    
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Update fields
    for field, value in exam_update.dict(exclude_unset=True).items():
        setattr(exam, field, value)
    
    exam.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(exam)
    
    return exam

@app.delete("/api/exams/{exam_id}", tags=["Exams"])
async def delete_exam(
    exam_id: str,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """Delete exam (Teacher only)."""
    exam = db.query(Exam).filter(
        Exam.exam_id == exam_id,
        Exam.teacher_id == current_user.id
    ).first()
    
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Soft delete
    exam.is_active = False
    db.commit()
    
    return {"message": "Exam deleted successfully"}

# OMR Processing endpoints
@app.get("/api/omr/check-submission/{exam_id}", tags=["OMR Processing"])
async def check_existing_submission(
    exam_id: str,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Check if student has already submitted for this exam."""
    # Validate exam exists
    exam = db.query(Exam).filter(
        Exam.exam_id == exam_id,
        Exam.is_active == True
    ).first()
    
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Check for existing submission
    existing_result = db.query(Result).filter(
        Result.exam_id == exam.id,
        Result.student_id == current_user.id
    ).first()
    
    return {
        "has_submitted": existing_result is not None,
        "submission_details": {
            "score": existing_result.score,
            "percentage": existing_result.percentage,
            "submitted_at": existing_result.created_at.isoformat(),
            "result_id": existing_result.id
        } if existing_result else None
    }

@app.delete("/api/omr/submission/{exam_id}", tags=["OMR Processing"])
async def delete_submission(
    exam_id: str,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Delete student's submission for an exam."""
    # Validate exam exists
    exam = db.query(Exam).filter(
        Exam.exam_id == exam_id,
        Exam.is_active == True
    ).first()
    
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Find existing result
    existing_result = db.query(Result).filter(
        Result.exam_id == exam.id,
        Result.student_id == current_user.id
    ).first()
    
    if not existing_result:
        raise HTTPException(status_code=404, detail="No submission found for this exam")
    
    try:
        # Delete the OMR file if it exists
        if existing_result.omr_file_path and os.path.exists(existing_result.omr_file_path):
            os.remove(existing_result.omr_file_path)
        
        # Delete the result record
        db.delete(existing_result)
        
        # Also delete any processing logs for this result
        db.query(OMRProcessingLog).filter(OMRProcessingLog.result_id == existing_result.id).delete()
        
        db.commit()
        
        return {"message": "Submission deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting submission: {str(e)}"
        )

@app.post("/api/omr/upload", tags=["OMR Processing"])
async def upload_omr_sheet(
    exam_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Upload and process OMR sheet."""
    # Validate that the student has a roll number
    if not current_user.roll_number:
        raise HTTPException(
            status_code=400,
            detail="Student must have a roll number assigned to submit OMR sheets"
        )
    
    # Use the user's roll number
    roll_number = current_user.roll_number
    
    # Validate exam exists
    exam = db.query(Exam).filter(
        Exam.exam_id == exam_id,
        Exam.is_active == True
    ).first()
    
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Check if student has already submitted for this exam
    existing_result = db.query(Result).filter(
        Result.exam_id == exam.id,
        Result.student_id == current_user.id
    ).first()
    
    # Handle existing submissions
    allow_resubmission = settings.ALLOW_RESUBMISSION
    if existing_result and not allow_resubmission:
        raise HTTPException(
            status_code=400,
            detail="You have already submitted an OMR sheet for this exam"
        )
    
    # If resubmission is allowed and there's an existing result, we'll replace it
    replacing_submission = existing_result is not None
    
    # Validate file format
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    file_extension = os.path.splitext(file.filename)[1].lower()
    allowed_extensions = settings.ALLOWED_FILE_EXTENSIONS
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File format not supported. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Validate file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File exceeds maximum size limit of {settings.MAX_FILE_SIZE // (1024*1024)}MB")
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process OMR sheet
        processing_result = omr_processor.process_omr_sheet(file_path, exam.total_questions, exam.number_of_choices)
        
        if not processing_result["success"]:
            # Log processing failure
            log_entry = OMRProcessingLog(
                file_path=file_path,
                processing_status="failed",
                error_message=processing_result["message"],
                processing_time=processing_result["processing_time"]
            )
            db.add(log_entry)
            db.commit()
            
            raise HTTPException(
                status_code=400,
                detail=f"OMR processing failed: {processing_result['message']}"
            )
        
        # Calculate results
        student_answers = processing_result["answers"]
        correct_answers = 0
        wrong_answers = 0
        
        for q_num, student_ans in student_answers.items():
            correct_ans = exam.answer_key.get(q_num)
            if student_ans != "MULTIPLE" and correct_ans == student_ans:
                correct_answers += 1
            else:
                wrong_answers += 1
        
        unanswered = exam.total_questions - len(student_answers)
        marks_per_question = exam.max_marks / exam.total_questions if exam.total_questions > 0 else 1.0
        score = round(correct_answers * marks_per_question, 2)
        percentage = round((score / exam.max_marks) * 100, 2) if exam.max_marks > 0 else 0.0
        
        # Save result to database (replace existing if resubmission)
        if replacing_submission:
            # Update existing result
            result = existing_result
            # Remove old OMR file if it exists
            if result.omr_file_path and os.path.exists(result.omr_file_path):
                try:
                    os.remove(result.omr_file_path)
                except Exception as e:
                    print(f"Warning: Could not delete old OMR file {result.omr_file_path}: {e}")
            
            # Update all fields
            result.student_answers = student_answers
            result.correct_answers = correct_answers
            result.wrong_answers = wrong_answers
            result.unanswered = unanswered
            result.score = score
            result.percentage = percentage
            result.omr_file_path = file_path
            result.processing_confidence = processing_result["confidence"]
            result.created_at = datetime.utcnow()  # Update timestamp for resubmission
        else:
            # Create new result
            result = Result(
                exam_id=exam.id,
                student_id=current_user.id,
                roll_number=roll_number,
                student_answers=student_answers,
                correct_answers=correct_answers,
                wrong_answers=wrong_answers,
                unanswered=unanswered,
                score=score,
                percentage=percentage,
                omr_file_path=file_path,
                processing_confidence=processing_result["confidence"]
            )
            db.add(result)
        
        db.commit()
        db.refresh(result)
        
        # Log successful processing
        log_entry = OMRProcessingLog(
            result_id=result.id,
            file_path=file_path,
            processing_status="success",
            processing_time=processing_result["processing_time"],
            detected_bubbles={"count": processing_result["total_bubbles_detected"]},
            confidence_scores={"overall": processing_result["confidence"]}
        )
        db.add(log_entry)
        db.commit()
        
        # Prepare response message
        if replacing_submission:
            message = "OMR sheet resubmitted and processed successfully. Your previous submission has been replaced."
        else:
            message = "OMR sheet processed successfully"
        
        return {
            "message": message,
            "result_id": result.id,
            "score": score,
            "percentage": round(percentage, 2),
            "correct_answers": correct_answers,
            "wrong_answers": wrong_answers,
            "unanswered": unanswered,
            "confidence": processing_result["confidence"],
            "is_resubmission": replacing_submission
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions (like validation errors)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        raise
    except Exception as e:
        # Clean up file if processing fails
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        
        # Log the full error for debugging
        import traceback
        error_details = traceback.format_exc()
        print(f"OMR Upload Error: {error_details}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Error processing OMR sheet: {str(e)}"
        )

@app.post("/api/omr/debug", tags=["OMR Processing"])
async def debug_omr_sheet(
    exam_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(require_teacher),  # Only teachers can debug
    db: Session = Depends(get_db)
):
    """Debug OMR processing to help troubleshoot detection issues."""
    # Validate exam exists
    exam = db.query(Exam).filter(
        Exam.exam_id == exam_id,
        Exam.is_active == True
    ).first()
    
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Validate file format
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    file_extension = os.path.splitext(file.filename)[1].lower()
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.pdf']
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File format not supported. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Generate unique filename for debug
    unique_filename = f"debug_{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Run debug analysis
        debug_result = omr_processor.debug_omr_processing(
            file_path, exam.total_questions, exam.number_of_choices
        )
        
        # Clean up debug file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return {
            "exam_info": {
                "exam_id": exam.exam_id,
                "title": exam.title,
                "total_questions": exam.total_questions,
                "number_of_choices": exam.number_of_choices
            },
            "debug_analysis": debug_result
        }
        
    except Exception as e:
        # Clean up file if debug fails
        if os.path.exists(file_path):
            os.remove(file_path)
        
        raise HTTPException(
            status_code=500,
            detail=f"Error debugging OMR sheet: {str(e)}"
        )

@app.get("/api/results/{exam_id}/{roll_number}", response_model=ResultSummary, tags=["Results"])
async def get_result(
    exam_id: str,
    roll_number: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get result for specific exam and roll number."""
    # Get exam
    exam = db.query(Exam).filter(Exam.exam_id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Authorization check: students can only see their own results, teachers can see results for their exams
    if current_user.role == "student" and current_user.roll_number != roll_number:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Students can only view their own results"
        )
    if current_user.role == "teacher" and exam.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Teachers can only view results for their own exams"
        )
    
    # Get result
    result = db.query(Result).filter(
        Result.exam_id == exam.id,
        Result.roll_number == roll_number
    ).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    
    # Create answer breakdown
    answer_breakdown = []
    for q_num in range(1, exam.total_questions + 1):
        q_str = str(q_num)
        correct_answer = exam.answer_key.get(q_str, "")
        raw_student_ans = result.student_answers.get(q_str, "Not Answered")
        
        if raw_student_ans == "MULTIPLE":
            display_ans = "Multiple Marked"
            ans_status = "incorrect"
        elif raw_student_ans == "Not Answered":
            display_ans = "Not Answered"
            ans_status = "unanswered"
        elif raw_student_ans == correct_answer:
            display_ans = raw_student_ans
            ans_status = "correct"
        else:
            display_ans = raw_student_ans
            ans_status = "incorrect"
        
        answer_breakdown.append({
            "question": q_str,
            "correct_answer": correct_answer,
            "student_answer": display_ans,
            "status": ans_status
        })
    
    return ResultSummary(
        roll_number=result.roll_number,
        exam_title=exam.title,
        score=result.score,
        percentage=result.percentage,
        correct_answers=result.correct_answers,
        wrong_answers=result.wrong_answers,
        unanswered=result.unanswered,
        total_questions=exam.total_questions,
        max_marks=exam.max_marks,
        answer_breakdown=answer_breakdown
    )

# Teacher Dashboard endpoints
@app.get("/api/teacher/dashboard", response_model=TeacherDashboard, tags=["Teacher"])
async def get_teacher_dashboard(
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """Get teacher dashboard data."""
    try:
        print(f"Getting dashboard for teacher ID: {current_user.id}")
        
        # Get total exams created by teacher
        total_exams = db.query(Exam).filter(Exam.teacher_id == current_user.id).count()
        print(f"Total exams: {total_exams}")
        
        # Get total students (unique roll numbers in results for teacher's exams)
        total_students = db.query(Result.roll_number).join(Exam).filter(
            Exam.teacher_id == current_user.id
        ).distinct().count()
        print(f"Total students: {total_students}")
        
        # Get recent exams (last 5)
        recent_exams = db.query(Exam).filter(
            Exam.teacher_id == current_user.id
        ).order_by(Exam.created_at.desc()).limit(5).all()
        print(f"Recent exams count: {len(recent_exams)}")
        
        # Get recent results (last 5)
        recent_results = db.query(Result).join(Exam).filter(
            Exam.teacher_id == current_user.id
        ).order_by(Result.created_at.desc()).limit(5).all()
        print(f"Recent results count: {len(recent_results)}")
        
        return TeacherDashboard(
            total_exams=total_exams,
            total_students=total_students,
            recent_exams=recent_exams,
            recent_results=recent_results
        )
    except Exception as e:
        print(f"Error in teacher dashboard: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Dashboard error: {str(e)}")

@app.get("/api/exams/{exam_id}/statistics", response_model=ExamStatistics, tags=["Teacher"])
async def get_exam_statistics(
    exam_id: str,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """Get detailed statistics for an exam."""
    exam = db.query(Exam).filter(
        Exam.exam_id == exam_id,
        Exam.teacher_id == current_user.id
    ).first()
    
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Get all results for this exam
    results = db.query(Result).filter(Result.exam_id == exam.id).all()
    
    if not results:
        raise HTTPException(status_code=404, detail="No results found for this exam")
    
    # Calculate statistics
    scores = [result.score for result in results]
    total_students = len(results)
    average_score = sum(scores) / total_students
    highest_score = max(scores)
    lowest_score = min(scores)
    pass_rate = len([s for s in scores if s >= (exam.max_marks * 0.5)]) / total_students * 100
    
    # Question-wise accuracy
    question_wise_accuracy = {}
    for q_num in range(1, exam.total_questions + 1):
        q_str = str(q_num)
        correct_count = 0
        answered_count = 0
        
        for result in results:
            if q_str in result.student_answers:
                answered_count += 1
                if result.student_answers[q_str] == exam.answer_key.get(q_str):
                    correct_count += 1
        
        accuracy = (correct_count / answered_count * 100) if answered_count > 0 else 0
        question_wise_accuracy[q_str] = round(accuracy, 2)
    
    return ExamStatistics(
        exam_id=exam.exam_id,
        exam_title=exam.title,
        total_students=total_students,
        average_score=round(average_score, 2),
        highest_score=highest_score,
        lowest_score=lowest_score,
        pass_rate=round(pass_rate, 2),
        question_wise_accuracy=question_wise_accuracy
    )

@app.get("/api/exams/{exam_id}/export/csv", tags=["Exams"])
async def export_exam_results_csv(
    exam_id: str,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """Export exam results to CSV (Teacher only)."""
    import io
    import csv
    from fastapi.responses import StreamingResponse

    exam = db.query(Exam).filter(
        Exam.exam_id == exam_id,
        Exam.teacher_id == current_user.id
    ).first()
    
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
        
    results = db.query(Result).filter(Result.exam_id == exam.id).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Roll Number", "Student Name", "Correct Answers", 
        "Wrong Answers", "Unanswered", "Score", "Max Marks", 
        "Percentage", "Submission Date"
    ])
    
    for r in results:
        student = db.query(User).filter(User.id == r.student_id).first()
        student_name = student.full_name or student.username if student else "N/A"
        date_str = r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else "N/A"
        writer.writerow([
            r.roll_number,
            student_name,
            r.correct_answers,
            r.wrong_answers,
            r.unanswered,
            r.score,
            exam.max_marks,
            f"{r.percentage:.2f}%",
            date_str
        ])
        
    output.seek(0)
    filename = f"exam_{exam_id}_results.csv"
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# Student Dashboard endpoints
@app.get("/api/student/dashboard", response_model=StudentDashboard, tags=["Student"])
async def get_student_dashboard(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """Get student dashboard data with exam history and results."""
    try:
        print(f"Getting dashboard for student ID: {current_user.id}")
        
        # Get all results for this student with exam details
        results_query = db.query(Result, Exam).join(Exam).filter(
            Result.student_id == current_user.id
        ).order_by(Result.created_at.desc())
        
        result_exam_pairs = results_query.all()
        print(f"Found {len(result_exam_pairs)} results for student")
        
        if not result_exam_pairs:
            return StudentDashboard(
                total_exams_taken=0,
                average_percentage=0.0,
                highest_score=0.0,
                recent_results=[]
            )
        
        # Calculate statistics
        all_results = [result for result, exam in result_exam_pairs]
        total_exams_taken = len(all_results)
        
        percentages = [result.percentage for result in all_results]
        scores = [result.score for result in all_results]
        
        average_percentage = sum(percentages) / len(percentages)
        highest_score = max(scores)
        
        # Create result history (limit to last 10 results)
        recent_results = []
        for result, exam in result_exam_pairs[:10]:
            recent_results.append(StudentResultHistory(
                id=result.id,
                exam_id=exam.exam_id,
                exam_title=exam.title,
                roll_number=result.roll_number,
                score=result.score,
                percentage=result.percentage,
                correct_answers=result.correct_answers,
                wrong_answers=result.wrong_answers,
                unanswered=result.unanswered,
                total_questions=exam.total_questions,
                max_marks=exam.max_marks,
                created_at=result.created_at
            ))
        
        return StudentDashboard(
            total_exams_taken=total_exams_taken,
            average_percentage=round(average_percentage, 2),
            highest_score=highest_score,
            recent_results=recent_results
        )
        
    except Exception as e:
        print(f"Error in student dashboard: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Dashboard error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)