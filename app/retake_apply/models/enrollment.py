from datetime import datetime
from typing import Optional, TYPE_CHECKING
from enum import Enum
from beanie import Document, Link
from pydantic import Field
from .users import User
from .course import Course
from ..utils.funcs import get_utc_now # 改用 get_utc_now

if TYPE_CHECKING:
    from .payment import Payment # 處理循環匯入

class EnrollmentStatus(str, Enum):
    """選課狀態列舉"""
    SUCCESS = "成功"  # 選課成功
    PENDING_CONFIRMATION = "待確認" # 例如，需要管理員確認資格
    CANCELLED_BY_STUDENT = "學生自行退選"
    CANCELLED_CONFLICT = "衝堂取消"
    CANCELLED_ADMIN = "管理員取消" # 例如，資格不符或課程取消
    # TODO: 根據實際需求，可能需要更多狀態，例如 "已額滿" (COURSE_FULL), "資格不符" (NOT_QUALIFIED) 等。

class PaymentStatus(str, Enum):
    """繳費狀態列舉"""
    AWAITING_PAYMENT = "待繳費" # 等待學生繳費
    PAID = "已繳費" # 學生已完成繳費
    REFUNDED = "已退費" # 已退款給學生
    PARTIALLY_REFUNDED = "部分退費" # 部分退款
    NOT_REQUIRED = "無需繳費" # 例如免費課程或特定身份學生
    PAYMENT_FAILED = "繳費失敗" # 繳費嘗試失敗
    # TODO: 根據實際需求，可能需要更多狀態。

class Enrollment(Document):
    """
    代表學生選課記錄的資料模型，記錄學生與課程之間的關聯。
    """
    user_id: Link[User]  # 關聯到學生 (User Document)
    course_id: Link[Course]  # 關聯到課程 (Course Document)
    academic_year: str  # 選課當下學年度，冗餘欄位，方便查詢，例如 "113-1"
    
    enrolled_at: datetime = Field(default_factory=get_utc_now)  # 登記時間
    status: EnrollmentStatus = Field(default=EnrollmentStatus.SUCCESS)  # 選課狀態
    
    payment_status: PaymentStatus = Field(default=PaymentStatus.AWAITING_PAYMENT)  # 繳費狀態
    payment_record: Optional[Link["Payment"]] = None # 指向對應的繳費記錄 (Payment Document)

    updated_at: Optional[datetime] = None # 最後更新時間

    class Settings:
        name = "enrollments"  # 明確指定集合名稱
        indexes = [
            [("user_id", 1), ("course_id", 1), ("academic_year", 1), {"unique": True}],  # 確保同一學年學生不會重複選同一課程
            [("academic_year", 1), ("status", 1)], # 方便按學年和狀態查詢
            [("payment_status", 1)], # 方便查詢繳費狀態
        ]

    async def save(self, **kwargs):
        """覆寫 save 方法以自動更新 updated_at 欄位。"""
        self.updated_at = get_utc_now()
        await super().save(**kwargs)

    @property
    def is_active_enrollment(self) -> bool:
        """判斷此選課記錄是否為當前有效的 (非已取消或衝堂)"""
        return self.status not in [
            EnrollmentStatus.CANCELLED_BY_STUDENT,
            EnrollmentStatus.CANCELLED_CONFLICT,
            EnrollmentStatus.CANCELLED_ADMIN,
        ]
