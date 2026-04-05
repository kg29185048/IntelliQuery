# database/mongo_client.py

import certifi
from pymongo import MongoClient
from app.config import MONGO_URI

def get_db():
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    return client["sample_mflix"]

def get_db_from_uri(uri: str, db_name: str = None):
    """Build a MongoClient from a user-supplied URI and return the database.
    db_name: explicit database name (from X-Mongo-Db header or URI path).
    """
    from urllib.parse import urlparse
    resolved = db_name.strip() if db_name and db_name.strip() else urlparse(uri).path.strip("/")
    if not resolved:
        raise ValueError(
            "No database name provided. Enter the database name in the 'Database Name' field."
        )
    client = MongoClient(
        uri,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=10000,
    )
    return client[resolved]
