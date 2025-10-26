# gui/movie_detail.py
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QFormLayout, QScrollArea, QFrame, QMessageBox, QGridLayout, QSpacerItem
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from gui.session_manager import SessionManager
from database.services.movie_service import MovieService
from database.services.rating_service import RatingService
from database.services.review_service import ReviewService
from database.services.genre_service import GenreService
from database.services.cast_crew_service import CastCrewService

from gui.utils import is_placeholder_url, DEFAULT_POSTER_PATH, load_default_poster

class MovieDetailWindow(QWidget):
    def __init__(self, tmdb_id):
        super().__init__()
        self.tmdb_id = tmdb_id
        self.session_manager = SessionManager()
        self.movie_service = MovieService()
        self.rating_service = RatingService()
        self.review_service = ReviewService()
        self.genre_service = GenreService()
        self.cast_crew_service = CastCrewService()

        self.network_manager = QNetworkAccessManager()

        self.setWindowTitle('Movie Details')
        self.setGeometry(150, 150, 1000, 800)

        self.init_ui()
        self.load_movie_details()

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)

        # --- Movie Info Section ---
        self.movie_info_frame = QFrame()
        self.movie_info_layout = QVBoxLayout(self.movie_info_frame)

        # Top row: Poster and Title/Link
        top_row_layout = QHBoxLayout()
        self.poster_label = QLabel()
        self.poster_label.setFixedSize(300, 450) # Larger size for detail page
        self.poster_label.setAlignment(Qt.AlignCenter)
        self.poster_label.setStyleSheet("border: 1px solid gray;")
        top_row_layout.addWidget(self.poster_label)

        title_link_layout = QVBoxLayout()
        self.title_label = QLabel("Loading...")
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        title_link_layout.addWidget(self.title_label)

        self.link_label = QLabel("Loading...")
        self.link_label.setOpenExternalLinks(True) # Make links clickable
        self.link_label.setTextFormat(Qt.RichText)
        title_link_layout.addWidget(self.link_label)

        top_row_layout.addLayout(title_link_layout)
        top_row_layout.addStretch()
        self.movie_info_layout.addLayout(top_row_layout)

        # Middle row: Runtime, Rating, Release Date
        info_row_layout = QHBoxLayout()
        self.runtime_label = QLabel("Runtime: Loading...")
        self.avg_rating_label = QLabel("Average Rating: Loading...")
        self.release_date_label = QLabel("Release Date: Loading...")

        info_row_layout.addWidget(self.runtime_label)
        info_row_layout.addWidget(self.avg_rating_label)
        info_row_layout.addWidget(self.release_date_label)
        info_row_layout.addStretch()
        self.movie_info_layout.addLayout(info_row_layout)

        # Overview
        self.overview_label = QLabel("Overview:")
        self.overview_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        self.overview_text = QTextEdit()
        self.overview_text.setReadOnly(True)
        self.overview_text.setMaximumHeight(120)
        self.movie_info_layout.addWidget(self.overview_label)
        self.movie_info_layout.addWidget(self.overview_text)

        # --- Genres, Cast, Crew Section ---
        self.metadata_frame = QFrame()
        self.metadata_layout = QFormLayout(self.metadata_frame)

        self.genres_label = QLabel("Genres:")
        self.genres_text = QTextEdit()
        self.genres_text.setReadOnly(True)
        self.genres_text.setMaximumHeight(60)
        self.metadata_layout.addRow(self.genres_label, self.genres_text)

        self.director_label = QLabel("Director:")
        self.director_text = QLabel("Loading...")
        self.metadata_layout.addRow(self.director_label, self.director_text)

        self.cast_label = QLabel("Cast:")
        self.cast_text = QTextEdit()
        self.cast_text.setReadOnly(True)
        self.cast_text.setMaximumHeight(100)
        self.metadata_layout.addRow(self.cast_label, self.cast_text)

        self.scroll_layout.addWidget(self.movie_info_frame)
        self.scroll_layout.addWidget(self.metadata_frame)

        # --- Reviews Section ---
        self.reviews_frame = QFrame()
        self.reviews_layout = QVBoxLayout(self.reviews_frame)
        self.reviews_label = QLabel("Recent Reviews:")
        self.reviews_label.setStyleSheet("font-weight: bold; font-size: 16px; margin-top: 10px;")
        self.reviews_layout.addWidget(self.reviews_label)

        self.reviews_container = QVBoxLayout()
        self.reviews_layout.addLayout(self.reviews_container)

        self.scroll_layout.addWidget(self.reviews_frame)

        # --- Rating/Review Input Section (Visible only if logged in) ---
        self.input_frame = QFrame()
        self.input_layout = QVBoxLayout(self.input_frame)

        self.rating_input_label = QLabel("Your Rating (0-5):")
        self.rating_input_layout = QHBoxLayout()
        self.rating_buttons = []
        for i in range(6): # Buttons for 0 to 5
            btn = QPushButton(str(i))
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, val=i: self.select_rating(val))
            self.rating_buttons.append(btn)
            self.rating_input_layout.addWidget(btn)

        self.input_layout.addWidget(self.rating_input_label)
        self.input_layout.addLayout(self.rating_input_layout)

        self.review_input_label = QLabel("Your Review:")
        self.review_text_input = QTextEdit()
        self.review_text_input.setMaximumHeight(100)
        self.input_layout.addWidget(self.review_input_label)
        self.input_layout.addWidget(self.review_text_input)

        self.submit_button = QPushButton("Submit Rating/Review")
        self.submit_button.clicked.connect(self.submit_rating_review)
        self.input_layout.addWidget(self.submit_button)

        # Initially hide the input frame if not logged in
        if not self.session_manager.is_logged_in():
            self.input_frame.hide()
        self.scroll_layout.addWidget(self.input_frame)

        # --- Back Button ---
        back_button_layout = QHBoxLayout()
        back_button_layout.addStretch()
        back_button = QPushButton("Back to Home")
        back_button.clicked.connect(self.close)
        back_button_layout.addWidget(back_button)
        self.scroll_layout.addLayout(back_button_layout)

        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        main_layout.addWidget(self.scroll_area)
        self.setLayout(main_layout)

    def load_movie_details(self):
        """Fetches and populates all movie details."""
        # Fetch main movie info
        movie_detail = self.movie_service.get_movie_detail(self.tmdb_id)
        if not movie_detail:
            QMessageBox.critical(self, 'Error', f'Could not load details for movie ID {self.tmdb_id}.')
            self.close() # Close the window if movie not found
            return

        # --- Populate Movie Info ---
        self.title_label.setText(movie_detail.get('title', 'Unknown Title'))
        # Note: 'link' field is not present in the provided Movies table schema.
        # Assuming it's stored but maybe empty. If not stored, this will be empty.
        link_url = movie_detail.get('link', '') # Get the link from the movie detail
        if link_url:
            self.link_label.setText(f'<a href="{link_url}">{link_url}</a>')
        else:
            self.link_label.setText("No official website link available.")

        # Load Poster
        poster_url = movie_detail.get('poster')
        if is_placeholder_url(poster_url):
            pixmap = QPixmap(DEFAULT_POSTER_PATH)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(300, 450, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.poster_label.setPixmap(scaled_pixmap)
            else:
                self.poster_label.setText("No Poster")
        else:
            request = QNetworkRequest(QUrl(poster_url))
            request.setTransferTimeout(5000)
            reply = self.network_manager.get(request)
            reply.finished.connect(
                lambda: self.on_poster_load_finished(reply, self.poster_label, movie_detail.get('title', 'Unknown'))
            )

        runtime = movie_detail.get('runtime')
        self.runtime_label.setText(f"Runtime: {runtime} minutes" if runtime else "Runtime: Unknown")

        avg_rating = movie_detail.get('totalRatings', 0)
        count_rating = movie_detail.get('countRatings', 0)
        self.avg_rating_label.setText(f"Average Rating: {avg_rating:.1f}/5 ({count_rating} ratings)")

        release_date = movie_detail.get('releaseDate')
        self.release_date_label.setText(f"Release Date: {release_date}" if release_date else "Release Date: Unknown")

        self.overview_text.setPlainText(movie_detail.get('overview', 'No overview available.'))

        # --- Fetch and Populate Genres, Cast, Crew ---
        genres = self.genre_service.get_genres_for_movie(self.tmdb_id)
        genre_names = [g['genreName'] for g in genres]
        self.genres_text.setPlainText(", ".join(genre_names) if genre_names else "No genres listed.")

        director_info = self.cast_crew_service.get_director_for_movie(self.tmdb_id)
        self.director_text.setText(director_info['name'] if director_info else "Director information not available.")

        cast_list = self.cast_crew_service.get_formatted_cast_list(self.tmdb_id)
        self.cast_text.setPlainText(", ".join(cast_list) if cast_list else "Cast information not available.")

        # --- Fetch and Populate Reviews ---
        self.load_reviews()

        # --- Check for Existing User Rating/Review (if logged in) ---
        if self.session_manager.is_logged_in():
            user_id = self.session_manager.get_current_user_id()
            existing_rating = self.rating_service.get_user_rating_for_movie(user_id, self.tmdb_id)
            existing_review = self.review_service.get_user_review_for_movie(user_id, self.tmdb_id)

            if existing_rating:
                rating_val = float(existing_rating['rating'])
                self.select_rating(rating_val, set_initial=True) # Pre-select the rating

            if existing_review:
                self.review_text_input.setPlainText(existing_review['review']) # Pre-fill the review text

    def load_reviews(self):
        """Fetches and displays the 3 most recent reviews."""
        # Clear existing review widgets
        while self.reviews_container.count():
            child = self.reviews_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        reviews = self.review_service.get_reviews_for_movie(self.tmdb_id)

        if not reviews:
            no_reviews_label = QLabel("No reviews yet.")
            self.reviews_container.addWidget(no_reviews_label)
        else:
            for review in reviews:
                review_widget = QWidget()
                review_layout = QVBoxLayout(review_widget)

                # Reviewer and timestamp
                reviewer_info = QLabel(f"<b>{review['email']}</b> on {review['timeStamp']}")
                reviewer_info.setStyleSheet("font-size: 12px; color: gray;")

                # Review text
                review_text = QTextEdit()
                review_text.setPlainText(review['review'])
                review_text.setReadOnly(True)
                review_text.setMaximumHeight(80) # Limit height per review

                review_layout.addWidget(reviewer_info)
                review_layout.addWidget(review_text)

                self.reviews_container.addWidget(review_widget)

    def on_poster_load_finished(self, reply, poster_label, movie_title):
        """Callback for loading the movie poster."""
        if reply.error() == QNetworkReply.NoError:
            image_data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(300, 450, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                poster_label.setPixmap(scaled_pixmap)
            else:
                print(f"Could not load image data for movie '{movie_title}' from {reply.url().toString()}")
                # --- NEW: Use helper from utils ---
                load_default_poster(poster_label, size=(300, 450))
                # --- END NEW ---
        else:
            print(f"Failed to load poster for '{movie_title}' from {reply.url().toString()}: {reply.errorString()}")
            # --- NEW: Use helper from utils ---
            load_default_poster(poster_label, size=(300, 450))
            # --- END NEW ---
        reply.deleteLater()

    # Note: This helper is redundant now as load_default_poster from utils.py is used
    # def load_default_poster(self, poster_label):
    #     """Helper to load the default poster."""
    #     pixmap = QPixmap(DEFAULT_POSTER_PATH)
    #     if not pixmap.isNull():
    #         scaled_pixmap = pixmap.scaled(300, 450, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    #         poster_label.setPixmap(scaled_pixmap)
    #     else:
    #         poster_label.setText("No Poster")

    def select_rating(self, value, set_initial=False):
        """Handles rating button selection."""
        for i, btn in enumerate(self.rating_buttons):
            btn.setChecked(i == value)
        if not set_initial: # Only store if it's a user click, not initial set
            self.selected_rating = value

    def submit_rating_review(self):
        """Handles submitting the user's rating and/or review."""
        if not self.session_manager.is_logged_in():
            QMessageBox.warning(self, 'Not Logged In', 'You must be logged in to rate or review a movie.')
            return

        user_id = self.session_manager.get_current_user_id()
        rating_value = getattr(self, 'selected_rating', None) # Get the selected rating
        review_text = self.review_text_input.toPlainText().strip()

        # At least one action (rating or review) must be provided
        if rating_value is None and not review_text:
             QMessageBox.warning(self, 'No Input', 'Please provide a rating or a review.')
             return

        success = True
        message_parts = []

        # Submit Rating if selected
        if rating_value is not None:
            rating_result = self.rating_service.add_rating(user_id, self.tmdb_id, rating_value)
            success &= rating_result["success"]
            message_parts.append(f"Rating: {rating_result['message']}")

        # Submit Review if provided
        if review_text:
            review_result = self.review_service.add_review(user_id, self.tmdb_id, review_text)
            success &= review_result["success"]
            message_parts.append(f"Review: {review_result['message']}")

        if success:
            QMessageBox.information(self, 'Success', " ".join(message_parts))
            # Reload movie details to show updated average rating and review count
            self.load_movie_details()
            # Clear the input fields after successful submission
            if rating_value is not None:
                self.select_rating(0) # Deselect rating
            if review_text:
                self.review_text_input.clear()
        else:
            QMessageBox.critical(self, 'Error', " ".join(message_parts))

# Example for standalone testing (usually called from gui_home.py)
# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     # Simulate login for testing rating/review functionality
#     session = SessionManager()
#     session.login(1, "test@example.com", "user")
#     detail_window = MovieDetailWindow(862) # Example TMDB ID
#     detail_window.show()
#     sys.exit(app.exec_())
