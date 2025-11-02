import mysql.connector
from mysql.connector import pooling, Error

# Global connection pool
_mysql_pool = None

def initialize_mysql_pool(pool_name='myapp_pool', pool_size=10):
    """
    Initializes MySQL connection pool (call once at app startup)
    """
    global _mysql_pool
    try:
        _mysql_pool = pooling.MySQLConnectionPool(
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

def get_mysql_connection():
    """
    Gets a connection from the pool
    """
    global _mysql_pool
    if _mysql_pool is None:
        initialize_mysql_pool()
    
    try:
        connection = _mysql_pool.get_connection()
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error getting connection from pool: {e}")
        return None

def close_connection(connection):
    """
    Returns connection to pool (not actually closing)
    """
    if connection and connection.is_connected():
        connection.close()  # Returns to pool automatically

def shutdown_pool():
    """
    Closes all connections in pool (call on app shutdown)
    """
    global _mysql_pool
    if _mysql_pool:
        # Pool will auto-close connections when garbage collected
        _mysql_pool = None
        print("MySQL connection pool shutdown")

def test_connection():
    """
    Test function to verify MySQL connection
    """
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