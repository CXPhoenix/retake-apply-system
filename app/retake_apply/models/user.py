from typing import Annotated, Optional
from pydantic import Field, EmailStr
from beanie import Document, Indexed, before_event, Save

class User(Document):
    email: Annotated[EmailStr, Field(...), Indexed(unique=True)]
    name: str
    family_name: str
    given_name: str
    
    school_id: Annotated[Optional[str], Field(None), Indexed(unique=True)]
    
    @before_event(Save)
    def update_school_id(self) -> None:
        self.school_id = self.email.split('@')[0]
    
    class Settings:
        name = "users"