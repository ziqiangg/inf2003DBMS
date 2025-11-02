# main.py

import sys
from PyQt5.QtWidgets import QApplication
from gui.gui_home import HomeWindow
from database.db_connection import MySQLConnectionManager
from database.db_mongo_connection import MongoConnectionManager

def main():
    # Initialize singleton connection managers
    print("Initializing database connections...")
    
    # Get singleton instances and initialize
    mysql_manager = MySQLConnectionManager()
    mongo_manager = MongoConnectionManager()
    
    mysql_manager.initialize_pool(pool_size=10)
    mongo_manager.initialize_connection()
    
    app = QApplication(sys.argv)
    
    home_window = HomeWindow()
    home_window.show()
    
    # Cleanup on exit
    exit_code = app.exec_()
    
    print("Shutting down database connections...")
    mysql_manager.shutdown_pool()
    mongo_manager.close_connection()
    
    sys.exit(exit_code)

if __name__ == '__main__':
    main()