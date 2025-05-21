"""資料庫連線與初始化模組。

此模組提供初始化 MongoDB 資料庫連線、註冊 Beanie ODM 文件模型
以及在應用程式結束時關閉資料庫連線的功能。
這些功能通常與應用程式的生命週期管理 (lifespan management) 結合使用。
"""
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
    """初始化資料庫連線並註冊所有 Beanie 資料模型。

    此函式會根據 `DbEnv` 組態設定建立一個 `AsyncIOMotorClient` 實例，
    然後使用此客戶端初始化 Beanie，並註冊專案中定義的所有 Document 模型。

    Returns:
        AsyncIOMotorClient: 已建立並可用於 Beanie 初始化的 Motor 客戶端實例。
                           此實例應被傳遞給 `close_db` 以在應用程式關閉時釋放資源。
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
    """關閉指定的 MongoDB 資料庫連線並釋放資源。

    Args:
        client (AsyncIOMotorClient): 先前由 `init_db` 函式建立並回傳的
                                     `AsyncIOMotorClient` 實例。
    """
    console.info("正在關閉 MongoDB 連線...")
    client.close()
    console.info("MongoDB 連線已關閉。")
