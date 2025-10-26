# gui/gui_register.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QApplication
from database.services.user_service import UserService
from gui.session_manager import SessionManager

class RegisterWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Movie Rating System - Register')
        self.setGeometry(150, 150, 300, 200)

        self.user_service = UserService()
        self.session_manager = SessionManager()

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Form Layout for Email and Password
        form_layout = QFormLayout()
        self.email_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.Password)

        form_layout.addRow("Email:", self.email_input)
        form_layout.addRow("Password:", self.password_input)
        form_layout.addRow("Confirm Password:", self.confirm_password_input)

        layout.addLayout(form_layout)

        # Register Button
        self.register_button = QPushButton('Register')
        self.register_button.clicked.connect(self.attempt_register)
        layout.addWidget(self.register_button)

        self.setLayout(layout)

    def attempt_register(self):
        email = self.email_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()

        if not email or not password or not confirm_password:
            QMessageBox.warning(self, 'Input Error', 'Please fill in all fields.')
            return

        if password != confirm_password:
            QMessageBox.critical(self, 'Password Mismatch', 'Passwords do not match.')
            return

        result = self.user_service.register_user(email, password)

        if result["success"]:
            QMessageBox.information(self, 'Registration Successful', result["message"])
            # Optionally, log the user in automatically after registration
            # login_result = self.user_service.login_user(email, password)
            # if login_result["success"]:
            #     self.session_manager.login(login_result["user_id"], email, login_result["role"])
            #     self.close()
            #     self.main_window = HomeWindow() # Pass session info if needed
            #     self.main_window.show()
            # else:
            #     # This should ideally not happen if registration was successful
            #     QMessageBox.critical(self, 'Login Error', 'Registration succeeded but login failed.')
            # For now, just show success and close
            self.close()
        else:
            QMessageBox.critical(self, 'Registration Failed', result["message"])


# Example of standalone run (usually called from gui_login.py)
# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     register_window = RegisterWindow()
#     register_window.show()
#     sys.exit(app.exec_())