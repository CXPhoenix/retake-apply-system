from beanie import Document
from pydantic import computed_field, field_validator
import typing
from datetime import datetime


class SystemSettings(Document):
    registration_start_date: datetime
    registration_end_date: typing.Optional[datetime] = None

    @computed_field
    @property
    
    
    # Add other global settings if needed

    class Settings:
        name = "system_settings"

    