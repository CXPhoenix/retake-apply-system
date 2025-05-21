import base64
import os
from datetime import datetime
from typing import Annotated, Optional, List

from beanie import Document, Indexed
from pydantic import EmailStr, Field, computed_field
from ..utils.funcs import get_now, get_utc_now

from enum import Enum

class UserGroup(str, Enum):
    """使用者角色群組列舉"""
    STUDENT = "學生"
    COURSE_MANAGER = "課程管理者"
    SYSTEM_ADMIN = "系統管理者"
    AUTHENTICATED_USER = "已驗證使用者"

class User(Document):
    """
    代表系統中的任何使用者，透過 Google 進行身分驗證。
    角色由本地應用程式管理。
    """

    google_sub: Annotated[str, Indexed(unique=True)]  # 來自 Google ID Token 的 sub，唯一識別碼
    email: Annotated[EmailStr, Indexed(unique=True)]  # 來自 Google Auth 的電子郵件，主要索引鍵
    fullname: Optional[str] = None  # 來自 Google Auth 的全名
    picture: Optional[str] = None  # 來自 Google Auth 的頭像 URL
    student_id: Optional[str] = None  # 校內學號，若為學生則填入
    id_card_number_hash: Optional[str] = None  # 校內身分證號碼的雜湊值，用於學生身份核對
    groups: Annotated[List[UserGroup], Field(default_factory=lambda: [UserGroup.STUDENT, UserGroup.AUTHENTICATED_USER])]  # 本地應用程式角色群組
    created_at: datetime = Field(default_factory=get_utc_now)  # 帳號創建時間
    last_login: Optional[datetime] = None  # 最後登入時間
    is_active: bool = True  # 帳號是否啟用
    token_secret: Optional[str] = None  # 令牌密鑰

    @computed_field
    @property
    def student_campus_id(self) -> str:
        """計算並返回學生的校園 ID（從電子郵件中提取）"""
        return self.email.split("@")[0]

    def update_token_secret(self) -> None:
        """更新使用者的令牌密鑰"""
        self.token_secret = base64.b32encode(os.urandom(20)).decode()

    def update_login_datetime(self) -> None:
        """更新使用者的最後登入時間"""
        self.last_login = get_utc_now()

    def update_groups(self, new_groups: List[UserGroup]) -> None:
        """更新使用者的角色群組，合併新舊群組"""
        temp = set(self.groups) | set(new_groups)
        self.groups = list(temp)

    class Settings:
        name = "users"  # 明確指定集合名稱
