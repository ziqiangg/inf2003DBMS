# gui/gui_home.py

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QGridLayout, QMessageBox, QFrame, QTextEdit, QSizePolicy, QSpacerItem, QLineEdit, QComboBox
)
from PyQt5.QtCore import Qt, QUrl # Added QUrl for potential link handling
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import sys
from gui.session_manager import SessionManager
from gui.gui_signals import global_signals
from database.services.movie_service import MovieService
from database.services.genre_service import GenreService
from gui.gui_movie_detail import MovieDetailWindow
from gui.gui_profile import ProfileWindow
from gui.utils import is_placeholder_url, DEFAULT_POSTER_PATH, load_default_poster
import weakref



class HomeWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Movie Rating System - Home')
        self.setGeometry(100, 100, 1200, 800)
        self.session_manager = SessionManager()
        self.movie_service = MovieService()
        self.genre_service = GenreService()
        # Current filter state for searches
        self.current_genre = None
        self.current_year = None
        self.current_rating = None
        # Map active QNetworkReply objects to (label_ref, movie_title) so handlers
        # can find the right widget when signals arrive. This helps avoid lambda
        # closures which can sometimes lead to duplicate signal handling.
        self._reply_map = {}
        # Initialize current page state
        self.current_page = 1
        self.movies_per_page = 20
        self.max_pages = 10
        # Track if we are in search mode
        self.search_mode = False
        self.current_search_term = ""
        # Initialize the Network Access Manager for async image loading
        self.network_manager = QNetworkAccessManager()
        self.profile_window_ref = None
        global_signals.movie_data_updated.connect(self.on_movie_data_updated)
        self.init_ui()
        self.load_movies_page(self.current_page)

    # Slot to handle the signal
    def on_movie_data_updated(self, tmdb_id):
        """Reloads the current page of movies or search results if the updated movie is visible."""
        print(f"DEBUG: HomeWindow.on_movie_data_updated: Received signal for tmdbID {tmdb_id}.")
        # Check if we are currently showing paginated movies or search results
        if self.search_mode and (self.current_search_term or self.current_genre or self.current_year):
            # If in search mode, reload the search results
            print(f"DEBUG: HomeWindow.on_movie_data_updated: Reloading search results for title='{self.current_search_term}', genre='{self.current_genre}', year='{self.current_year}'.")
            self.load_search_results()
        else:
            # If in pagination mode, reload the current page
            print(f"DEBUG: HomeWindow.on_movie_data_updated: Reloading current page {self.current_page}.")
            self.load_movies_page(self.current_page) # This will fetch the updated average ratings

    def init_ui(self):
        main_layout = QVBoxLayout()

        # --- Top Bar (User Info, Login Button, Logout Button) ---
        top_bar_layout = QHBoxLayout()

        # Show user info if logged in, otherwise show a generic message
        if self.session_manager.is_logged_in():
            self.user_label = QLabel(f"Logged in as: {self.session_manager.get_current_user_email()} ({self.session_manager.get_current_user_role()})")
            logout_button = QPushButton("Logout")
            logout_button.clicked.connect(self.logout)
            profile_button = QPushButton("Profile")
            profile_button.clicked.connect(self.open_profile_window)
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

        # --- Search Bar ---
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search movies by title...") # Optional: Add placeholder text
        # Add genre and year dropdowns with descriptive defaults
        self.genre_combo = QComboBox()
        self.genre_combo.addItem("All Genre")
        try:
            genres = self.genre_service.get_all_genres()
            for g in genres:
                # genre service returns dict rows with 'genreName'
                name = g.get('genreName') if isinstance(g, dict) else str(g)
                if name:
                    self.genre_combo.addItem(name)
        except Exception as e:
            print(f"DEBUG: Failed to load genres for dropdown: {e}")

        self.year_combo = QComboBox()
        self.year_combo.addItem("All Year")
        try:
            years = self.movie_service.get_available_years()
            for y in years:
                self.year_combo.addItem(str(y))
        except Exception as e:
            # Fallback: populate a range if DB call fails
            print(f"DEBUG: Failed to load years from DB: {e}")
            import datetime
            current_year = datetime.datetime.now().year
            for y in range(current_year, current_year-30, -1):
                self.year_combo.addItem(str(y))

        # Average rating dropdown (minimum average rating)
        self.rating_combo = QComboBox()
        self.rating_combo.addItem("Any Rating")
        # Options represent minimum average rating threshold
        rating_options = ["0+", "1+", "2+", "3+", "4+", "5"]
        for r in rating_options:
            self.rating_combo.addItem(r)

        search_button = QPushButton("Search")
        clear_search_button = QPushButton("Clear") # Add a clear button

        search_button.clicked.connect(self.perform_search)
        clear_search_button.clicked.connect(self.clear_search)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.genre_combo)
        search_layout.addWidget(self.year_combo)
        search_layout.addWidget(self.rating_combo)
        search_layout.addWidget(search_button)
        search_layout.addWidget(clear_search_button) # Add the clear button
        main_layout.addLayout(search_layout)

        # --- Movie Grid Area ---
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.movie_grid_layout = QGridLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True) # Allow the scroll area to expand with content
        main_layout.addWidget(self.scroll_area)

        # --- Pagination Controls (Arrows only) ---
        self.pagination_layout = QHBoxLayout() # Store as instance variable
        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(lambda: self.change_page(self.current_page - 1))
        self.page_label = QLabel("Page 1") # This will be updated
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(lambda: self.change_page(self.current_page + 1))

        self.pagination_layout.addStretch() # Push controls to the center
        self.pagination_layout.addWidget(self.prev_button)
        self.pagination_layout.addWidget(self.page_label)
        self.pagination_layout.addWidget(self.next_button)
        self.pagination_layout.addStretch()
        main_layout.addLayout(self.pagination_layout)
        # Show/hide based on search mode initially (default is pagination)
        self.update_pagination_visibility()

        # --- REMOVED: Dynamic Page Number Buttons (1, 2, 3, ...) ---
        # self.page_buttons_layout = QHBoxLayout()
        # Buttons will be added dynamically by load_movies_page (REMOVED)
        # main_layout.addLayout(self.page_buttons_layout) (REMOVED)

        self.setLayout(main_layout)
    
    def perform_search(self):
        """Handles the search button click."""
        search_term = self.search_input.text().strip()
        # Read dropdown selections
        selected_genre = self.genre_combo.currentText() if hasattr(self, 'genre_combo') else None
        selected_year = self.year_combo.currentText() if hasattr(self, 'year_combo') else None
        selected_rating = self.rating_combo.currentText() if hasattr(self, 'rating_combo') else None

        # Normalize default labels to None
        genre = None if (not selected_genre or selected_genre in ['Genre', 'All Genre']) else selected_genre
        year = None if (not selected_year or selected_year in ['Year', 'All Year']) else selected_year

        # Parse rating selection into a numeric minimum average (None for Any Rating)
        rating = None
        if selected_rating and selected_rating != 'Any Rating':
            try:
                # '3+' -> 3, '5' -> 5
                rating = float(selected_rating.replace('+', ''))
            except Exception:
                rating = None

        # Set current filter state
        self.current_search_term = search_term
        self.current_genre = genre
        self.current_year = year
        self.current_rating = rating
        # Debug print for selected filters
        print(f"DEBUG: perform_search filters -> title='{search_term}', genre='{genre}', year='{year}', min_avg_rating='{rating}'")

        # If any filter is present, perform search. Otherwise clear.
        self.current_page = 1  # Reset to first page for new search
        if search_term or genre or year or rating is not None:
            self.search_mode = True
            self.load_search_results()
        else:
            self.clear_search()

    def clear_search(self):
        """Clears the search input, dropdowns, and results, returning to pagination mode."""
        print("DEBUG: Clearing search and filters")
        self.search_input.clear()
        self.genre_combo.setCurrentText("All Genre")  # Reset genre to default
        self.year_combo.setCurrentText("All Year")    # Reset year to default
        self.rating_combo.setCurrentText("Any Rating")
        self.current_search_term = ""
        self.current_genre = None
        self.current_year = None
        self.current_rating = None
        self.search_mode = False
        self.current_page = 1 # Reset to first page for pagination
        self.load_movies_page(self.current_page) # Reload paginated movies
        self.update_pagination_visibility() # Show pagination controls again

    def update_pagination_visibility(self):
        """Shows or hides pagination controls based on search mode and results."""
        self.prev_button.show()
        self.page_label.show()
        self.next_button.show()

    def load_search_results(self):
        """Fetches search results using current filters and updates the UI with pagination."""
        # Get paginated search results
        result = self.movie_service.search_movies_by_title(
            search_term=self.current_search_term,
            genre=self.current_genre,
            year=self.current_year,
            min_avg_rating=self.current_rating,
            page_number=self.current_page,
            movies_per_page=self.movies_per_page,
            max_pages=self.max_pages
        )

        print(f"DEBUG: Found results for title='{self.current_search_term}', genre='{self.current_genre}', "
              f"year='{self.current_year}', min_avg_rating='{self.current_rating}', "
              f"page {result['current_page']} of {result['total_pages']}")

        # Clear existing movie widgets from the grid layout
        while self.movie_grid_layout.count():
            child = self.movie_grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Populate the grid with search results
        if result['movies']:
            row, col = 0, 0
            for movie in result['movies']:
                movie_widget = self.create_movie_widget(movie)
                self.movie_grid_layout.addWidget(movie_widget, row, col)
                col += 1
                if col > 3:  # Show 4 movies per row
                    col = 0
                    row += 1
        else:
            # Show a message if no results found
            no_results_label = QLabel("No movies found matching your search.")
            no_results_label.setAlignment(Qt.AlignCenter)
            self.movie_grid_layout.addWidget(no_results_label, 0, 0, 1, 4)  # Span 4 columns

        # Update pagination display
        self.page_label.setText(f"Page {result['current_page']} of {result['total_pages']}")
        self.prev_button.setEnabled(result['has_prev'])
        self.next_button.setEnabled(result['has_next'])

    def load_movies_page(self, page_number):
        """Fetches movies for the given page and updates the UI."""
        self.current_page = page_number
        result = self.movie_service.get_movies_for_homepage(
            page_number=self.current_page,
            movies_per_page=self.movies_per_page,
            max_pages=self.max_pages
        )
        
        # Clear existing movie widgets from the grid layout
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
            if col > 3:  # Show 4 movies per row
                col = 0
                row += 1

        # Update pagination controls
        if not self.search_mode:
            self.page_label.setText(f"Page {self.current_page} of {result['total_pages']}")
            self.prev_button.setEnabled(result['has_prev'])
            self.next_button.setEnabled(result['has_next'])

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
        if not self.search_mode:
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
            # Store a weakref and title for this reply so handlers can look them up
            label_ref = weakref.ref(poster_label)
            movie_title = movie_data.get('title', 'Unknown')
            try:
                # Map the reply object (QObject) to its context
                self._reply_map[reply] = (label_ref, movie_title)
            except Exception:
                # If reply is not hashable for some reason, fall back to the lambda approach
                reply.finished.connect(lambda r=reply, lr=label_ref, mt=movie_title: self.on_image_load_finished(r, lr, mt))
            else:
                # Connect centralized handlers which use sender() to find reply
                # Bind finished and errorOccurred when available.
                try:
                    reply.finished.connect(self._on_image_reply_finished)
                except Exception:
                    # Fallback: if finished doesn't accept this slot, use lambda
                    reply.finished.connect(lambda r=reply: self._on_image_reply_finished())
                try:
                    # errorOccurred is available in newer PyQt5/Qt versions
                    reply.errorOccurred.connect(self._on_image_reply_error)
                except Exception:
                    # Older versions may not have errorOccurred; ignore (finished will still be invoked)
                    pass
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
        sum_ratings = movie_data.get('totalRatings', 0) # Retrieves the SUM from the database row
        num_ratings = movie_data.get('countRatings', 0) # Retrieves the COUNT from the database row
        avg_rating = 0.0
        if num_ratings > 0:
            avg_rating = sum_ratings / num_ratings

        # NEW: Display the CALCULATED average
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

    def on_image_load_finished(self, reply, poster_label_ref, movie_title):
        """
        Callback function called when the QNetworkReply finishes.
        Updates the specific poster_label with the loaded image or the default image.
        """
        poster_label = poster_label_ref()
        if poster_label is None:
            reply.deleteLater()
            return

        if reply.error() == QNetworkReply.NoError:  # Success
            image_data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(200, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                poster_label.setPixmap(scaled_pixmap)
            else:
                print(f"Could not load image data for movie '{movie_title}' from {reply.url().toString()}")
                load_default_poster(poster_label, size=(200, 300))
        else:  # Error (e.g., 404, timeout, network failure)
            load_default_poster(poster_label, size=(200, 300))

        reply.deleteLater()

    def _handle_reply_once(self, reply):
        """Internal helper to ensure a reply is processed only once.

        Returns (label_ref, movie_title) tuple or (None, None) if already handled
        or not found.
        """
        # Use the map we maintain to find the widget context
        try:
            if reply in self._reply_map:
                label_ref, movie_title = self._reply_map.pop(reply)
            else:
                return None, None
        except Exception:
            # If reply isn't hashable or any other issue, bail out
            return None, None

        # Mark handled via a property to be extra-safe
        try:
            if reply.property('handled'):
                return None, None
            reply.setProperty('handled', True)
        except Exception:
            pass

        return label_ref, movie_title

    def _on_image_reply_finished(self):
        """Called when a QNetworkReply emits finished(). Uses sender() to locate context."""
        reply = self.sender()
        if reply is None:
            return
        # Debug lifecycle
        try:
            url = reply.url().toString()
        except Exception:
            url = '<unknown>'
        print(f"DEBUG: _on_image_reply_finished for {url}")

        label_ref, movie_title = self._handle_reply_once(reply)
        if label_ref is None:
            reply.deleteLater()
            return

        # Reuse the existing image processing routine
        try:
            self.on_image_load_finished(reply, label_ref, movie_title)
        except Exception as e:
            print(f"ERROR: Exception processing finished reply: {e}")
            reply.deleteLater()

    def _on_image_reply_error(self, code):
        """Called when a QNetworkReply emits errorOccurred(code)."""
        reply = self.sender()
        if reply is None:
            return
        try:
            url = reply.url().toString()
        except Exception:
            url = '<unknown>'
        print(f"DEBUG: _on_image_reply_error code={code} for {url}")

        label_ref, movie_title = self._handle_reply_once(reply)
        if label_ref is None:
            reply.deleteLater()
            return

        # Treat error like finished but on_image_load_finished will choose default image
        try:
            self.on_image_load_finished(reply, label_ref, movie_title)
        except Exception as e:
            print(f"ERROR: Exception processing error reply: {e}")
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
        """Changes the displayed movie page for both search results and homepage."""
        if new_page != self.current_page:  # Only reload if page actually changed
            self.current_page = new_page
            if self.search_mode:
                self.load_search_results()
            else:
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

            profile_button = QPushButton("Profile")
            profile_button.clicked.connect(self.open_profile_window)

            top_bar_layout.addWidget(self.user_label)
            top_bar_layout.addStretch() # Push logout button to the right
            top_bar_layout.addWidget(logout_button)
            top_bar_layout.addWidget(profile_button)
            
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

    def open_profile_window(self):
        """Opens the profile window."""
        # Check if a profile window is already open, optionally bring it to front
        if self.profile_window_ref and not self.profile_window_ref.isHidden():
             print("DEBUG: HomeWindow.open_profile_window: Profile window already open, raising it.")
             self.profile_window_ref.raise_()
             self.profile_window_ref.activateWindow()
             return

        # Create the new profile window instance
        new_profile_window = ProfileWindow(session_manager=self.session_manager)
        # Connect the window's destroyed signal BEFORE storing the reference
        new_profile_window.destroyed.connect(self.on_profile_window_closed)
        # Store the reference to the NEW window instance
        self.profile_window_ref = new_profile_window
        # Show the NEW window
        self.profile_window_ref.show()
    
    def on_profile_window_closed(self):
        """Called when the profile window is destroyed."""
        print("DEBUG: HomeWindow.on_profile_window_closed: Profile window reference cleared.")
        # It's possible this is called multiple times or if the reference was already cleared
        # Check if the sender is the same object as the stored reference before clearing
        # sender() returns the object that emitted the signal
        sender_obj = self.sender() # Get the object that triggered the signal
        if sender_obj == self.profile_window_ref:
            # Only clear the reference if the destroyed object is the one we were tracking
            self.profile_window_ref = None

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