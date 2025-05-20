from datetime import datetime
from typing import List, Optional, Annotated
from beanie import Document, Link, Indexed
from pydantic import Field, BaseModel
from ..utils.funcs import get_now

class CourseTimeSlot(BaseModel):
    """課程上課時間插槽的內嵌模型"""
    week_number: Optional[int] = None  # 週次，若適用
    day_of_week: int  # 星期幾，1=週一, ..., 7=週日
    period: str  # 節次，例如 "D1"-"D4" (早上), "DN" (中午), "D5"-"D9" (下午)
    start_time: str  # 格式 HH:MM
    end_time: str  # 格式 HH:MM
    location: Optional[str] = None  # 上課地點

class Course(Document):
    """
    代表重補修課程的資料模型，包含課程基本資訊和上課時間。
    """
    academic_year: Annotated[str, Indexed()]  # 學年度，例如 "113-1" 代表113學年度上學期
    course_code: Annotated[str, Indexed()]  # 科目代碼，同一學年度內應唯一
    course_name: str  # 科目名稱
    credits: float  # 學分數
    fee_per_credit: int  # 每學分費用，例如 240
    total_fee: int = Field(default=0)  # 總費用 = credits * fee_per_credit，由系統計算
    time_slots: List[CourseTimeSlot] = Field(default_factory=list)  # 上課時間列表
    instructor_name: Optional[str] = None  # 授課教師姓名
    max_students: Optional[int] = None  # 人數上限，初期可忽略
    is_open_for_registration: bool = True  # 是否開放選課
    created_at: datetime = Field(default_factory=get_now)  # 創建時間
    updated_at: Optional[datetime] = None  # 更新時間

    class Settings:
        name = "courses"  # 明確指定集合名稱
        indexes = [
            [("academic_year", 1), ("course_code", 1)],  # 複合索引，確保學年度內科目代碼唯一
        ]

    def calculate_total_fee(self) -> int:
        """計算課程總費用"""
        return int(self.credits * self.fee_per_credit)

    # TODO: 確保在 Course 物件儲存或更新 (特別是 credits 或 fee_per_credit 變動) 時，
    #       total_fee 欄位能被正確計算並更新。
    #       可以考慮使用 Beanie 的事件鉤子 (例如 @before_event(Insert, Replace, SaveChanges))
    #       來自動呼叫 self.total_fee = self.calculate_total_fee()。
    #       參考規格文件：`total_fee: Computed[int]`，暗示其值應基於其他欄位計算。
