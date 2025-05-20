from datetime import datetime
from typing import Optional
from enum import Enum
from beanie import Document, Link
from pydantic import Field
from .enrollment import Enrollment, PaymentStatus as EnrollmentPaymentStatus # 引用 Enrollment 的 PaymentStatus
from ..utils.funcs import get_now

# TODO: 檢視此 PaymentRecordStatus 是否可以與 Enrollment 中的 PaymentStatus 合併或保持獨立。
#       若 Payment 記錄的是單筆繳費行為，而 Enrollment 的 payment_status 是該選課的整體繳費狀態，
#       則可能需要區分。目前暫定為獨立，但可再評估。
class PaymentRecordStatus(str, Enum):
    """繳費記錄狀態列舉"""
    PENDING = "待繳費"      # 繳費單已產生，等待繳費
    PAID = "已繳費"        # 已確認收到款項
    FAILED = "繳費失敗"    # 繳費嘗試失敗 (例如信用卡交易失敗)
    OVERDUE = "已逾期"      # 超過繳費期限未繳費
    CANCELLED = "已取消"    # 繳費單被取消 (例如選課取消導致)
    REFUND_PENDING = "待退款" # 等待退款處理
    REFUNDED = "已退款"      # 已完成退款

class Payment(Document):
    """
    代表學生繳費單的資料模型，記錄繳費狀態與金額，與選課記錄相關聯。
    """
    enrollment_id: Link[Enrollment]  # 關聯到選課記錄
    amount: int  # 繳費金額 (單位：元)
    status: PaymentRecordStatus = Field(default=PaymentRecordStatus.PENDING)  # 繳費記錄狀態
    created_at: datetime = Field(default_factory=get_now)  # 創建時間
    updated_at: Optional[datetime] = None  # 更新時間
    payment_due_date: Optional[datetime] = None  # 繳費截止日期
    payment_date: Optional[datetime] = None  # 實際繳費日期
    payment_method: Optional[str] = None  # 繳費方式，例如 "銀行轉帳", "現場繳費"
    receipt_number: Optional[str] = None  # 收據編號

    class Settings:
        name = "payments"  # 明確指定集合名稱

    # TODO: 實現繳費金額計算邏輯
    # 應根據相關選課記錄的課程總費用計算繳費金額。
    # 例如：可透過 enrollment_id 獲取課程費用，若有多筆選課，可考慮彙整計算。

    # TODO: 實現繳費狀態更新邏輯
    # 應提供方法更新繳費狀態，例如從 "待繳費" 變更為 "已繳費"，並記錄繳費日期與方式。

    # TODO: 支援多科目彙整繳費單
    # 考慮如何處理學生報名多個科目的情況，確保一張繳費單能包含多筆選課記錄的總金額。
    # 可考慮新增一個欄位或關聯，記錄多筆選課記錄。
