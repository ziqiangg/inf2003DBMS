import mysql.connector
from mysql.connector import Error
import os


def get_mysql_connection():
    """
    Creates and returns a MySQL database connection
    """
    try:
        connection = mysql.connector.connect(
            host='100.124.52.6',           # Your MySQL host
            database='INF2003_DBS_P1_20',  # Your database name
            user='p1_20_db_user',          # Your username
            password='p1_20',              # Your password
            port=3306
        )
        
        if connection.is_connected():
            print("Successfully connected to MySQL database")
            return connection
            
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return None

def close_connection(connection):
    """
    Closes the MySQL database connection
    """
    if connection and connection.is_connected():
        connection.close()
        print("MySQL connection closed")

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