"""
SCANALYZE — Comprehensive Test Suite
Tests:
- Auth & RBAC (Teacher, Student, Tokens, Access Control)
- Database Operations & Schema Integrity
- Exam Creation & Validation
- OMR Engine (Synthetic sheet generation, detection, multiple marking, unanswered)
- Result Scoring Mathematics (correct + wrong + unanswered == total)
- Security (Student result privacy RBAC, empty file rejection)
- Statistics and CSV Export Endpoint
"""
import os
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup test database using SQLite in-memory or separate file
TEST_DB_FILE = "./test_scanalyze.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_FILE}"
os.environ["SECRET_KEY"] = "test-secret-key-for-unit-testing-32bytes"

from database import Base, get_db, seed_demo_users
import models
from main import app
from omr_processor import OMRProcessor

# Create test engine
test_engine = create_engine(
    f"sqlite:///{TEST_DB_FILE}",
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def setup_module():
    """Setup test database tables and demo accounts."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    # Seed demo users
    db = TestingSessionLocal()
    from auth import get_password_hash
    teacher = models.User(
        username="teacher",
        email="teacher@scanalyze.com",
        full_name="Prof. Demo Teacher",
        role="teacher",
        roll_number=None,
        hashed_password=get_password_hash("password"),
        is_active=True
    )
    student = models.User(
        username="student",
        email="student@scanalyze.com",
        full_name="Alex Student",
        role="student",
        roll_number="STU001",
        hashed_password=get_password_hash("password"),
        is_active=True
    )
    student2 = models.User(
        username="student2",
        email="student2@scanalyze.com",
        full_name="Sam Student",
        role="student",
        roll_number="STU002",
        hashed_password=get_password_hash("password"),
        is_active=True
    )
    db.add_all([teacher, student, student2])
    db.commit()
    db.close()

def teardown_module():
    """Cleanup test database file."""
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except:
            pass

# ================= AUTHENTICATION & RBAC TESTS =================

def test_demo_login_teacher():
    """Verify demo teacher can log in and receives a valid JWT token."""
    res = client.post("/api/auth/login", json={"username": "teacher", "password": "password"})
    assert res.status_code == 200, res.text
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_demo_login_student():
    """Verify demo student can log in and receives a valid JWT token."""
    res = client.post("/api/auth/login", json={"username": "student", "password": "password"})
    assert res.status_code == 200, res.text
    data = res.json()
    assert "access_token" in data

def test_invalid_login():
    """Verify wrong password returns 401 Unauthorized."""
    res = client.post("/api/auth/login", json={"username": "teacher", "password": "wrongpassword"})
    assert res.status_code == 401

def test_user_me_profile():
    """Verify /api/auth/me returns current user info."""
    login_res = client.post("/api/auth/login", json={"username": "teacher", "password": "password"})
    token = login_res.json()["access_token"]
    
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    user = res.json()
    assert user["username"] == "teacher"
    assert user["role"] == "teacher"

# ================= EXAM MANAGEMENT TESTS =================

def test_teacher_creates_exam():
    """Teacher creates an exam with answer key."""
    login_res = client.post("/api/auth/login", json={"username": "teacher", "password": "password"})
    token = login_res.json()["access_token"]

    exam_payload = {
        "exam_id": "TEST101",
        "title": "Computer Vision & OMR Test",
        "description": "Midterm test on image processing",
        "total_questions": 5,
        "number_of_choices": 4,
        "answer_key": {"1": "A", "2": "B", "3": "C", "4": "D", "5": "A"},
        "max_marks": 25
    }
    res = client.post("/api/exams/create", json=exam_payload, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200, res.text
    exam = res.json()
    assert exam["exam_id"] == "TEST101"
    assert exam["max_marks"] == 25
    assert exam["total_questions"] == 5

def test_student_cannot_create_exam():
    """Student attempting to create exam must get 403 Forbidden."""
    login_res = client.post("/api/auth/login", json={"username": "student", "password": "password"})
    token = login_res.json()["access_token"]

    exam_payload = {
        "exam_id": "HACK101",
        "title": "Unauthorized Exam",
        "total_questions": 5,
        "number_of_choices": 4,
        "answer_key": {"1": "A"},
        "max_marks": 5
    }
    res = client.post("/api/exams/create", json=exam_payload, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403

def test_get_exams():
    """Both teachers and students can retrieve active exams."""
    login_res = client.post("/api/auth/login", json={"username": "student", "password": "password"})
    token = login_res.json()["access_token"]

    res = client.get("/api/exams", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    exams = res.json()
    assert len(exams) >= 1
    assert any(e["exam_id"] == "TEST101" for e in exams)

# ================= OMR ENGINE UNIT TESTS =================

def generate_synthetic_omr_image(answers_to_fill: dict, file_path: str, total_q: int = 5, choices: int = 4):
    """
    Generate a clean synthetic OMR sheet image with bubbles.
    answers_to_fill: dict mapping question index (1-based) to list of marked choices e.g. {1: ['A'], 3: ['A', 'B']}
    """
    img = np.ones((800, 600, 3), dtype=np.uint8) * 255  # white background
    
    start_y = 120
    row_height = 80
    start_x = 150
    col_width = 80
    radius = 18

    for q in range(1, total_q + 1):
        y = start_y + (q - 1) * row_height
        marked_choices = answers_to_fill.get(q, [])
        for c in range(choices):
            x = start_x + c * col_width
            choice_letter = chr(ord('A') + c)
            # Draw bubble outline
            cv2.circle(img, (x, y), radius, (0, 0, 0), 2)
            
            # If filled, fill circle solidly with black
            if choice_letter in marked_choices:
                cv2.circle(img, (x, y), radius - 3, (0, 0, 0), -1)

    cv2.imwrite(file_path, img)

def test_omr_processor_single_marks():
    """Test OMR engine with standard single-marked bubbles."""
    processor = OMRProcessor()
    test_img = "./test_omr_single.png"
    # Q1: A, Q2: B, Q3: C, Q4: D, Q5: unanswered
    generate_synthetic_omr_image({1: ['A'], 2: ['B'], 3: ['C'], 4: ['D']}, test_img, 5, 4)
    
    result = processor.process_omr_sheet(test_img, total_questions=5, number_of_choices=4)
    assert result["success"] is True
    answers = result["answers"]
    assert answers.get("1") == "A"
    assert answers.get("2") == "B"
    assert answers.get("3") == "C"
    assert answers.get("4") == "D"
    assert "5" not in answers  # Q5 unanswered
    assert isinstance(result["confidence"], float)
    assert isinstance(result["processing_time"], float)
    
    if os.path.exists(test_img):
        os.remove(test_img)

def test_omr_processor_multiple_marks():
    """Test that multiple marks on a single question are flagged as MULTIPLE."""
    processor = OMRProcessor()
    test_img = "./test_omr_multi.png"
    # Q1: A, Q2: marked BOTH A and B (double bubble)
    generate_synthetic_omr_image({1: ['A'], 2: ['A', 'B']}, test_img, 5, 4)
    
    result = processor.process_omr_sheet(test_img, total_questions=5, number_of_choices=4)
    assert result["success"] is True
    answers = result["answers"]
    assert answers.get("1") == "A"
    assert answers.get("2") == "MULTIPLE"  # Correctly detected multiple mark
    
    if os.path.exists(test_img):
        os.remove(test_img)

def test_omr_processor_invalid_format():
    """Test validation on non-existent or invalid format files."""
    processor = OMRProcessor()
    res = processor.process_omr_sheet("non_existent_file.xyz", 5, 4)
    assert res["success"] is False

# ================= END-TO-END WORKFLOW & SECURITY =================

def test_student_upload_and_evaluation():
    """Student uploads OMR sheet, gets scored consistently with marks_per_question."""
    login_res = client.post("/api/auth/login", json={"username": "student", "password": "password"})
    token = login_res.json()["access_token"]

    test_img = "./test_upload.png"
    # Key is 1:A, 2:B, 3:C, 4:D, 5:A
    # Student marks: Q1: A (correct), Q2: B (correct), Q3: A (wrong), Q4: A & B (MULTIPLE/wrong), Q5: blank (unanswered)
    # Total questions = 5, Max marks = 25 (5 marks per question)
    # Correct: 2 (Q1, Q2) -> Score: 2 * 5 = 10.0 marks
    # Wrong: 2 (Q3 wrong answer, Q4 multiple marked)
    # Unanswered: 1 (Q5)
    # Percentage: 10/25 * 100 = 40.0%
    generate_synthetic_omr_image({1: ['A'], 2: ['B'], 3: ['A'], 4: ['A', 'B']}, test_img, 5, 4)

    with open(test_img, "rb") as f:
        res = client.post(
            "/api/omr/upload",
            data={"exam_id": "TEST101"},
            files={"file": ("omr.png", f, "image/png")},
            headers={"Authorization": f"Bearer {token}"}
        )

    if os.path.exists(test_img):
        os.remove(test_img)

    assert res.status_code == 200, res.text
    data = res.json()
    assert data["correct_answers"] == 2
    assert data["wrong_answers"] == 2
    assert data["unanswered"] == 1
    assert data["correct_answers"] + data["wrong_answers"] + data["unanswered"] == 5
    assert data["score"] == 10.0
    assert data["percentage"] == 40.0

def test_student_privacy_rbac():
    """A student must NOT be allowed to view another student's exam result."""
    login_student2 = client.post("/api/auth/login", json={"username": "student2", "password": "password"})
    token2 = login_student2.json()["access_token"]

    # Student 2 tries to view Student 1's (STU001) result
    res = client.get("/api/results/TEST101/STU001", headers={"Authorization": f"Bearer {token2}"})
    assert res.status_code == 403
    assert "Access denied" in res.json()["detail"]

def test_student_can_view_own_result():
    """A student can view their own result."""
    login_student1 = client.post("/api/auth/login", json={"username": "student", "password": "password"})
    token1 = login_student1.json()["access_token"]

    res = client.get("/api/results/TEST101/STU001", headers={"Authorization": f"Bearer {token1}"})
    assert res.status_code == 200
    data = res.json()
    assert data["roll_number"] == "STU001"
    assert data["score"] == 10.0
    assert data["max_marks"] == 25
    assert data["total_questions"] == 5
    
    # Check answer breakdown contains "Multiple Marked" for Q4
    q4 = next((item for item in data["answer_breakdown"] if item["question"] == "4"), None)
    assert q4 is not None
    assert q4["student_answer"] == "Multiple Marked"
    assert q4["status"] == "incorrect"

def test_teacher_can_view_student_result():
    """Teacher who created the exam can view student result."""
    login_teacher = client.post("/api/auth/login", json={"username": "teacher", "password": "password"})
    token = login_teacher.json()["access_token"]

    res = client.get("/api/results/TEST101/STU001", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["roll_number"] == "STU001"

def test_exam_statistics():
    """Teacher retrieves exam statistics."""
    login_teacher = client.post("/api/auth/login", json={"username": "teacher", "password": "password"})
    token = login_teacher.json()["access_token"]

    res = client.get("/api/exams/TEST101/statistics", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    stats = res.json()
    assert stats["total_students"] == 1
    assert stats["average_score"] == 10.0
    assert stats["highest_score"] == 10.0
    assert "question_wise_accuracy" in stats

def test_export_results_csv():
    """Teacher exports results to CSV."""
    login_teacher = client.post("/api/auth/login", json={"username": "teacher", "password": "password"})
    token = login_teacher.json()["access_token"]

    res = client.get("/api/exams/TEST101/export/csv", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    csv_text = res.text
    assert "Roll Number,Student Name,Correct Answers" in csv_text
    assert "STU001" in csv_text
    assert "10.0" in csv_text

def test_empty_file_upload_rejected():
    """Uploading an empty file must be rejected with 400."""
    login_student = client.post("/api/auth/login", json={"username": "student", "password": "password"})
    token = login_student.json()["access_token"]

    res = client.post(
        "/api/omr/upload",
        data={"exam_id": "TEST101"},
        files={"file": ("empty.png", b"", "image/png")},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()
