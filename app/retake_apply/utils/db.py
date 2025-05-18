from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
# Import your Beanie document models here later

async def init_db():
    client = AsyncIOMotorClient("mongodb://your_mongodb_connection_string")
    await init_beanie(database=client.your_database_name, document_models=[
        # Add your Beanie models here, e.g., Student, Course, Registration
    ])