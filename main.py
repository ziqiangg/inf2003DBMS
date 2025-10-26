# main.py

import sys
from PyQt5.QtWidgets import QApplication
from gui.gui_login import LoginWindow # Import the main starting window

def main():
    # Create the main application object
    app = QApplication(sys.argv)

    # Create and show the initial window (Login Window)
    login_window = LoginWindow()
    login_window.show()

    # Start the application's event loop
    # This function call blocks until the application is closed.
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()