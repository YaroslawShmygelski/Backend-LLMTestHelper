import os

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase


class MongoDB:
    def __init__(self):
        self.mongodb_client: AsyncIOMotorClient | None = None
        self.database = None

    async def connect_mongodb(self):
        MONGO_URI = os.getenv("MONGO_URI")
        self.mongodb_client = AsyncIOMotorClient(MONGO_URI)
        self.database = self.mongodb_client[os.getenv("MONGO_DATABASE")]


    async def close_mongodb(self):
        if self.mongodb_client:
            self.mongodb_client.close()

mongodb_connection = MongoDB()
