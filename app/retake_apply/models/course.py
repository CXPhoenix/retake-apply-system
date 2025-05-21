from datetime import datetime
from typing import List, Optional, Annotated
from beanie import Document, Indexed # Link 不再直接使用於此模型
from pydantic import Field, BaseModel, field_validator, computed_field # Pydantic v2 匯入
from ..utils.funcs import get_utc_now # 使用 UTC 時間以確保時區一致性

# VALID_PERIODS 常數定義：定義了系統中所有有效的課程節次代號。
VALID_PERIODS = [f"D{i}" for i in range(1, 10)] + ["DN"]

class CourseTimeSlot(BaseModel):
    """課程上課時間插槽的內嵌 Pydantic 模型。"""
    week_number: Optional[int] = None  # 週次，若適用
    day_of_week: int = Field(..., ge=1, le=7)  # 星期幾，1=週一, ..., 7=週日
    period: str  # 節次，例如 "D1", "DN", "D5"
    start_time: str  # 格式 HH:MM
    end_time: str  # 格式 HH:MM
    location: Optional[str] = None  # 上課地點

    @field_validator('period')
    @classmethod
    def validate_period(cls, value: str) -> str:
        """驗證節次代號是否有效。

        Args:
            value (str): 待驗證的節次代號。

        Returns:
            str: 若有效則回傳原節次代號。

        Raises:
            ValueError: 若節次代號無效。
        """
        if value not in VALID_PERIODS:
            raise ValueError(f"無效的節次代號: {value}。有效代號為: {VALID_PERIODS}")
        return value

    @field_validator('start_time', 'end_time')
    @classmethod
    def validate_time_format(cls, value: str) -> str:
        """驗證時間格式是否為 HH:MM。

        Args:
            value (str): 待驗證的時間字串。

        Returns:
            str: 若格式正確則回傳原時間字串。

        Raises:
            ValueError: 若時間格式不正確。
        """
        try:
            datetime.strptime(value, "%H:%M")
        except ValueError:
            raise ValueError(f"時間格式應為 HH:MM，但收到: {value}")
        return value
    
    def overlaps_with(self, other_slot: "CourseTimeSlot") -> bool:
        """檢查此時間插槽是否與另一個時間插槽重疊。

        衝堂判斷邏輯：
        1.  如果星期 (`day_of_week`) 不同，則不衝突。
        2.  如果兩者都有定義週次 (`week_number`) 且週次不同，則不衝突。
            （若一方有週次另一方無，則不因此條件判斷為不衝突，需繼續比較時間）。
        3.  如果節次代號 (`period`) 相同（在同一天，且若適用則同一週的情況下），則視為衝突。
        4.  即使節次代號不同，如果實際開始/結束時間 (`start_time`, `end_time`) 有重疊，也視為衝突。

        Args:
            other_slot (CourseTimeSlot): 另一個用於比較的時間插槽物件。

        Returns:
            bool: 若兩個時間插槽有重疊（衝堂）則回傳 `True`，否則回傳 `False`。
        """
        if self.day_of_week != other_slot.day_of_week:
            return False
        
        # 僅當兩者都有 week_number 時才比較；若一方有另一方無，則不因此判斷不衝突
        if self.week_number is not None and \
           other_slot.week_number is not None and \
           self.week_number != other_slot.week_number:
            return False

        # 檢查節次代號是否相同
        if self.period == other_slot.period:
            return True # 同一天、同一週(如果適用)、同一節次，必衝突

        # 檢查實際時間是否有重疊
        try:
            # 將 HH:MM 時間轉換為當天的分鐘數以便比較
            s1_minutes = int(self.start_time[:2]) * 60 + int(self.start_time[3:])
            e1_minutes = int(self.end_time[:2]) * 60 + int(self.end_time[3:])
            s2_minutes = int(other_slot.start_time[:2]) * 60 + int(other_slot.start_time[3:])
            e2_minutes = int(other_slot.end_time[:2]) * 60 + int(other_slot.end_time[3:])
        except ValueError:
            # 理論上時間格式已由 Pydantic validator 驗證過。
            # 若此處仍發生錯誤，可能代表資料未經 Pydantic 模型初始化。
            # 為求穩健，將其視為不衝突，並建議記錄此異常。
            # logging.error(f"時間轉換錯誤於衝堂檢查: self={self}, other={other_slot}")
            return False 

        # 檢查時間區間是否重疊: max(start1, start2) < min(end1, end2)
        if max(s1_minutes, s2_minutes) < min(e1_minutes, e2_minutes):
            return True # 實際時間重疊

        return False

class Course(Document):
    """
    代表重補修課程的資料模型，包含課程基本資訊和上課時間。
    """
    academic_year: Annotated[str, Indexed()]  # 學年度，例如 "113-1" 代表113學年度上學期
    course_code: Annotated[str, Indexed()]  # 科目代碼，同一學年度內應唯一
    course_name: str  # 科目名稱
    credits: float  # 學分數
    fee_per_credit: int  # 每學分費用，例如 240
    # total_fee is now a computed field
    time_slots: List[CourseTimeSlot] = Field(default_factory=list)  # 上課時間列表
    instructor_name: Optional[str] = None  # 授課教師姓名
    max_students: Optional[int] = None  # 人數上限，初期可忽略
    is_open_for_registration: bool = Field(default=True)  # 是否開放選課
    created_at: datetime = Field(default_factory=get_utc_now)  # 創建時間
    updated_at: Optional[datetime] = None  # 最後更新時間

    @computed_field
    @property
    def total_fee(self) -> int:
        """計算並回傳課程總費用。

        總費用由 `credits` (學分數) 和 `fee_per_credit` (每學分費用) 計算得出。
        若任一必要欄位為 `None`，則回傳 0。

        Returns:
            int: 計算後的課程總費用。
        """
        if self.credits is not None and self.fee_per_credit is not None:
            return int(self.credits * self.fee_per_credit)
        return 0 # 或者，若 credits 和 fee_per_credit 應為必填，可考慮拋出錯誤

    class Settings:
        name = "courses"  # 明確指定 MongoDB collection 名稱
        indexes = [
            # 確保在同一學年度 (academic_year) 下，科目代碼 (course_code) 是唯一的。
            [("academic_year", 1), ("course_code", 1), {"unique": True}],
        ]

    async def save(self, **kwargs):
        """覆寫 `save` 方法以自動更新 `updated_at` 欄位。

        在每次儲存文件前，將 `updated_at` 更新為當前 UTC 時間。

        Args:
            **kwargs: 傳遞給父類 `save` 方法的其他關鍵字參數。
        """
        self.updated_at = get_utc_now()
        await super().save(**kwargs)

    # 備註：舊有的 calculate_total_fee 方法已被移除。
    # 目前 total_fee 欄位已改為使用 Pydantic 的 @computed_field 實現，
    # 這使得此衍生欄位的值能自動基於其他欄位計算，更為簡潔。
    # 若未來有需要在儲存前執行更複雜的欄位更新邏輯（非純粹衍生計算），
    # 可考慮使用 Beanie 的事件鉤子，例如 @before_event(Insert, Replace, SaveChanges)。
