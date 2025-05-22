"""通用輔助函式模組。

此模組包含專案中可能在多處使用到的日期時間處理、
業務邏輯判斷（例如衝堂檢查）等通用功能。
"""
from typing import Annotated
from pydantic import AfterValidator
from datetime import datetime, timedelta, timezone

UTC8 = timezone(timedelta(hours=8), name="Asia/Taipei")

# 定義轉換函數
def convert_to_utc8(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        # 如果 datetime 物件是 naive (無時區資訊)，
        # 假設它是 UTC (MongoDB 通常以 UTC 儲存)
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(UTC8)

# 創建一個 Annotated 類型，它會在 Pydantic 解析完 datetime 後應用轉換函數
Utc8DateTime = Annotated[datetime, AfterValidator(convert_to_utc8)]

def get_now(utc_offset: int = 8) -> datetime:
    """獲取帶有指定 UTC 時區偏移的當前日期時間。

    Args:
        utc_offset (int, optional): 相對於 UTC 的小時偏移量。預設為 8 (台北時間 UTC+8)。

    Returns:
        datetime: 一個代表當前日期時間的 timezone-aware `datetime` 物件。
    """
    return datetime.now(timezone(timedelta(hours=utc_offset)))

