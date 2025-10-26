# gui/gui_home.py

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QGridLayout, QMessageBox, QFrame, QTextEdit, QSizePolicy, QSpacerItem
)
from PyQt5.QtCore import Qt, QUrl # Added QUrl for potential link handling
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import sys
from gui.session_manager import SessionManager
from database.services.movie_service import MovieService
from gui.gui_movie_detail import MovieDetailWindow
from gui.utils import is_placeholder_url, DEFAULT_POSTER_PATH, load_default_poster


class HomeWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Movie Rating System - Home')
        self.setGeometry(100, 100, 1200, 800)
        self.session_manager = SessionManager()
        self.movie_service = MovieService()
        # Initialize current page state
        self.current_page = 1
        self.movies_per_page = 20
        self.max_pages = 10
        # Initialize the Network Access Manager for async image loading
        self.network_manager = QNetworkAccessManager()
        self.init_ui()
        self.load_movies_page(self.current_page)

    def init_ui(self):
        main_layout = QVBoxLayout()

        # --- Top Bar (User Info, Login Button, Logout Button) ---
        top_bar_layout = QHBoxLayout()

        # Show user info if logged in, otherwise show a generic message
        if self.session_manager.is_logged_in():
            self.user_label = QLabel(f"Logged in as: {self.session_manager.get_current_user_email()} ({self.session_manager.get_current_user_role()})")
            logout_button = QPushButton("Logout")
            logout_button.clicked.connect(self.logout)
            top_bar_layout.addWidget(self.user_label)
            top_bar_layout.addStretch() # Push logout button to the right
            top_bar_layout.addWidget(logout_button)
        else:
            # Show a generic message and a login button
            self.user_label = QLabel("Guest User") # Or just remove the user label entirely if desired
            login_button = QPushButton("Login / Register")
            login_button.clicked.connect(self.open_login_window)
            top_bar_layout.addWidget(self.user_label)
            top_bar_layout.addStretch() # Push login button to the right
            top_bar_layout.addWidget(login_button)

        main_layout.addLayout(top_bar_layout)

        # --- Search Bar (Optional for now, can be added later) ---
        # search_layout = QHBoxLayout()
        # self.search_input = QLineEdit()
        # search_button = QPushButton("Search")
        # search_layout.addWidget(self.search_input)
        # search_layout.addWidget(search_button)
        # main_layout.addLayout(search_layout)

        # --- Movie Grid Area ---
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.movie_grid_layout = QGridLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True) # Allow the scroll area to expand with content
        main_layout.addWidget(self.scroll_area)

        # --- Pagination Controls (Arrows only) ---
        pagination_layout = QHBoxLayout()
        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(lambda: self.change_page(self.current_page - 1))
        self.page_label = QLabel("Page 1") # This will be updated
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(lambda: self.change_page(self.current_page + 1))

        pagination_layout.addStretch() # Push controls to the center
        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_button)
        pagination_layout.addStretch()
        main_layout.addLayout(pagination_layout)

        # --- REMOVED: Dynamic Page Number Buttons (1, 2, 3, ...) ---
        # self.page_buttons_layout = QHBoxLayout()
        # Buttons will be added dynamically by load_movies_page (REMOVED)
        # main_layout.addLayout(self.page_buttons_layout) (REMOVED)

        self.setLayout(main_layout)

    def load_movies_page(self, page_number):
        """Fetches movies for the given page and updates the UI."""
        self.current_page = page_number
        result = self.movie_service.get_movies_for_homepage(
            page_number=self.current_page,
            movies_per_page=self.movies_per_page,
            max_pages=self.max_pages
        )

        # Clear existing movie widgets from the grid layout
        # Method to clear layout: https://stackoverflow.com/a/45790404
        # To remove widgets/layouts from a layout, you typically need to take them out and delete them
        while self.movie_grid_layout.count():
            child = self.movie_grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Populate the grid with new movies
        movies = result['movies']
        row, col = 0, 0
        for movie in movies:
            movie_widget = self.create_movie_widget(movie)
            self.movie_grid_layout.addWidget(movie_widget, row, col)
            col += 1
            if col > 3: # Show 4 movies per row
                col = 0
                row += 1

        # Update pagination controls
        self.page_label.setText(f"Page {self.current_page} of {result['total_pages']}")
        self.prev_button.setEnabled(result['has_prev'])
        self.next_button.setEnabled(result['has_next'])

    def create_movie_widget(self, movie_data):
        """Creates a QWidget representing a single movie."""
        widget = QWidget()
        widget.setFixedWidth(250) # Set a fixed width for consistency
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignTop) # Align contents to the top

        # Movie Poster
        poster_label = QLabel()
        poster_label.setFixedSize(200, 300) # Set a fixed size for posters
        poster_label.setAlignment(Qt.AlignCenter)
        poster_label.setStyleSheet("border: 1px solid gray;") # Add a border for clarity

        # Load poster image from URL or use default
        poster_url = movie_data.get('poster')
        # Use the helper function to check for placeholders/invalid URLs
        if is_placeholder_url(poster_url):
            # Use default image if poster is NULL, empty, or a known placeholder/invalid URL
            pixmap = QPixmap(DEFAULT_POSTER_PATH) # Load default image
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(200, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                poster_label.setPixmap(scaled_pixmap)
            else:
                poster_label.setText("No Poster") # Fallback if default image also fails
        else: # If poster_url is not a placeholder/invalid URL
            # --- ASYNC LOADING ---
            # Create a request object
            request = QNetworkRequest(QUrl(poster_url))
            # Set a short timeout for the request (optional, handled differently in async)
            request.setTransferTimeout(5000) # Timeout in milliseconds (e.g., 5 seconds)
            # Start the network request using the manager
            # The finished signal will be emitted when the request completes (success, failure, timeout)
            reply = self.network_manager.get(request)
            # Connect the 'finished' signal of the reply object to a lambda
            # This lambda captures the specific 'poster_label' widget for this movie
            # and the 'movie_data' title for potential error logging.
            # The lambda then calls the 'on_image_load_finished' method.
            reply.finished.connect(
                lambda: self.on_image_load_finished(reply, poster_label, movie_data.get('title', 'Unknown'))
            )
            # The label currently shows nothing or the old pixmap if reused. It will be updated by the callback.
            # You could set a temporary loading image here if desired.
            # --- END ASYNC LOADING ---
        # Movie Title
        title_label = QLabel(movie_data.get('title', 'Unknown Title'))
        title_label.setWordWrap(True) # Allow text wrapping
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        # Movie Overview (Truncated)
        overview_text = QTextEdit()
        overview_text.setMaximumHeight(60) # Limit height
        overview_text.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded) # Enable scrolling if needed
        overview_text.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) # Disable horizontal scrolling
        overview_text.setPlainText(movie_data.get('overview', 'No overview available.'))
        overview_text.setReadOnly(True) # Make it non-editable
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        size_policy.setVerticalStretch(0)
        overview_text.setSizePolicy(size_policy)

        # Release Date and Rating Info
        info_label = QLabel()
        release_date = movie_data.get('releaseDate')
        if release_date:
             # Format date if it's a string, or use strftime if it's a datetime object
             # Assuming it comes as 'YYYY-MM-DD' string from the DB
            formatted_date = str(release_date)[:10] # Get just the date part if datetime
        else:
            formatted_date = "Unknown Date"
        avg_rating = movie_data.get('totalRatings', 0)
        num_ratings = movie_data.get('countRatings', 0)
        info_label.setText(f"Release: {formatted_date} | Avg: {avg_rating:.1f}/5 ({num_ratings} ratings)")

        # Add widgets to the layout
        layout.addWidget(poster_label)
        layout.addWidget(title_label)
        layout.addWidget(overview_text)
        layout.addWidget(info_label)

        # Connect click event to open movie detail
        def open_detail():
            from gui.gui_movie_detail import MovieDetailWindow
            print(f"DEBUG: gui_home.py open_detail: Creating MovieDetailWindow for tmdbID {movie_data['tmdbID']}")
            detail_window = MovieDetailWindow(movie_data['tmdbID']) # Pass the movie ID
            print(f"DEBUG: gui_home.py open_detail: Attempting to show MovieDetailWindow")
            try:
                detail_window.show()
                print(f"DEBUG: gui_home.py open_detail: Successfully called show() on MovieDetailWindow")
            except Exception as e:
                print(f"ERROR: gui_home.py open_detail: Exception occurred when showing MovieDetailWindow: {e}")
                import traceback
                traceback.print_exc() # Print the full traceback for detailed error info
        widget.mousePressEvent = lambda event: open_detail() # Simulate click on the whole widget
        poster_label.mousePressEvent = lambda event: open_detail() # Also allow click on poster
        title_label.mousePressEvent = lambda event: open_detail() # Also allow click on title
        # Note: QTextEdit and QLabel are not focusable by default, so mousePressEvent might not work directly on them if they contain other focusable elements.
        # The widget-level event should handle most clicks.

        return widget

    def on_image_load_finished(self, reply, poster_label, movie_title):
        """
        Callback function called when the QNetworkReply finishes.
        Updates the specific poster_label with the loaded image or the default image.
        """
        # Check the status of the reply
        if reply.error() == QNetworkReply.NoError: # Success
            # Read the image data from the reply
            image_data = reply.readAll()
            # Create a QPixmap from the data
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            # Scale and set the pixmap on the specific label widget passed to this callback
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(200, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                poster_label.setPixmap(scaled_pixmap)
            else:
                # If QPixmap couldn't be created from data (unexpected), use default
                print(f"Could not load image data for movie '{movie_title}' from {reply.url().toString()}")
                load_default_poster(poster_label, size=(200, 300))
        else: # Error (e.g., 404, timeout, network failure)
            # Print the error for debugging (optional)
            # print(f"Failed to load poster for '{movie_title}' from {reply.url().toString()}: {reply.errorString()}")
            # Load the default poster for the specific label
            load_default_poster(poster_label, size=(200, 300))
        # Clean up the reply object to free resources
        reply.deleteLater()

    def load_default_poster(self, poster_label):
        """Helper function to load the default poster into a given label."""
        pixmap = QPixmap(DEFAULT_POSTER_PATH)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(200, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            poster_label.setPixmap(scaled_pixmap)
        else:
            poster_label.setText("No Poster")


    def change_page(self, new_page):
        """Changes the displayed movie page."""
        if new_page != self.current_page: # Only reload if page actually changed
            self.load_movies_page(new_page)

    def open_login_window(self):
        """Opens the login window and passes a reference to this HomeWindow instance."""
        # Import LoginWindow here to avoid circular import at module level
        from gui.gui_login import LoginWindow
        # Pass 'self' (the HomeWindow instance) to the LoginWindow
        self.login_window = LoginWindow(home_window_instance=self)
        self.login_window.show()

    def update_ui_after_login(self):
        """Updates the top bar UI elements based on the current session state."""
        # Clear the existing top bar layout content (excluding the main movie grid and pagination)
        # We'll recreate the top bar layout.
        # Get the main layout
        main_layout = self.layout()
        # Remove the old top bar layout (assuming it's the first item)
        old_top_bar = main_layout.itemAt(0)
        if old_top_bar:
            # Remove the layout item from the main layout
            main_layout.removeItem(old_top_bar)
            # Delete the widgets within the old layout
            while old_top_bar.count():
                child = old_top_bar.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            old_top_bar.deleteLater()

        # Create the new top bar layout based on the current session state
        top_bar_layout = QHBoxLayout()
        if self.session_manager.is_logged_in():
            self.user_label = QLabel(f"Logged in as: {self.session_manager.get_current_user_email()} ({self.session_manager.get_current_user_role()})")
            logout_button = QPushButton("Logout")
            logout_button.clicked.connect(self.logout)
            top_bar_layout.addWidget(self.user_label)
            top_bar_layout.addStretch() # Push logout button to the right
            top_bar_layout.addWidget(logout_button)
        else:
            # Show a generic message and a login button
            self.user_label = QLabel("Guest User") # Or just remove the user label entirely if desired
            login_button = QPushButton("Login / Register")
            login_button.clicked.connect(self.open_login_window)
            top_bar_layout.addWidget(self.user_label)
            top_bar_layout.addStretch() # Push login button to the right
            top_bar_layout.addWidget(login_button)

        # Insert the new top bar layout back at the top (index 0)
        main_layout.insertLayout(0, top_bar_layout)

        # Store references to the new widgets if needed later (though update_ui_after_logout might be simpler)
        # self.top_bar_layout = top_bar_layout # Not strictly necessary here, but good practice if you access it elsewhere

    def logout(self):
        """Handles user logout."""
        reply = QMessageBox.question(self, 'Logout', 'Are you sure you want to logout?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.session_manager.logout()
            # Update the UI to reflect the logged-out state
            self.update_ui_after_login()


# Example of how to run the home window (usually opened from gui_login.py after successful login)
# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     # Simulate a logged-in session for testing
#     session = SessionManager()
#     session.login(1, "test@example.com", "user")
#     home_window = HomeWindow()
#     home_window.show()
#     sys.exit(app.exec_())