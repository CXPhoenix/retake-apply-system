from datetime import datetime
from typing import Optional
from beanie import Document
from pydantic import Field
from ..utils.funcs import get_now

class AcademicYearSetting(Document):
    """
    代表系統當前運作的學年度設定，用於確保選課與開課操作基於正確的學年度。
    """
    academic_year: str  # 學年度，例如 "113-1" 代表113學年度上學期
    set_at: datetime = Field(default_factory=get_now)  # 設定時間
    updated_at: Optional[datetime] = None  # 更新時間
    set_by: Optional[str] = None  # 設定者，例如使用者的 Google sub 或 email

    class Settings:
        name = "academic_year_settings"  # 明確指定集合名稱

    # TODO: 實現獲取當前學年度的方法
    # 應提供一個靜態方法或類方法，獲取最新的學年度設定記錄。
    # 例如：@classmethod async def get_current(cls) -> Optional["AcademicYearSetting"]
    # 確保在多筆記錄存在時，返回最新的設定。

    # TODO: 確保系統中僅有一個有效的學年度設定
    # 可考慮在插入新記錄時，標記舊記錄為無效，或限制僅能有一筆記錄。
    # 或者透過索引與查詢邏輯，確保總是使用最新的設定。
