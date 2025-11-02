from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Global MongoDB client (thread-safe, connection pooling built-in)
_mongo_client = None
_mongo_db = None

def initialize_mongo_connection():
    """
    Initializes MongoDB client once (call at app startup)
    """
    global _mongo_client, _mongo_db
    
    if _mongo_client is not None:
        return _mongo_db
    
    try:
        MONGO_URI = "mongodb+srv://p1-20_db_user:p1-20@db-p1-20.fecspzj.mongodb.net/"
        DB_NAME = "Non-Relational"
        
        # MongoDB client automatically uses connection pooling
        _mongo_client = MongoClient(
            MONGO_URI,
            maxPoolSize=50,  # Max connections in pool
            minPoolSize=10,  # Min connections kept alive
            maxIdleTimeMS=45000
        )
        
        _mongo_client.admin.command('ping')
        print("MongoDB client initialized with connection pooling")
        
        _mongo_db = _mongo_client[DB_NAME]
        return _mongo_db
        
    except ConnectionFailure as e:
        print(f"Error initializing MongoDB: {e}")
        return None

def get_mongo_connection():
    """
    Returns the shared MongoDB database instance
    """
    global _mongo_db
    if _mongo_db is None:
        return initialize_mongo_connection()
    return _mongo_db

def close_mongo_connection():
    """
    Closes MongoDB client (call on app shutdown)
    """
    global _mongo_client, _mongo_db
    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None
        _mongo_db = None
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