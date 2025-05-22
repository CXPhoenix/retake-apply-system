from enum import Enum

class Groups(str, Enum):
    STUDENT = "學生"
    MANAGER = "行政"
    ADMIN = "系統管理員"