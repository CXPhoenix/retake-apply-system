from beanie import init_beanie
from ..configs import DbEnv
from ..models import (
    User, 
    Course, 
    Enrollment, 
    RequiredCourse,
    AcademicYearSetting, # 新增
    SystemLog,           # 新增
    Payment              # 新增
)
from motor.motor_asyncio import AsyncIOMotorClient
from reflex.utils import console

db_env = DbEnv()

async def init_db() -> AsyncIOMotorClient:
    """
    初始化資料庫連線並註冊所有 Beanie 資料模型。
    回傳 AsyncIOMotorClient 實例，以便在應用程式關閉時釋放資源。
    """
    console.info(f"正在連線至 MongoDB 資料庫: {db_env.db_name}")
    client = AsyncIOMotorClient(
        host=db_env.url,
        port=db_env.port,
        username=db_env.username,
        password=db_env.password,
        authSource=db_env.authSource,
    )
    await init_beanie(
        database=client[db_env.db_name],
        document_models=[
            User,
            Course,
            Enrollment,
            RequiredCourse,
            AcademicYearSetting,
            SystemLog,
            Payment,
        ]
    )
    console.info(f"已連線至 MongoDB 資料庫 {db_env.db_name} 並初始化 Beanie，已註冊模型。")
    return client

async def close_db(client: AsyncIOMotorClient) -> None:
    """關閉資料庫連線並釋放資源"""
    console.info("正在關閉 MongoDB 連線...")
    client.close()
    console.info("MongoDB 連線已關閉。")
