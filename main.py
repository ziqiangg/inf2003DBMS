# main.py

import sys
from PyQt5.QtWidgets import QApplication
from gui.gui_home import HomeWindow
from database.db_connection import initialize_mysql_pool, shutdown_pool
from database.db_mongo_connection import initialize_mongo_connection, close_mongo_connection

def main():
    # Initialize connection pools before creating GUI
    print("Initializing database connections...")
    initialize_mysql_pool(pool_size=10)
    initialize_mongo_connection()
    
    app = QApplication(sys.argv)
    
    home_window = HomeWindow()
    home_window.show()
    
    # Cleanup on exit
    exit_code = app.exec_()
    
    print("Shutting down database connections...")
    shutdown_pool()
    close_mongo_connection()
    
    sys.exit(exit_code)

if __name__ == '__main__':
    main()