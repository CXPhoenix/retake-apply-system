"""資料庫連線與初始化模組。

此模組提供初始化 MongoDB 資料庫連線、註冊 Beanie ODM 文件模型
以及在應用程式結束時關閉資料庫連線的功能。
這些功能通常與應用程式的生命週期管理 (lifespan management) 結合使用。
"""
from beanie import init_beanie, Document
from ..configs import DbEnv

from motor.motor_asyncio import AsyncIOMotorClient
from reflex.utils import console

db_env = DbEnv()

class MongoDbClient:
    def __init__(self) -> None:
        console.info("建立與 MongoDB 資料庫的連線...")
        self._client = AsyncIOMotorClient(
            host=db_env.url,
            port=db_env.port,
            username=db_env.username,
            password=db_env.password,
            authSource=db_env.authSource,
        )
    
    async def init_database_connection(self, database_name: str, documents: list[Document]) -> 'MongoDbClient':
        await init_beanie(database=self._client[database_name], document_models=documents)
        console.info(f"已連線至 database {database_name}")
        return self
    
    def close_connection(self) -> None:
        console.info("正在關閉 MongoDB 連線...")
        self._client.close()
        console.info("MongoDB 連線已關閉。")
