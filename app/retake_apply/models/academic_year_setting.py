from datetime import datetime # Python 標準庫的 datetime
from typing import Optional
from beanie import Document, Field # 從 beanie 匯入 Document 和 Field
from ..utils.funcs import get_utc_now # 替換了 get_now

# 為了範例獨立性，如果 get_now 未提供，可以直接使用 datetime.utcnow
# 例如： set_at: datetime = Field(default_factory=datetime.utcnow)

class AcademicYearSetting(Document):
    """
    代表系統當前運作的學年度設定，用於確保選課與開課操作基於正確的學年度。
    同時包含學生登記的起迄時間。
    """
    academic_year: str  # 學年度，例如 "113-1" 代表113學年度上學期
    registration_start_time: Optional[datetime] = None # 學生登記開始時間
    registration_end_time: Optional[datetime] = None   # 學生登記結束時間
    set_by_user_email: Optional[str] = None  # 設定者，使用者的 Google email
    set_at: datetime = Field(default_factory=get_utc_now)  # 設定時間
    updated_at: Optional[datetime] = None  # 最後更新時間 (可選)
    is_active: bool = Field(default=True) # 此設定是否為當前作用中

    class Settings:
        name = "academic_year_settings"  # 明確指定集合名稱
        indexes = [
            [("academic_year", 1), ("is_active", 1)], # 方便查詢特定學年是否活躍
            [("is_active", 1), ("set_at", -1)], # 方便查詢最新活躍設定
        ]

    @classmethod
    async def get_current(cls) -> Optional["AcademicYearSetting"]:
        """
        獲取當前有效的學年度設定。
        優先查找 is_active 為 True 且 set_at 最新的記錄。
        """
        current_setting = await cls.find_one(
            cls.is_active == True,
            sort=[("-set_at",)], # 確保取到最新的 active 設定
        )
        return current_setting

    @classmethod
    async def set_current(
        cls,
        academic_year: str,
        registration_start: Optional[datetime] = None,
        registration_end: Optional[datetime] = None,
        user_email: Optional[str] = None
    ) -> "AcademicYearSetting":
        """
        設定新的學年度為當前作用中的學年度。
        此操作會將先前所有 is_active 為 True 的設定更新為 False，
        然後插入一筆新的 is_active 為 True 的學年度設定。

        參數:
            academic_year (str): 新的學年度字串，例如 "113-1"。
            registration_start (Optional[datetime]): 學生登記開始時間。
            registration_end (Optional[datetime]): 學生登記結束時間。
            user_email (Optional[str]): 設定此學年度的使用者 Email。

        返回:
            AcademicYearSetting: 新建立並已設為作用中的學年度設定物件。
        """
        # 使用 Beanie 的 update 方法將所有現存的 is_active 設為 False
        # 注意：Beanie 的 update 方法通常作用於查詢結果的 Document 實例上，
        # 或者使用 update_many。這裡我們用 find 結合 update。
        # await cls.find(cls.is_active == True).update({"$set": {cls.is_active: False}})
        # 更安全的作法是遍歷更新，或確保 update_many 的語法正確
        # Beanie 的 update 適用於 Document 實例，若要更新多個文檔，應使用 collection.update_many
        # 或者，如果 Beanie 的 find().update() 支援直接更新多個文檔的特定欄位：
        await cls.get_motor_collection().update_many(
            filter={"is_active": True},
            update={"$set": {"is_active": False, "updated_at": get_utc_now()}}
        )
        
        new_setting = cls(
            academic_year=academic_year,
            registration_start_time=registration_start,
            registration_end_time=registration_end,
            set_by_user_email=user_email,
            set_at=get_utc_now(), # 確保使用 utcnow
            is_active=True
        )
        await new_setting.insert()
        return new_setting

    async def save(self, **kwargs):
        """覆寫 save 方法以自動更新 updated_at 欄位。"""
        self.updated_at = get_utc_now()
        await super().save(**kwargs)
