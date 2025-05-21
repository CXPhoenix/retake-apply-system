"""
校園重補修課程登記系統的資料模型模組。
此模組包含所有與資料庫相關的模型定義，用於 MongoDB 與 Beanie ODM。
"""

from .users import User, UserGroup
from .course import Course, CourseTimeSlot
from .enrollment import Enrollment, PaymentStatus # 從 enrollment 匯入 PaymentStatus
from .required_course import RequiredCourse
from .academic_year_setting import AcademicYearSetting
from .system_log import SystemLog, LogLevel
from .payment import Payment, PaymentRecordStatus # 匯入 Payment 和 PaymentRecordStatus

__all__ = [
    "User",
    "UserGroup",
    "Course",
    "CourseTimeSlot",
    "Enrollment",
    "PaymentStatus", # 將 Enrollment 的 PaymentStatus 加入 __all__
    "RequiredCourse",
    "AcademicYearSetting",
    "SystemLog",
    "LogLevel",
    "Payment", # 將 Payment 加入 __all__
    "PaymentRecordStatus", # 將 PaymentRecordStatus 加入 __all__
]
