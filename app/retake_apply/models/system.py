from datetime import timedelta
from typing import Annotated

from beanie import Document, Indexed
from pydantic import AfterValidator, Field
from pymongo import DESCENDING

from ..utils.data_enum import Groups
from ..utils.funcs import Utc8DateTime, get_now
from .utils import app_env

DEFAULT_APPLY_EXPIRED_RANGE = 7  # 7 days


def year_to_roc_year(year: int) -> int:
    if year <= 0:
        return app_env.default_year
    if year > 1911:
        return year - 1911
    return year


ROC_YEAR = Annotated[int, AfterValidator(year_to_roc_year)]


class SystemConfig(Document):
    retake_year: Annotated[
        ROC_YEAR,
        Field(app_env.default_year),
        Indexed(index_type=DESCENDING, unique=True),
    ]
    apply_start: Annotated[Utc8DateTime, Field(default_factory=get_now)]
    apply_end: Annotated[
        Utc8DateTime, Field(default_factory=lambda: get_now() + timedelta(days=14))
    ]
    updated_time: Annotated[Utc8DateTime, Field(default_factory=get_now)]

    class Setting:
        name = app_env.system_configs_store


class Manager(Document):
    school_id: Annotated[str, Field(...), Indexed(unique=True)]
    roles: Annotated[list[Groups], Field([Groups.MANAGER])]

    class Setting:
        name = app_env.managers_store
