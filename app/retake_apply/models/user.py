from typing import Annotated, Optional
from pydantic import Field, EmailStr
from beanie import Document, Indexed, before_event, Save, Update
from ..utils.data_enum import Groups
from .system import Manager

from reflex.utils import console

class User(Document):
    email: Annotated[str, Field(...), Indexed(unique=True)]
    name: str
    family_name: str
    given_name: str
    
    school_id: Annotated[Optional[str], Field(None), Indexed(unique=True)]
    roles: Annotated[list[Groups], Field([Groups.STUDENT])]
    
    @before_event(Save, Update)
    async def update_info(self) -> None:
        self.school_id = self.email.split('@')[0]
        console.info(Manager.school_id)
        manager_access = await Manager.find_one(Manager.school_id == self.school_id)
        if manager_access is not None:
            self.roles.extend(manager_access.roles)
    
    class Settings:
        name = "users"