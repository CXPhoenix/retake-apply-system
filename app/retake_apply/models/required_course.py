from datetime import datetime
from typing import Optional
from beanie import Document, Link
from pydantic import Field
from .users import User
from ..utils.funcs import get_utc_now

class RequiredCourse(Document):
    """
    代表學生應重補修科目的資料模型，記錄學生需要重修的課程資訊。
    """
    user_id: Link[User]  # 關聯到學生
    academic_year_taken: str  # 原始修課學年度
    course_code: str  # 應重補修的科目代碼
    course_name: str  # 應重補修的科目名稱
    original_grade: str  # 原始不及格成績，例如 "45", "F"
    is_remedied: bool = False  # 是否已完成重補修
    uploaded_at: datetime = Field(default_factory=get_utc_now)  # 此記錄上傳時間

    class Settings:
        name = "required_courses"  # 明確指定集合名稱
