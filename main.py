# main.py

import sys
from PyQt5.QtWidgets import QApplication
from gui.gui_home import HomeWindow # Import the home window as the main starting point
# from gui.gui_login import LoginWindow # We might import this conditionally now

def main():
    # Create the main application object
    app = QApplication(sys.argv)

    # Create and show the initial window (Home Window)
    # The HomeWindow will handle checking session state and showing login button if needed
    home_window = HomeWindow()
    home_window.show()

    # Start the application's event loop
    # This function call blocks until the application is closed.
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()