"""
校園重補修課程登記系統的資料模型模組。
此模組包含所有與資料庫相關的模型定義，用於 MongoDB 與 Beanie ODM。
"""

from .users import User, UserGroup
from .course import Course, CourseTimeSlot
from .enrollment import Enrollment
from .required_course import RequiredCourse

__all__ = [
    "User",
    "UserGroup",
    "Course",
    "CourseTimeSlot",
    "Enrollment",
    "RequiredCourse",
]
