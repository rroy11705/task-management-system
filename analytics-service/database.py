"""
Database configuration for the Analytics Service.
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient

# Get MongoDB URL from environment variable
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/analytics")

# Create MongoDB client
client = AsyncIOMotorClient(MONGODB_URL)
database = client.get_database()

async def get_database():
    """
    Get MongoDB database.
    """
    return database