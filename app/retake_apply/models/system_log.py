from datetime import datetime
from typing import Optional
from beanie import Document, Indexed
from pydantic import Field
from ..utils.funcs import get_now

class SystemLog(Document):
    """
    代表系統運作日誌的資料模型，用於記錄應用程式的重要操作與錯誤資訊。
    """
    level: str  # 日誌級別，例如 "INFO", "WARNING", "ERROR"
    message: str  # 日誌訊息內容
    source: Optional[str] = None  # 日誌來源，例如模組名稱或功能名稱
    user_id: Optional[str] = None  # 相關使用者的 Google sub 或 email，若有
    created_at: datetime = Field(default_factory=get_now)  # 日誌創建時間
    details: Optional[str] = None  # 詳細資訊，例如錯誤堆疊追蹤

    class Settings:
        name = "system_logs"  # 明確指定集合名稱
        indexes = [
            [("created_at", -1)],  # 按創建時間降序索引，方便按時間排序查詢
            [("level", 1)],  # 按日誌級別索引，方便篩選
        ]

    # TODO: 實現日誌記錄靜態方法
    # 應提供一個靜態方法或類方法，方便應用程式各處記錄日誌。
    # 例如：@classmethod async def log(cls, level: str, message: str, source: Optional[str] = None, user_id: Optional[str] = None, details: Optional[str] = None)
    # 確保記錄日誌的操作是非同步且高效的。

    # TODO: 實現日誌查詢方法
    # 應提供方法支援按時間範圍、級別、關鍵字等條件查詢日誌。
    # 例如：支援篩選與分頁查詢，方便系統管理者介面顯示。
