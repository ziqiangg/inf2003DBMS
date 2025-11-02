from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import threading

class MongoConnectionManager:
    """Thread-safe singleton for MongoDB connection management"""
    _instance = None
    _lock = threading.Lock()
    _client = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(MongoConnectionManager, cls).__new__(cls)
        return cls._instance
    
    def initialize_connection(self):
        """Initialize MongoDB client once (call at app startup)"""
        if self._client is not None:
            print("MongoDB client already initialized")
            return self._db
        
        try:
            MONGO_URI = "mongodb+srv://p1-20_db_user:p1-20@db-p1-20.fecspzj.mongodb.net/"
            DB_NAME = "Non-Relational"
            
            # MongoDB client automatically uses connection pooling
            self._client = MongoClient(
                MONGO_URI,
                maxPoolSize=50,
                minPoolSize=10,
                maxIdleTimeMS=45000
            )
            
            self._client.admin.command('ping')
            print("MongoDB client initialized with connection pooling")
            
            self._db = self._client[DB_NAME]
            return self._db
            
        except ConnectionFailure as e:
            print(f"Error initializing MongoDB: {e}")
            return None
    
    def get_database(self):
        """Returns the shared MongoDB database instance"""
        if self._db is None:
            return self.initialize_connection()
        return self._db
    
    def close_connection(self):
        """Closes MongoDB client (call on app shutdown)"""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            print("MongoDB connection closed")

# Global singleton instance and convenience functions for backward compatibility
_manager = MongoConnectionManager()

def initialize_mongo_connection():
    """Initialize MongoDB client (convenience function)"""
    return _manager.initialize_connection()

def get_mongo_connection():
    """Get MongoDB database instance (convenience function)"""
    return _manager.get_database()

def close_mongo_connection():
    """Close MongoDB client (convenience function)"""
    return _manager.close_connection()

def test_mongo_connection():
    """Test function to verify MongoDB connection"""
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