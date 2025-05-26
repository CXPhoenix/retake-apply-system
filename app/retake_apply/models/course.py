from typing import Annotated

from beanie import Document, Indexed
from pydantic import Field

from ..utils.funcs import Utc8DateTime


class Course(Document):
    """（由管理者上傳）課程
    
    Attributes:
        campus_id (str): 課程 id；主鍵
        name (str): 課程名稱
        date_range (list[Utc8DateTime]): 上課時間（每一天都要列出）
        sessions (list[str]): 上課節次；紀錄使用 `D1~D4、DN、D5~D9`
        provided_credits (int): 課程重補修的學分數
    """
    campus_id: Annotated[str, Field(...), Indexed(unique=True)]
    name: str
    date_range: Annotated[list[Utc8DateTime], Field(...)]
    sessions: list[str]
    provided_credits: Annotated[int, Field(..., gt=0)]
    