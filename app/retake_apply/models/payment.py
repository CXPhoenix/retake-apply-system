from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from enum import Enum
from beanie import Document, Link, before_event, Insert
from pydantic import Field
from pymongo import IndexModel # 匯入 IndexModel
# 備註：Enrollment 模型中的 PaymentStatus 列舉用於表示選課記錄本身的繳費狀態。
from ..utils.funcs import get_utc_now # 使用 UTC 時間以確保時區一致性

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
            IndexModel([("user_id", 1), ("status", 1)], name="user_id_1_status_1"), # 方便查詢某用戶特定狀態的繳費單
            IndexModel([("status", 1), ("payment_due_date", 1)], name="status_1_payment_due_date_1"), # 方便查詢待處理且快到期的繳費單
        ]

    async def calculate_amount_due_from_enrollments(self) -> int:
        """根據關聯的選課記錄計算應繳總金額。

        遍歷所有連結的 `Enrollment` 記錄，獲取其對應課程的 `total_fee` 並加總。

        Returns:
            int: 計算得出的應繳總金額。
        """
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
        """
        Beanie `Insert` 事件鉤子：在首次插入繳費記錄前執行。

        如果 `amount_due` (應繳金額) 未被明確設定（仍為初始值 0），
        則會嘗試根據關聯的選課記錄 (`enrollments`) 計算應繳總金額。
        此外，若只有一筆選課且該選課記錄為無需繳費，則將此繳費記錄也標註為無需繳費。
        """
        if self.amount_due == 0 and self.enrollments:
            self.amount_due = await self.calculate_amount_due_from_enrollments()
        
        # 特殊處理：若僅關聯一筆選課，且該選課本身標註為無需繳費
        if len(self.enrollments) == 1:
            enrollment_link = self.enrollments[0]
            enrollment = await enrollment_link.fetch() # type: ignore[attr-defined] # Beanie Link fetch
            
            # 局部匯入以避免循環依賴，並獲取 Enrollment 中的 PaymentStatus
            from .enrollment import PaymentStatus as EnrollmentPaymentStatus
            
            if enrollment and enrollment.payment_status == EnrollmentPaymentStatus.NOT_REQUIRED:
                self.status = PaymentRecordStatus.PAID # 將 PAID 視為無需繳費的最終狀態
                self.amount_due = 0
                self.amount_paid = 0 # 也應設定已付金額為0
                self.notes = "課程無需繳費，自動標記完成。"


    async def mark_as_paid(
        self,
        amount_paid: int,
        payment_method: str,
        transaction_id: Optional[str] = None,
        receipt_number: Optional[str] = None,
        payment_date: Optional[datetime] = None
    ):
        """將此繳費記錄標記為已付款，並同步更新相關選課記錄的繳費狀態。

        Args:
            amount_paid (int): 實際支付的金額。
            payment_method (str): 支付方式（例如："信用卡"、"銀行轉帳"）。
            transaction_id (Optional[str]): 支付平台或銀行的交易編號。
            receipt_number (Optional[str]): 校內產生的收據編號。
            payment_date (Optional[datetime]): 實際支付日期，若未提供則使用當前 UTC 時間。
        """
        self.amount_paid = amount_paid
        self.payment_method = payment_method
        self.payment_date = payment_date or get_utc_now()
        self.transaction_id = transaction_id
        self.receipt_number = receipt_number
        self.status = PaymentRecordStatus.PAID
        self.updated_at = get_utc_now()
        await self.save() # 儲存 Payment 自身的變更

        # 更新所有關聯 Enrollment 的 payment_status
        from .enrollment import PaymentStatus as EnrollmentPaymentStatus # 局部匯入
        for enrollment_link in self.enrollments:
            enrollment = await enrollment_link.fetch() # type: ignore[attr-defined] # Beanie Link fetch
            if enrollment:
                enrollment.payment_status = EnrollmentPaymentStatus.PAID
                # enrollment.payment_record = self # 若 Enrollment 有反向連結欄位，可在此設定
                await enrollment.save()

    async def save(self, **kwargs):
        """覆寫 `save` 方法以自動更新 `updated_at` 欄位。

        在每次儲存文件前，將 `updated_at` 更新為當前 UTC 時間。

        Args:
            **kwargs: 傳遞給父類 `save` 方法的其他關鍵字參數。
        """
        self.updated_at = get_utc_now()
        await super().save(**kwargs)
