# database/services/user_service.py

import hashlib
import re
from database.repositories.user_repository import UserRepository

class UserService:
    def __init__(self):
        self.user_repo = UserRepository()

    def hash_password(self, password):
        """Hashes the password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def validate_email(self, email):
        """Validates the email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def validate_password(self, password):
        """Validates the password strength (basic example: length > 5)."""
        return len(password) > 5

    def register_user(self, email, password):
        """Registers a new user after validation."""
        if not self.validate_email(email):
            return {"success": False, "message": "Invalid email format."}

        if not self.validate_password(password):
            return {"success": False, "message": "Password must be at least 6 characters long."}

        if self.user_repo.check_user_exists(email):
            return {"success": False, "message": "A user with this email already exists."}

        password_hash = self.hash_password(password)
        user_id = self.user_repo.create_user(email, password_hash)

        if user_id:
            return {"success": True, "message": "Registration successful!", "user_id": user_id}
        else:
            return {"success": False, "message": "Registration failed due to a database error."}

    def login_user(self, email, password):
        """Logs in a user after validating credentials and checking role."""
        if not self.validate_email(email):
            return {"success": False, "message": "Invalid email format."}

        stored_user = self.user_repo.get_user_by_email(email)

        if not stored_user:
            return {"success": False, "message": "Invalid email or password."}

        # Handle soft-deleted users (where email/password might be NULL)
        # Use the correct key name 'email' (lowercase) as it appears in the DB schema
        if stored_user.get('email') is None or stored_user.get('passwordHash') is None:
             print(f"Login attempt for soft-deleted user ID: {stored_user['userID']}")
             return {"success": False, "message": "Account not found or access denied."}

        password_hash = self.hash_password(password)

        if stored_user['passwordHash'] == password_hash:
            # Credentials are valid, now check the role explicitly.
            # The system logic implies checking for 'admin' first.
            role = stored_user['role']
            if role == 'admin':
                # Successful admin login
                return {
                    "success": True,
                    "message": "Admin login successful!",
                    "user_id": stored_user['userID'],
                    "role": "admin" # Explicitly return 'admin'
                }
            elif role == 'user':
                # Successful standard user login
                return {
                    "success": True,
                    "message": "Login successful!",
                    "user_id": stored_user['userID'],
                    "role": "user" # Explicitly return 'user'
                }
            else:
                # Should not happen with CHECK constraint, but good practice to handle
                print(f"Unexpected role '{role}' for user ID: {stored_user['userID']}")
                return {"success": False, "message": "Login failed due to an unexpected user role."}
        else:
            return {"success": False, "message": "Invalid email or password."}

    def delete_user(self, user_id):
        """Soft deletes a user account."""
        # The service might perform additional checks or logging here before calling the repo
        success = self.user_repo.soft_delete_user(user_id)
        if success:
            return {"success": True, "message": "Account deleted successfully."}
        else:
            return {"success": False, "message": "Account deletion failed due to a database error."}

    def get_user_by_email(self, email):
        """Gets user data by email (for admin search functionality).
        
        Args:
            email (str): User's email address
            
        Returns:
            dict: Response with success status and user data
        """
        user = self.user_repo.get_user_by_email(email)
        if user:
            return {
                "success": True,
                "user": user
            }
        else:
            return {
                "success": False,
                "message": "User not found"
            }