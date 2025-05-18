from beanie import Document, Link
from datetime import datetime, timezone, timedelta
from .students import Student
from .courses import Course
from enum import Enum

class Status(int, Enum):
    CANCELLED = 0
    PENDING_PAYMENT = 1
    PAID = 2

class Registration(Document):
    student: Link[Student]
    course: Link[Course]
    registration_date: datetime = datetime.now(timezone(timedelta(hours=8)))
    status: Status = Status.PENDING_PAYMENT # e.g., pending_payment, paid, cancelled
    payment_slip_generated: bool = False
    on_site_registration: bool = False # To differentiate between online and on-site [cite: 4]

    class Settings:
        name = "registrations"
        indexes = [("student", "course")] # Ensure a student can't register for the same course multiple times