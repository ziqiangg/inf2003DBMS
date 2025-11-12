# test_connections.py
from database.db_connection import get_mysql_connection, close_connection
from database.db_mongo_connection import get_mongo_connection

def test_mysql():
    print("Testing MySQL connection...")
    connection = get_mysql_connection()
    if connection:
        print("✅ MySQL connection successful!")
        # Test a simple query
        cursor = connection.cursor()
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        print(f"MySQL query result: {result}")
        cursor.close()
        close_connection(connection)
        return True
    else:
        print("❌ MySQL connection failed!")
        return False

def test_mongo():
    print("\nTesting MongoDB connection...")
    db = get_mongo_connection()
    if db is not None:  # Fix: Use 'is not None' instead of 'if db:'
        print("✅ MongoDB connection successful!")
        # Test a simple operation
        print(f"Connected to database: {db.name}")
        collections = db.list_collection_names()
        print(f"Available collections: {collections}")
        return True
    else:
        print("❌ MongoDB connection failed!")
        return False

if __name__ == "__main__":
    print("Starting database connection tests...\n")
    
    mysql_success = test_mysql()
    mongo_success = test_mongo()
    
    print(f"\nTest Results:")
    print(f"MySQL: {'✅ PASS' if mysql_success else '❌ FAIL'}")
    print(f"MongoDB: {'✅ PASS' if mongo_success else '❌ FAIL'}")
    
    if mysql_success and mongo_success:
        print("\n🎉 All database connections are working!")
    else:
        print("\n❌ Some connections failed. Please check your credentials and network.")