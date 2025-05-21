from datetime import datetime
from typing import List, Optional, Annotated
from beanie import Document, Indexed # Link 不再直接使用於此模型
from pydantic import Field, BaseModel, field_validator, computed_field # Pydantic v2 imports
# from pydantic import validator # Pydantic v1 validator
from ..utils.funcs import get_utc_now # 替換了 get_now

# VALID_PERIODS 常數定義
VALID_PERIODS = [f"D{i}" for i in range(1, 10)] + ["DN"]

class CourseTimeSlot(BaseModel):
    """課程上課時間插槽的內嵌模型"""
    week_number: Optional[int] = None  # 週次，若適用
    day_of_week: int = Field(..., ge=1, le=7)  # 星期幾，1=週一, ..., 7=週日
    period: str  # 節次，例如 "D1", "DN", "D5"
    start_time: str  # 格式 HH:MM
    end_time: str  # 格式 HH:MM
    location: Optional[str] = None  # 上課地點

    @field_validator('period')
    @classmethod
    def validate_period(cls, value: str) -> str:
        """驗證節次代號是否有效。"""
        if value not in VALID_PERIODS:
            raise ValueError(f"無效的節次代號: {value}。有效代號為: {VALID_PERIODS}")
        return value

    @field_validator('start_time', 'end_time')
    @classmethod
    def validate_time_format(cls, value: str) -> str:
        """驗證時間格式是否為 HH:MM。"""
        try:
            datetime.strptime(value, "%H:%M")
        except ValueError:
            raise ValueError(f"時間格式應為 HH:MM，但收到: {value}")
        return value
    
    def overlaps_with(self, other_slot: "CourseTimeSlot") -> bool:
        """
        檢查此時間插槽是否與另一個時間插槽重疊。
        衝堂判斷:
        1. 如果星期 (`day_of_week`) 不同，則不衝突。
        2. 如果都有週次 (`week_number`) 且不同，則不衝突。
        3. 如果節次代號 (`period`) 相同，則視為衝突。
        4. 即使節次代號不同，如果實際開始/結束時間 (`start_time`, `end_time`) 有重疊，也視為衝突。
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
            s1_m = int(self.start_time[:2]) * 60 + int(self.start_time[3:])
            e1_m = int(self.end_time[:2]) * 60 + int(self.end_time[3:])
            s2_m = int(other_slot.start_time[:2]) * 60 + int(other_slot.start_time[3:])
            e2_m = int(other_slot.end_time[:2]) * 60 + int(other_slot.end_time[3:])
        except ValueError:
            # 如果時間格式不正確 (理論上已被 validator 擋下)，保守起見視為不衝突或記錄錯誤
            return False 

        # 檢查時間區間是否重疊: max(start1, start2) < min(end1, end2)
        if max(s1_m, s2_m) < min(e1_m, e2_m):
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
        """計算課程總費用。"""
        if self.credits is not None and self.fee_per_credit is not None:
            return int(self.credits * self.fee_per_credit)
        return 0 # 或者拋出錯誤，如果 credits 或 fee_per_credit 不應為 None

    class Settings:
        name = "courses"  # 明確指定集合名稱
        indexes = [
            [("academic_year", 1), ("course_code", 1), {"unique": True}],  # 確保學年度內科目代碼唯一
        ]

    async def save(self, **kwargs):
        """覆寫 save 方法以自動更新 updated_at 欄位。"""
        self.updated_at = get_utc_now()
        await super().save(**kwargs)

    # 移除舊的 calculate_total_fee 方法和 TODO，因為 total_fee 已改為 computed_field
    # Beanie 的事件鉤子 (例如 @before_event) 也可以用來更新非 computed field，
    # 但對於這種純粹由其他欄位衍生的值，Pydantic 的 @computed_field 更簡潔。
    # from beanie import Insert, Replace, SaveChanges, before_event
    # @before_event(Insert, Replace, SaveChanges)
    # def update_total_fee_hook(self):
    #    if self.credits is not None and self.fee_per_credit is not None:
    #        self.total_fee = int(self.credits * self.fee_per_credit)
    #    else:
    #        self.total_fee = 0
