from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os

def get_mongo_connection():
    """
    Creates and returns a MongoDB connection
    """
    try:
        # Your MongoDB connection string
        MONGO_URI = "mongodb+srv://p1-20_db_user:p1-20@db-p1-20.fecspzj.mongodb.net/"
        DB_NAME = "Non-Relational"
        
        client = MongoClient(MONGO_URI)
        
        # Test the connection
        client.admin.command('ping')
        print("Successfully connected to MongoDB")
        
        db = client[DB_NAME]
        return db
        
    except ConnectionFailure as e:
        print(f"Error while connecting to MongoDB: {e}")
        return None

def get_mongo_client():
    """
    Returns the MongoDB client (useful for operations requiring the client object)
    """
    try:
        MONGO_URI = "mongodb+srv://p1-20_db_user:p1-20@db-p1-20.fecspzj.mongodb.net/"
        client = MongoClient(MONGO_URI)
        # Test the connection
        client.admin.command('ping')
        return client
    except ConnectionFailure as e:
        print(f"Error while connecting to MongoDB: {e}")
        return None

def close_mongo_connection(client):
    """
    Closes the MongoDB connection
    """
    if client:
        client.close()
        print("MongoDB connection closed")

def test_mongo_connection():
    """
    Test function to verify MongoDB connection
    """
    db = get_mongo_connection()
    if db:
        print("MongoDB connection test successful!")
        print(f"Connected to database: {db.name}")
        print(f"Available collections: {db.list_collection_names()}")
        return True
    else:
        print("MongoDB connection test failed!")
        return False

if __name__ == "__main__":
    test_mongo_connection()