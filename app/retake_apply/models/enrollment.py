from datetime import datetime
from typing import Optional
from enum import Enum
from beanie import Document, Link
from pydantic import Field
from .users import User
from .course import Course
from ..utils.funcs import get_now

class EnrollmentStatus(str, Enum):
    """選課狀態列舉"""
    SUCCESS = "成功"
    PENDING = "待處理"
    CANCELLED_BY_STUDENT = "已退選"
    CANCELLED_CONFLICT = "衝堂取消"
    # TODO: 根據實際需求，可能需要更多狀態，例如 "已額滿"、"資格不符" 等。

class PaymentStatus(str, Enum):
    """繳費狀態列舉"""
    PENDING = "待繳費"
    PAID = "已繳費"
    REFUNDED = "已退費"
    NOT_REQUIRED = "無需繳費" # 例如免費課程或特定身份學生
    # TODO: 根據實際需求，可能需要更多狀態。

class Enrollment(Document):
    """
    代表學生選課記錄的資料模型，記錄學生與課程之間的關聯。
    """
    user_id: Link[User]  # 關聯到學生
    course_id: Link[Course]  # 關聯到課程
    academic_year: str  # 選課當下學年度，冗餘欄位，方便查詢
    enrolled_at: datetime = Field(default_factory=get_now)  # 登記時間
    status: EnrollmentStatus = Field(default=EnrollmentStatus.SUCCESS)  # 選課狀態
    payment_status: Optional[PaymentStatus] = Field(default=PaymentStatus.PENDING)  # 繳費狀態

    class Settings:
        name = "enrollments"  # 明確指定集合名稱
        indexes = [
            [("user_id", 1), ("course_id", 1)],  # 複合唯一索引，確保學生不會重複選同一課程
        ]
