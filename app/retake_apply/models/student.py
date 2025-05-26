from typing import Annotated

from beanie import Document, Indexed
from pydantic import BaseModel, Field, computed_field

from .utils import app_env


class RetakeCourse(BaseModel):
    """紀錄重補修課程

    Attributes:
        campus_id (str): 課程 id
        name (str): 課程名稱
        required_credits (int): 所需重補修的學分數
    """

    campus_id: str
    name: str
    required_credits: Annotated[int, Field(..., gt=0)]


class SelectedRetakeCourse(RetakeCourse):
    """紀錄選擇後的重補修課程

    Attributes:
        fee (int): 自動計算這門課程所需的費用
    """

    @computed_field
    @property
    def fee(self) -> int:
        """int: 課程所需費用（自動計算）"""
        return app_env.single_credit_fee * self.required_credits


class Student(Document):
    """（由管理員上傳）學生資料

    Attributes:
        school_id (str): 學號；主鍵
        name (str): 學生姓名
        required_retake_courses (list[RetakeCourse]): 學生需要重補修的課程
        selected_courses (list[SelectedRetakeCourse]): 學生選擇要重補修的課程
        total_fee (int): 總共要繳的重補修金額
    """

    school_id: Annotated[str, Field(...), Indexed(unique=True)]
    name: str
    required_retake_courses: list[RetakeCourse]
    selected_courses: list[SelectedRetakeCourse]
    total_fee: Annotated[int, Field(0, ge=0)]

    def update_total_fee(self) -> "Student":
        """更新 total_fee

        Returns:
            Student 物件（用於串接指令用）
        """
        self.total_fee = sum(map(lambda v: v.fee, self.selected_courses))
        return self

    class Settings:
        name = "students"
