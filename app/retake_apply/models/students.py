from beanie import Document
from typing import List, Optional
from pydantic import BaseModel

class RetakeSubjectInfo(BaseModel):
    subject_code: str
    subject_name: str
    original_grade: Optional[str] # Or float, depending on grade format
    # Add other relevant fields from the uploaded list

class Student(Document):
    student_id: str  # 學號
    id_number: str  # 身分證字號 (for login)
    name: str
    eligible_retake_subjects: List[RetakeSubjectInfo] = []

    class Settings:
        name = "students" # MongoDB collection name
        indexes = ["student_id", "id_number"]