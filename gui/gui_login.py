# gui/gui_login.py
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QFormLayout
from gui.gui_register import RegisterWindow
from gui.session_manager import SessionManager
from database.services.user_service import UserService

class LoginWindow(QWidget):
    def __init__(self, home_window_instance=None): # Accept home window reference
        super().__init__()
        self.setWindowTitle('Movie Rating System - Login')
        self.setGeometry(100, 100, 300, 200)
        self.session_manager = SessionManager()
        self.user_service = UserService()
        # Store the reference to the main home window
        self.main_home_window = home_window_instance
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        # Form Layout for Email and Password
        form_layout = QFormLayout()
        self.email_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password) # Hide password input
        form_layout.addRow("Email:", self.email_input)
        form_layout.addRow("Password:", self.password_input)
        layout.addLayout(form_layout)
        # Login Button
        self.login_button = QPushButton('Login')
        self.login_button.clicked.connect(self.attempt_login)
        layout.addWidget(self.login_button)
        # Horizontal Layout for Register Link
        h_layout = QHBoxLayout()
        register_link = QLabel('<a href="#">Register here</a>')
        register_link.setOpenExternalLinks(False) # Prevent default browser behavior
        register_link.linkActivated.connect(self.open_register_window) # Connect to register function
        h_layout.addWidget(register_link)
        h_layout.addStretch() # Push the link to the left
        layout.addLayout(h_layout)
        self.setLayout(layout)

    def attempt_login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text()
        if not email or not password:
            QMessageBox.warning(self, 'Input Error', 'Please enter both email and password.')
            return

        result = self.user_service.login_user(email, password)
        if result["success"]:
            QMessageBox.information(self, 'Login Successful', result["message"])
            # Update session
            self.session_manager.login(result["user_id"], email, result["role"])
            # Update the home window UI if a reference exists ---
            if self.main_home_window:
                self.main_home_window.update_ui_after_login()
            # Close login window
            self.close()
            # The HomeWindow will now reflect the logged-in state due to the update_ui_after_login call
        else:
            QMessageBox.critical(self, 'Login Failed', result["message"])

    def open_register_window(self, link): # 'link' argument is passed by linkActivated signal
        self.register_window = RegisterWindow()
        self.register_window.show()

# Example of how to run the login window as the main application window
# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     login_window = LoginWindow()
#     login_window.show()
#     sys.exit(app.exec_())