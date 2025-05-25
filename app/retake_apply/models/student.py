from typing import Annotated
from pydantic import Field
from beanie import Document, Indexed

class Student(Document):
    school_id: Annotated[str, Field(...), Indexed(unique=True)]
    name: str
    required_retake_courses: list
    