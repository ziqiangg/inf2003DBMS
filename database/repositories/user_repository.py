# database/repositories/user_repository.py

from database.db_connection import get_mysql_connection, close_connection
from database.sql_queries import (
    CHECK_USER_EXISTS_BY_EMAIL,
    INSERT_NEW_USER,
    GET_USER_BY_EMAIL,
    SOFT_DELETE_USER
)

class UserRepository:
    def __init__(self):
        pass

    def check_user_exists(self, email):
        """Checks if a user already exists by email."""
        connection = get_mysql_connection()
        if not connection:
            return False
        cursor = connection.cursor()
        try:
            cursor.execute(CHECK_USER_EXISTS_BY_EMAIL, (email,))
            result = cursor.fetchone()
            return result is not None  # Returns True if user exists, False otherwise
        except Exception as e:
            print(f"Error checking user existence: {e}")
            return False
        finally:
            cursor.close()
            close_connection(connection)

    def create_user(self, email, password_hash):
        """Creates a new user in the database."""
        connection = get_mysql_connection()
        if not connection:
            return None
        cursor = connection.cursor()
        try:
            cursor.execute(INSERT_NEW_USER, (email, password_hash))
            connection.commit()
            user_id = cursor.lastrowid # Get the ID of the newly inserted user
            return user_id
        except Exception as e:
            print(f"Error creating user: {e}")
            connection.rollback()
            return None
        finally:
            cursor.close()
            close_connection(connection)

    def get_user_by_email(self, email):
        """Retrieves user information by email."""
        connection = get_mysql_connection()
        if not connection:
            return None
        cursor = connection.cursor(dictionary=True) # Use dictionary cursor for easier access
        try:
            cursor.execute(GET_USER_BY_EMAIL, (email,))
            user = cursor.fetchone()
            # --- DEBUG PRINT ---
            print(f"DEBUG: Retrieved user from DB: {user}")
            # --- END DEBUG PRINT ---
            return user
        except Exception as e:
            print(f"Error retrieving user: {e}")
            return None
        finally:
            cursor.close()
            close_connection(connection)

    def soft_delete_user(self, user_id):
        """Soft deletes a user by removing email and password."""
        connection = get_mysql_connection()
        if not connection:
            return False
        cursor = connection.cursor()
        try:
            cursor.execute(SOFT_DELETE_USER, (user_id,))
            connection.commit()
            # Check if any rows were affected to confirm deletion attempt
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error soft deleting user: {e}")
            connection.rollback()
            return False
        finally:
            cursor.close()
            close_connection(connection)

# Example usage (optional, for testing):
# if __name__ == "__main__":
#     repo = UserRepository()
#     # Test check_user_exists
#     print("User exists:", repo.check_user_exists("test@example.com"))
#     # Test get_user_by_email
#     user_data = repo.get_user_by_email("test@example.com")
#     print("User ", user_data)