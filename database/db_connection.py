import mysql.connector
from mysql.connector import pooling, Error
import threading

class MySQLConnectionManager:
    """Thread-safe singleton for MySQL connection pool management"""
    _instance = None
    _lock = threading.Lock()
    _pool = None
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(MySQLConnectionManager, cls).__new__(cls)
        return cls._instance
    
    def initialize_pool(self, pool_name='myapp_pool', pool_size=10):
        """Initialize MySQL connection pool (call once at app startup)"""
        if self._pool is not None:
            print("MySQL pool already initialized")
            return True
            
        try:
            self._pool = pooling.MySQLConnectionPool(
                pool_name=pool_name,
                pool_size=pool_size,
                pool_reset_session=True,
                host='100.124.52.6',
                database='INF2003_DBS_P1_20',
                user='p1_20_db_user',
                password='p1_20',
                port=3306
            )
            print(f"MySQL connection pool created with {pool_size} connections")
            return True
        except Error as e:
            print(f"Error creating connection pool: {e}")
            return False
    
    def get_connection(self):
        """Gets a connection from the pool"""
        if self._pool is None:
            self.initialize_pool()
        
        try:
            connection = self._pool.get_connection()
            if connection.is_connected():
                return connection
        except Error as e:
            print(f"Error getting connection from pool: {e}")
            return None
    
    def close_connection(self, connection):
        """Returns connection to pool"""
        if connection and connection.is_connected():
            connection.close()
    
    def shutdown_pool(self):
        """Closes all connections in pool (call on app shutdown)"""
        if self._pool:
            self._pool = None
            print("MySQL connection pool shutdown")

# Global singleton instance and convenience functions for backward compatibility
_manager = MySQLConnectionManager()

def initialize_mysql_pool(pool_size=10):
    """Initialize MySQL connection pool (convenience function)"""
    return _manager.initialize_pool(pool_size=pool_size)

def get_mysql_connection():
    """Get a connection from the pool (convenience function)"""
    return _manager.get_connection()

def close_connection(connection):
    """Return connection to pool (convenience function)"""
    return _manager.close_connection(connection)

def shutdown_pool():
    """Close all connections in pool (convenience function)"""
    return _manager.shutdown_pool()

def test_connection():
    """Test function to verify MySQL connection"""
    connection = get_mysql_connection()
    if connection:
        print("MySQL connection test successful!")
        cursor = connection.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"MySQL Server version: {version}")
        cursor.close()
        close_connection(connection)
        return True
    else:
        print("MySQL connection test failed!")
        return False

if __name__ == "__main__":
    test_connection()