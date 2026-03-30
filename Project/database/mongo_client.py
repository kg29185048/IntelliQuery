# database/mongo_client.py

from pymongo import MongoClient
from app.config import MONGO_URI

def get_db():
    client = MongoClient(MONGO_URI)
    return client["test_db"]