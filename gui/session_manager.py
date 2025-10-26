# gui/session_manager.py

class SessionManager:
    _instance = None
    _user_id = None
    _email = None
    _role = 'guest'  # Default role is guest

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
        return cls._instance

    def login(self, user_id, email, role):
        """Sets the session information when a user logs in."""
        self._user_id = user_id
        self._email = email
        self._role = role

    def logout(self):
        """Clears the session information when a user logs out."""
        self._user_id = None
        self._email = None
        self._role = 'guest'

    def is_logged_in(self):
        """Checks if a user is currently logged in."""
        return self._user_id is not None

    def get_current_user_id(self):
        """Returns the ID of the currently logged-in user, or None if not logged in."""
        return self._user_id

    def get_current_user_email(self):
        """Returns the email of the currently logged-in user, or None if not logged in."""
        return self._email

    def get_current_user_role(self):
        """Returns the role of the currently logged-in user ('guest', 'user', 'admin')."""
        return self._role

# Example usage:
# session = SessionManager()
# session.login(123, "user@example.com", "user")
# print(session.is_logged_in())  # True
# print(session.get_current_user_role())  # 'user'
# session.logout()
# print(session.is_logged_in())  # False