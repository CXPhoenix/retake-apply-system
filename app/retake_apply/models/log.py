from typing import Annotated

from beanie import Document
from pydantic import BaseModel, Field, computed_field

from ..utils.data_enum import Action
from ..utils.funcs import Utc8DateTime


class User(BaseModel):
    """使用者紀錄

    Attributes:
        school_id (str): 學號/教職員編號
        name (str): 姓名
    """

    school_id: str
    name: str


class SystemLog(Document):
    """系統日誌（系統級別操作時產生）

    Attributes:
        create_time (datetime): 操作時間
        user (User): 操作者
        action (str): 操作
    """

    year: int
    create_time: Annotated[Utc8DateTime, Field(...)]
    user: User
    action: Action
    event: str

    @computed_field
    @property
    def full_description(self) -> str:
        return (
            f"[{self.action}]{self.create_time.strftime('%Y-%m-%d %H:%M:%S')}"
            f"-- {self.user.name}({self.user.school_id}) did {self.action} {self.event}"
        )

    class Settings:
        name = "system_logs"


class AccessLog(Document):
    year: int
    access_time: Annotated[Utc8DateTime, Field(...)]
    user: User
    action: Action
    event: str

    @computed_field
    @property
    def full_description(self) -> str:
        return (
            f"[{self.action}]{self.access_time.strftime('%Y-%m-%d %H:%M:%S')}"
            f"-- {self.user.name}({self.user.school_id}) did {self.action} {self.event}"
        )

    class Settings:
        name = "access_logs"


class ExceptionLog(Document):
    year: int
    occured_time: Annotated[Utc8DateTime, Field(...)]
    user: User
    action: Action
    event: str
    exception_name: str
    exception_traceback: str

    @computed_field
    @property
    def full_description(self) -> str:
        return (
            f"[{self.action} - {self.exception_name}]{self.occured_time.strftime('%Y-%m-%d %H:%M:%S')}"
            f" -- {self.exception_traceback}"
            f" when {self.user.name}({self.user.school_id}) did {self.action} {self.event}"
        )

    class Settings:
        name = "exception_logs"
