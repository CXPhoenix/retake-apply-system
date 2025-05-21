from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from beanie import Document, Indexed
from pydantic import Field
from ..utils.funcs import get_utc_now # 改用 get_utc_now

class LogLevel(str, Enum):
    """日誌級別列舉"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class SystemLog(Document):
    """
    代表系統運作日誌的資料模型，用於記錄應用程式的重要操作與錯誤資訊。
    """
    timestamp: datetime = Field(default_factory=get_utc_now)  # 日誌創建時間 (使用 timestamp 更通用)
    level: LogLevel = Field(default=LogLevel.INFO)  # 日誌級別
    message: str  # 日誌訊息內容
    source: Optional[str] = None  # 日誌來源，例如 'AuthState', 'CourseSelectionPage', 'API'
    user_email: Optional[str] = None  # 相關使用者的 Email，若有
    details: Optional[Dict[str, Any]] = None  # 結構化的詳細資訊，例如錯誤堆疊、請求參數等

    class Settings:
        name = "system_logs"  # 明確指定集合名稱
        indexes = [
            [("timestamp", -1)],  # 按創建時間降序索引，方便按時間排序查詢
            [("level", 1)],  # 按日誌級別索引，方便篩選
            [("user_email", 1)], # 按使用者 Email 索引
            [("source", 1)], # 按來源索引
        ]

    @classmethod
    async def log(
        cls,
        level: LogLevel,
        message: str,
        source: Optional[str] = None,
        user_email: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> "SystemLog":
        """
        創建並儲存一筆新的系統日誌。

        Args:
            level (LogLevel): 日誌的級別。
            message (str): 日誌的主要訊息。
            source (Optional[str]): 日誌的來源模組或功能。
            user_email (Optional[str]): 與此日誌相關的使用者 Email。
            details (Optional[Dict[str, Any]]): 其他結構化的詳細資訊。

        Returns:
            SystemLog: 已儲存的日誌物件。
        """
        log_entry = cls(
            timestamp=get_utc_now(), # 確保使用當前 UTC 時間
            level=level,
            message=message,
            source=source,
            user_email=user_email,
            details=details
        )
        await log_entry.insert()
        # 也可以考慮同時輸出到標準輸出或日誌檔案
        # print(f"LOG [{log_entry.timestamp}] [{log_entry.level.value}] {log_entry.source or ''} - {log_entry.message} - User: {log_entry.user_email or 'N/A'} - Details: {log_entry.details or '{}'}")
        return log_entry

    # 日誌查詢邏輯主要會在 AdminLogsState 中實現，
    # 使用 Beanie 的 find() 方法配合查詢條件 (時間範圍、級別、關鍵字等)。
    # 模型本身不需要額外的複雜查詢方法。
