# gui/gui_movie_detail.py

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QFormLayout, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPalette
import requests
from io import BytesIO
from gui.session_manager import SessionManager
from database.services.movie_service import MovieService
from database.services.rating_service import RatingService # Assuming you'll create this
from database.services.review_service import ReviewService # Assuming you'll create this

class MovieDetailWindow(QWidget):
    def __init__(self, tmdb_id):
        super().__init__()
        self.setWindowTitle('Movie Details')
        self.setGeometry(200, 200, 800, 600)

        self.tmdb_id = tmdb_id
        self.session_manager = SessionManager()
        self.movie_service = MovieService()
        # self.rating_service = RatingService() # Initialize if needed
        # self.review_service = ReviewService() # Initialize if needed

        self.movie_data = None # Will store the fetched movie details

        self.init_ui()
        self.load_movie_details()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # --- Top Bar (Back Button, User Info) ---
        top_bar_layout = QHBoxLayout()
        back_button = QPushButton("Back to Home")
        back_button.clicked.connect(self.close) # Simply close this window
        self.user_label = QLabel(f"Logged in as: {self.session_manager.get_current_user_email() or 'Guest'} ({self.session_manager.get_current_user_role()})")

        top_bar_layout.addWidget(back_button)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.user_label)
        main_layout.addLayout(top_bar_layout)

        # --- Movie Details Content ---
        content_frame = QFrame()
        content_layout = QVBoxLayout(content_frame)

        # Movie Poster and Info Side-by-Side
        top_info_layout = QHBoxLayout()

        # Poster
        self.poster_label = QLabel()
        self.poster_label.setFixedSize(300, 450) # Set a fixed size
        self.poster_label.setAlignment(Qt.AlignCenter)
        self.poster_label.setStyleSheet("border: 1px solid gray;")
        top_info_layout.addWidget(self.poster_label)

        # Info (Title, Release Date, Runtime, Rating, Overview, Link)
        info_layout = QFormLayout()

        self.title_label = QLabel("Title: Loading...")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        info_layout.addRow("Title:", self.title_label)

        self.release_date_label = QLabel("Release Date: Loading...")
        info_layout.addRow("Release Date:", self.release_date_label)

        self.runtime_label = QLabel("Runtime: Loading... mins")
        info_layout.addRow("Runtime:", self.runtime_label)

        self.rating_label = QLabel("Average Rating: Loading...")
        info_layout.addRow("Average Rating:", self.rating_label)

        self.overview_text = QTextEdit()
        self.overview_text.setMaximumHeight(100)
        self.overview_text.setReadOnly(True)
        info_layout.addRow("Overview:", self.overview_text)

        # Link (if available)
        self.link_label = QLabel("Official Website: N/A")
        self.link_label.setOpenExternalLinks(True) # Allow clicking on links
        info_layout.addRow("Link:", self.link_label)

        top_info_layout.addLayout(info_layout)
        content_layout.addLayout(top_info_layout)

        # --- Rating/Review Section (Visible only if logged in) ---
        self.rating_review_section = QFrame()
        rating_review_layout = QVBoxLayout(self.rating_review_section)

        # Rating Input
        self.rate_label = QLabel("Rate this movie (0-5):")
        self.rate_input = None # Will be created if user is logged in
        self.rate_button = None # Will be created if user is logged in

        # Review Input
        self.review_label = QLabel("Write a review:")
        self.review_input = None # Will be created if user is logged in
        self.review_submit_button = None # Will be created if user is logged in

        # Display existing ratings/reviews
        self.reviews_display = QTextEdit()
        self.reviews_display.setReadOnly(True)
        rating_review_layout.addWidget(QLabel("User Reviews:"))
        rating_review_layout.addWidget(self.reviews_display)

        content_layout.addWidget(self.rating_review_section)

        main_layout.addWidget(content_frame)

        self.setLayout(main_layout)

        # Initially hide the rating/review section if not logged in
        if not self.session_manager.is_logged_in():
            self.rating_review_section.setVisible(False)


    def load_movie_details(self):
        """Fetches and displays details for the movie specified by tmdb_id."""
        movie_data = self.movie_service.get_movie_detail(self.tmdb_id)

        if not movie_data:
            QMessageBox.critical(self, 'Error', f'Failed to load details for movie ID {self.tmdb_id}.')
            self.title_label.setText("Movie Not Found")
            return

        self.movie_data = movie_data

        # Update UI elements with movie data
        self.title_label.setText(movie_data.get('title', 'Unknown Title'))
        self.release_date_label.setText(str(movie_data.get('releaseDate', 'Unknown Date')))
        runtime = movie_data.get('runtime')
        self.runtime_label.setText(f"{runtime} mins" if runtime else "N/A")
        avg_rating = movie_data.get('totalRatings', 0)
        num_ratings = movie_data.get('countRatings', 0)
        self.rating_label.setText(f"{avg_rating:.2f}/5 ({num_ratings} ratings)")
        self.overview_text.setPlainText(movie_data.get('overview', 'No overview available.'))
        # Note: Link is not currently stored in the Movies table based on the schema provided earlier.
        # self.link_label.setText(f'<a href="{movie_data.get("link", "")}">Official Website</a>' if movie_data.get("link") else "N/A")

        # Load poster image
        poster_url = movie_data.get('poster')
        if poster_url:
            try:
                response = requests.get(poster_url)
                if response.status_code == 200:
                    pixmap = QPixmap()
                    pixmap.loadFromData(response.content)
                    scaled_pixmap = pixmap.scaled(300, 450, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.poster_label.setPixmap(scaled_pixmap)
                else:
                    self.poster_label.setText("No Poster")
            except Exception as e:
                print(f"Error loading poster: {e}")
                self.poster_label.setText("No Poster")
        else:
            self.poster_label.setText("No Poster")

        # If logged in, show rating/review inputs and populate reviews display
        if self.session_manager.is_logged_in():
            self.rating_review_section.setVisible(True)

            # --- Rating Input ---
            if self.rate_input is None: # Create only once
                self.rate_input = QTextEdit()
                self.rate_input.setMaximumHeight(30)
                self.rate_input.setPlaceholderText("Enter rating (0-5)")
                self.rate_button = QPushButton("Submit Rating")
                self.rate_button.clicked.connect(self.submit_rating)

                rate_layout = QHBoxLayout()
                rate_layout.addWidget(self.rate_input)
                rate_layout.addWidget(self.rate_button)
                self.rating_review_section.layout().insertLayout(0, QLabel("Rate this movie (0-5):"))
                self.rating_review_section.layout().insertLayout(1, rate_layout)

            # --- Review Input ---
            if self.review_input is None: # Create only once
                self.review_input = QTextEdit()
                self.review_input.setMaximumHeight(80)
                self.review_input.setPlaceholderText("Write your review here...")
                self.review_submit_button = QPushButton("Submit Review")
                self.review_submit_button.clicked.connect(self.submit_review)

                review_layout = QVBoxLayout()
                review_layout.addWidget(self.review_input)
                review_layout.addWidget(self.review_submit_button)
                self.rating_review_section.layout().insertLayout(2, QLabel("Write a review:"))
                self.rating_review_section.layout().insertLayout(3, review_layout)

            # Load and display existing reviews (placeholder for now)
            # This would require a service call to fetch reviews for this specific movie
            # self.load_movie_reviews() # Implement this function later
            self.reviews_display.setPlainText("Reviews for this movie will appear here once the review service is implemented.")


    def submit_rating(self):
        """Handles the submission of a new rating."""
        if not self.session_manager.is_logged_in():
            QMessageBox.warning(self, 'Not Logged In', 'You must be logged in to rate a movie.')
            return

        try:
            rating_str = self.rate_input.toPlainText().strip()
            rating = float(rating_str)
            if not (0 <= rating <= 5):
                raise ValueError("Rating must be between 0 and 5.")
        except ValueError as e:
            QMessageBox.critical(self, 'Invalid Rating', f'Please enter a valid number between 0 and 5. Error: {e}')
            return

        # Call the rating service to submit the rating
        # Example: result = self.rating_service.submit_rating(self.session_manager.get_current_user_id(), self.tmdb_id, rating)
        # if result["success"]:
        #     QMessageBox.information(self, 'Rating Submitted', result["message"])
        #     # Optionally, reload movie details to show updated average
        #     # self.load_movie_details()
        # else:
        #     QMessageBox.critical(self, 'Rating Failed', result["message"])
        # For now, just show a message
        QMessageBox.information(self, 'Rating Submitted (Simulated)', f'Rating {rating}/5 submitted for {self.movie_data["title"]}. (Service not implemented yet)')


    def submit_review(self):
        """Handles the submission of a new review."""
        if not self.session_manager.is_logged_in():
            QMessageBox.warning(self, 'Not Logged In', 'You must be logged in to review a movie.')
            return

        review_text = self.review_input.toPlainText().strip()
        if not review_text:
            QMessageBox.warning(self, 'Empty Review', 'Review text cannot be empty.')
            return

        # Call the review service to submit the review
        # Example: result = self.review_service.submit_review(self.session_manager.get_current_user_id(), self.tmdb_id, review_text)
        # if result["success"]:
        #     QMessageBox.information(self, 'Review Submitted', result["message"])
        #     # Optionally, clear the input and reload reviews display
        #     self.review_input.clear()
        #     # self.load_movie_reviews() # Implement this function later
        # else:
        #     QMessageBox.critical(self, 'Review Failed', result["message"])
        # For now, just show a message
        QMessageBox.information(self, 'Review Submitted (Simulated)', f'Review submitted for {self.movie_data["title"]}. (Service not implemented yet)')


# Example of standalone run (usually called from gui_home.py)
# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     # Simulate a logged-in session for testing
#     from gui.session_manager import SessionManager
#     session = SessionManager()
#     session.login(1, "test@example.com", "user")
#     detail_window = MovieDetailWindow(tmdb_id=123) # Example TMDB ID
#     detail_window.show()
#     sys.exit(app.exec_())