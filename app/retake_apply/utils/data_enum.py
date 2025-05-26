from enum import Enum

class Groups(str, Enum):
    MANAGER = "行政"
    ADMIN = "系統管理員"

class Action(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"