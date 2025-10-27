import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from gui.gui_home import HomeWindow  # Import the home window as the main starting point

def main():
    try:
        # Enable High DPI display with PyQt5
        if hasattr(Qt, 'AA_EnableHighDpiScaling'):
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # Create the main application object
        app = QApplication(sys.argv)
        
        # Create the main window
        home_window = HomeWindow()
        
        # Show the window
        home_window.show()
        
        # Start the event loop
        return app.exec_()
    except Exception as e:
        print(f"Fatal error: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())