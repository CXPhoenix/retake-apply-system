from beanie import Document
from typing import List, Optional
from pydantic import BaseModel


class TimeSlot(BaseModel):
    week: int # 週次
    day_of_week: int # 星期 (e.g., 1 for Monday, etc.)
    period: str # 節次 (e.g., "A" for morning, "B" for afternoon) [cite: 1]

class Course(Document):
    course_code: str  # 科目代碼 [cite: 1]
    academic_year_semester: str  # 學年期 [cite: 1]
    course_name: str  # 科目名稱 [cite: 1]
    credits: int # 學分數 (to calculate amount)
    amount_per_credit: float = 240.0 # 金額 (一個學分240) [cite: 1]
    instructor: Optional[str]
    max_capacity: Optional[int]
    current_enrollment: int = 0
    schedule: List[TimeSlot] = [] # 上課時段 [cite: 1]
    # Teaching office sets this [cite: 1]

    class Settings:
        name = "courses"
        indexes = ["course_code", "academic_year_semester"]

    @property
    def total_amount(self) -> float:
        return self.credits * self.amount_per_credit