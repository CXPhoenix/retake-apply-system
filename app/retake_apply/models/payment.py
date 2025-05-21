from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from enum import Enum
from beanie import Document, Link, before_event, Insert
from pydantic import Field
# from .enrollment import Enrollment, PaymentStatus as EnrollmentPaymentStatus # EnrollmentPaymentStatus is now in Enrollment
from ..utils.funcs import get_utc_now # 改用 get_utc_now

if TYPE_CHECKING:
    from .enrollment import Enrollment # 處理循環匯入
    from .users import User # 可能需要關聯 User

class PaymentRecordStatus(str, Enum):
    """繳費記錄狀態列舉"""
    PENDING = "待處理"      # 繳費單已產生，等待系統或人工處理 (例如產生繳費代碼)
    AWAITING_PAYMENT = "待繳費" # 已可繳費，等待使用者付款
    PAID = "已繳費"        # 已確認收到款項
    FAILED = "繳費失敗"    # 繳費嘗試失敗 (例如信用卡交易失敗)
    OVERDUE = "已逾期"      # 超過繳費期限未繳費
    CANCELLED = "已取消"    # 繳費單被取消 (例如選課取消導致)
    REFUND_PENDING = "待退款" # 等待退款處理
    REFUNDED = "已退款"      # 已完成退款

class Payment(Document):
    """
    代表學生繳費單的資料模型，記錄繳費狀態與金額，可與一或多筆選課記錄相關聯。
    """
    user_id: Link["User"] # 關聯到付款的學生 (方便查詢某學生的所有繳費單)
    enrollments: List[Link["Enrollment"]] = Field(default_factory=list)  # 關聯到一或多筆選課記錄
    
    amount_due: int = Field(default=0)  # 應繳總金額 (單位：元)，由系統計算
    amount_paid: Optional[int] = None # 實際繳納金額
    
    status: PaymentRecordStatus = Field(default=PaymentRecordStatus.PENDING)  # 繳費記錄狀態
    
    created_at: datetime = Field(default_factory=get_utc_now)  # 創建時間
    updated_at: Optional[datetime] = None  # 最後更新時間
    
    payment_due_date: Optional[datetime] = None  # 繳費截止日期
    payment_date: Optional[datetime] = None  # 實際繳費日期
    payment_method: Optional[str] = None  # 繳費方式，例如 "銀行轉帳", "現場繳費", "線上支付"
    transaction_id: Optional[str] = None # 支付平台或銀行的交易編號
    receipt_number: Optional[str] = None  # 校內收據編號
    
    notes: Optional[str] = None # 備註，例如退款原因或特殊處理說明

    class Settings:
        name = "payments"  # 明確指定集合名稱
        indexes = [
            [("user_id", 1), ("status", 1)], # 方便查詢某用戶特定狀態的繳費單
            [("status", 1), ("payment_due_date", 1)], # 方便查詢待處理且快到期的繳費單
        ]

    async def calculate_amount_due_from_enrollments(self) -> int:
        """根據關聯的選課記錄計算應繳總金額。"""
        total_due = 0
        if not self.enrollments:
            return 0
            
        for enrollment_link in self.enrollments:
            enrollment = await enrollment_link.fetch() # type: ignore
            if enrollment and enrollment.course_id: # type: ignore
                course = await enrollment.course_id.fetch() # type: ignore
                if course and hasattr(course, 'total_fee'):
                    total_due += course.total_fee
        return total_due

    @before_event(Insert)
    async def set_initial_amount_due(self):
        """在插入前，如果 amount_due 未設定，則根據選課計算。"""
        if self.amount_due == 0 and self.enrollments:
            self.amount_due = await self.calculate_amount_due_from_enrollments()
        
        # 如果 enrollments 只有一筆，且 payment_status 是 NOT_REQUIRED，則此 payment 也應是 NOT_REQUIRED
        if len(self.enrollments) == 1:
            enrollment = await self.enrollments[0].fetch() # type: ignore
            # Need to import PaymentStatus from enrollment
            from .enrollment import PaymentStatus as EnrollmentPaymentStatus
            if enrollment and enrollment.payment_status == EnrollmentPaymentStatus.NOT_REQUIRED: # type: ignore
                self.status = PaymentRecordStatus.PAID # 或新增一個 PAYMENT_NOT_REQUIRED 狀態
                self.amount_due = 0
                self.notes = "課程無需繳費"


    async def mark_as_paid(
        self,
        amount_paid: int,
        payment_method: str,
        transaction_id: Optional[str] = None,
        receipt_number: Optional[str] = None,
        payment_date: Optional[datetime] = None
    ):
        """將此繳費記錄標記為已付款，並更新相關選課記錄的狀態。"""
        self.amount_paid = amount_paid
        self.payment_method = payment_method
        self.payment_date = payment_date or get_utc_now()
        self.transaction_id = transaction_id
        self.receipt_number = receipt_number
        self.status = PaymentRecordStatus.PAID
        self.updated_at = get_utc_now()
        await self.save()

        # 更新相關 Enrollment 的 payment_status
        # Need to import PaymentStatus from enrollment
        from .enrollment import PaymentStatus as EnrollmentPaymentStatus
        for enrollment_link in self.enrollments:
            enrollment = await enrollment_link.fetch() # type: ignore
            if enrollment: # type: ignore
                enrollment.payment_status = EnrollmentPaymentStatus.PAID # type: ignore
                # enrollment.payment_record = self # 建立反向連結 (如果 Enrollment 模型有此欄位)
                await enrollment.save() # type: ignore

    async def save(self, **kwargs):
        """覆寫 save 方法以自動更新 updated_at 欄位。"""
        self.updated_at = get_utc_now()
        await super().save(**kwargs)
