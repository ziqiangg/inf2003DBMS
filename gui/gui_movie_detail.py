# gui/gui_movie_detail.py
import sys
import traceback
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QFormLayout, QScrollArea, QFrame, QMessageBox, QGridLayout, QSpacerItem
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from gui.session_manager import SessionManager
from gui.gui_signals import global_signals #for global signal to refresh other pages
from database.services.movie_service import MovieService
from database.services.rating_service import RatingService
from database.services.review_service import ReviewService
from database.services.genre_service import GenreService
from database.services.cast_crew_service import CastCrewService

from gui.utils import is_placeholder_url, DEFAULT_POSTER_PATH, load_default_poster

class MovieDetailWindow(QWidget):
    def __init__(self, tmdb_id):
        try:
            super().__init__()
            self.tmdb_id = tmdb_id
            self.session_manager = SessionManager()
            self.movie_service = MovieService()
            self.rating_service = RatingService()
            self.review_service = ReviewService()
            self.genre_service = GenreService()
            self.cast_crew_service = CastCrewService()

            self.network_manager = QNetworkAccessManager()
            self.reply_references = {}  # Keep track of network replies

            self.setWindowTitle('Movie Details')
            self.setGeometry(150, 150, 1000, 800)
            
        except Exception as e:
            print(f"Error in MovieDetailWindow initialization: {str(e)}")
            traceback.print_exc()
            raise

        #print("DEBUG: About to call self.init_ui()")
        self.init_ui()
        # print("DEBUG: Finished calling self.init_ui()")
        # print("DEBUG: About to call self.load_movie_details()")
        self.load_movie_details()
        # print("DEBUG: Finished calling self.load_movie_details() - __init__ ending")

    # Debug showEvent
    def showEvent(self, event):
        # print("DEBUG: MovieDetailWindow.showEvent called - Window is being shown.")
        super().showEvent(event)

    def closeEvent(self, event):
        try:
            print("DEBUG: MovieDetailWindow.closeEvent called - Window is about to close.")
            
            # Disconnect from global signals
            try:
                global_signals.movie_data_updated.disconnect(self.on_movie_data_updated)
            except:
                pass  # Signal might not be connected
            
            # Clean up network replies
            for reply in self.reply_references.values():
                if reply and not reply.isFinished():
                    reply.abort()
            self.reply_references.clear()
            
            # Accept the close event
            event.accept()
            
        except Exception as e:
            print(f"Error during MovieDetailWindow cleanup: {str(e)}")
            traceback.print_exc()
            event.accept()

    def init_ui(self):
        # print("DEBUG: MovieDetailWindow.init_ui() called")
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

        # --- Rating Button Input (0.0 to 5.0 in 0.5 steps) ---
        self.rating_input_label = QLabel("Your Rating (0.0 to 5.0):")
        self.rating_input_layout = QHBoxLayout()
        self.rating_buttons = []
        # Create buttons for 0.0, 0.5, 1.0, ..., 5.0 (11 buttons)
        for i in range(11): # 0 to 10 inclusive -> 11 steps
            rating_val = i * 0.5
            btn_text = f"{rating_val:.1f}"
            btn = QPushButton(btn_text)
            btn.setCheckable(True) # Allow selection/deselection
            # Connect the button click to a lambda that captures the rating value
            btn.clicked.connect(lambda checked, val=rating_val: self.select_rating(val, checked))
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
        # print("DEBUG: MovieDetailWindow.init_ui() finished")

    def select_rating(self, value, checked):
        """Handles rating button selection/deselection."""
        # print(f"DEBUG: select_rating called with value={value}, checked={checked}")
        # If the button was unchecked, and it was the currently selected one, clear the selection
        if not checked and hasattr(self, '_current_selected_rating') and self._current_selected_rating == value:
            self._current_selected_rating = None
            self.selected_rating = None # Store None if deselected
            # print(f"DEBUG: Rating deselected, stored: {self.selected_rating}")
            return

        # If the button was checked, update the selection
        if checked:
            # Deselect other buttons
            for btn in self.rating_buttons:
                if btn.text() != f"{value:.1f}":
                    btn.setChecked(False)
            # Store the selected rating value
            self._current_selected_rating = value # Keep track internally
            self.selected_rating = value
            # print(f"DEBUG: Rating selected, stored: {self.selected_rating}")


    def load_movie_details(self):
        # print(f"DEBUG: MovieDetailWindow.load_movie_details() called for tmdb_id: {self.tmdb_id}")
        # Fetch main movie info
        movie_detail = self.movie_service.get_movie_detail(self.tmdb_id)
        if not movie_detail:
            # print(f"DEBUG: MovieDetailWindow.load_movie_details(): Movie detail not found for ID {self.tmdb_id}. Showing error and closing.")
            QMessageBox.critical(self, 'Error', f'Could not load details for movie ID {self.tmdb_id}.')
            self.close() # Close the window if movie not found
            return

        print(f"DEBUG: MovieDetailWindow.load_movie_details(): Retrieved movie detail: {movie_detail.get('title')}")

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
        # print(f"DEBUG: MovieDetailWindow.load_movie_details(): Poster URL is '{poster_url}'")
        if is_placeholder_url(poster_url):
            # print("DEBUG: MovieDetailWindow.load_movie_details(): Poster URL is a placeholder.")
            pixmap = QPixmap(DEFAULT_POSTER_PATH)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(300, 450, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.poster_label.setPixmap(scaled_pixmap)
            else:
                self.poster_label.setText("No Poster")
        else:
            # print("DEBUG: MovieDetailWindow.load_movie_details(): Attempting to load poster from URL.")
            request = QNetworkRequest(QUrl(poster_url))
            request.setTransferTimeout(5000)
            reply = self.network_manager.get(request)
            reply.finished.connect(
                lambda: self.on_poster_load_finished(reply, self.poster_label, movie_detail.get('title', 'Unknown'))
            )

        runtime = movie_detail.get('runtime')
        self.runtime_label.setText(f"Runtime: {runtime} minutes" if runtime else "Runtime: Unknown")

        sum_ratings = movie_detail.get('totalRatings', 0) # Get the SUM
        count_rating = movie_detail.get('countRatings', 0) # Get the COUNT

        # Calculate the average
        avg_rating = 0.0
        if count_rating > 0:
            avg_rating = sum_ratings / count_rating

        # Display the CALCULATED average
        self.avg_rating_label.setText(f"Average Rating: {avg_rating:.1f}/5 ({count_rating} ratings)")

        release_date = movie_detail.get('releaseDate')
        self.release_date_label.setText(f"Release Date: {release_date}" if release_date else "Release Date: Unknown")

        self.overview_text.setPlainText(movie_detail.get('overview', 'No overview available.'))

        # --- Fetch and Populate Genres, Cast, Crew ---
        # print("DEBUG: MovieDetailWindow.load_movie_details(): Fetching genres...")
        genres = self.genre_service.get_genres_for_movie(self.tmdb_id)
        # print(f"DEBUG: MovieDetailWindow.load_movie_details(): Retrieved {len(genres)} genres.")
        genre_names = [g['genreName'] for g in genres]
        self.genres_text.setPlainText(", ".join(genre_names) if genre_names else "No genres listed.")

        # print("DEBUG: MovieDetailWindow.load_movie_details(): Fetching director...")
        director_info = self.cast_crew_service.get_director_for_movie(self.tmdb_id)
        # print(f"DEBUG: MovieDetailWindow.load_movie_details(): Retrieved director info: {director_info}")
        self.director_text.setText(director_info['name'] if director_info else "Director information not available.")

        # print("DEBUG: MovieDetailWindow.load_movie_details(): Fetching cast...")
        cast_list = self.cast_crew_service.get_formatted_cast_list(self.tmdb_id)
        # print(f"DEBUG: MovieDetailWindow.load_movie_details(): Retrieved {len(cast_list)} cast members.")
        self.cast_text.setPlainText(", ".join(cast_list) if cast_list else "Cast information not available.")

        # --- Fetch and Populate Reviews ---
        # print("DEBUG: MovieDetailWindow.load_movie_details(): Loading reviews...")
        self.load_reviews()
        # print("DEBUG: MovieDetailWindow.load_movie_details(): Finished loading reviews.")

        # --- Check for Existing User Rating/Review (if logged in) ---
        # print("DEBUG: MovieDetailWindow.load_movie_details(): Checking for existing user rating/review...")
        if self.session_manager.is_logged_in():
            user_id = self.session_manager.get_current_user_id()
            # print(f"DEBUG: MovieDetailWindow.load_movie_details(): User is logged in (ID: {user_id}). Fetching existing rating/review.")
            existing_rating = self.rating_service.get_user_rating_for_movie(user_id, self.tmdb_id)
            existing_review = self.review_service.get_user_review_for_movie(user_id, self.tmdb_id)

            if existing_rating:
                rating_val = float(existing_rating['rating'])
                # print(f"DEBUG: MovieDetailWindow.load_movie_details(): Found existing rating: {rating_val}")
                # Find the corresponding button and click it to select it
                for btn in self.rating_buttons:
                    if btn.text() == f"{rating_val:.1f}":
                        btn.setChecked(True)
                        # Manually call the handler to set the initial state correctly
                        self.select_rating(rating_val, True) # Pass True as checked
                        break # Exit loop after finding and clicking the button


            if existing_review:
                # print(f"DEBUG: MovieDetailWindow.load_movie_details(): Found existing review: {existing_review['review'][:50]}...") # Print first 50 chars
                self.review_text_input.setPlainText(existing_review['review']) # Pre-fill the review text
        #else:
            #print("DEBUG: MovieDetailWindow.load_movie_details(): User is not logged in, skipping rating/review check.")
        # print("DEBUG: MovieDetailWindow.load_movie_details(): Finished.")

    def load_reviews(self):
        # print("DEBUG: MovieDetailWindow.load_reviews() called")
        """Fetches and displays the 3 most recent reviews."""
        # Clear existing review widgets
        while self.reviews_container.count():
            child = self.reviews_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        reviews = self.review_service.get_reviews_for_movie(self.tmdb_id)
        # print(f"DEBUG: MovieDetailWindow.load_reviews(): Retrieved {len(reviews)} reviews from service.")

        if not reviews:
            no_reviews_label = QLabel("No reviews yet.")
            self.reviews_container.addWidget(no_reviews_label)
        else:
            for i, review in enumerate(reviews):
                # print(f"DEBUG: MovieDetailWindow.load_reviews(): Processing review {i+1}")
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
        # print("DEBUG: MovieDetailWindow.load_reviews(): Finished.")

    def on_poster_load_finished(self, reply, poster_label, movie_title):
        """Callback for loading the movie poster."""
        # print(f"DEBUG: MovieDetailWindow.on_poster_load_finished() called for '{movie_title}'")
        if reply.error() == QNetworkReply.NoError:
            image_data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(300, 450, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                poster_label.setPixmap(scaled_pixmap)
            else:
                # print(f"DEBUG: MovieDetailWindow.on_poster_load_finished(): Could not load image data for movie '{movie_title}' from {reply.url().toString()}")
                # --- Use helper from utils ---
                load_default_poster(poster_label, size=(300, 450))
                
        else:
            # print(f"DEBUG: MovieDetailWindow.on_poster_load_finished(): Failed to load poster for '{movie_title}' from {reply.url().toString()}: {reply.errorString()}")
            # --- Use helper from utils ---
            load_default_poster(poster_label, size=(300, 450))
        reply.deleteLater()
        # print(f"DEBUG: MovieDetailWindow.on_poster_load_finished(): Finished for '{movie_title}'")

    # Note: This helper is redundant now as load_default_poster from utils.py is used
    # def load_default_poster(self, poster_label):
    #     """Helper to load the default poster."""
    #     pixmap = QPixmap(DEFAULT_POSTER_PATH)
    #     if not pixmap.isNull():
    #         scaled_pixmap = pixmap.scaled(300, 450, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    #         poster_label.setPixmap(scaled_pixmap)
    #     else:
    #         poster_label.setText("No Poster")

    def submit_rating_review(self):
        # print("DEBUG: MovieDetailWindow.submit_rating_review() called")
        if not self.session_manager.is_logged_in():
            # print("DEBUG: MovieDetailWindow.submit_rating_review(): User not logged in.")
            QMessageBox.warning(self, 'Not Logged In', 'You must be logged in to rate or review a movie.')
            return

        user_id = self.session_manager.get_current_user_id()
        # Get the rating value from the slider via the stored attribute
        # Ensure selected_rating exists as an attribute before accessing it
        rating_value = getattr(self, 'selected_rating', None)
        # print(f"DEBUG: MovieDetailWindow.submit_rating_review(): Retrieved rating_value: {rating_value}")
        review_text = self.review_text_input.toPlainText().strip()
        # print(f"DEBUG: MovieDetailWindow.submit_rating_review(): Retrieved review_text: {review_text}")

        # At least one action (rating or review) must be provided
        if rating_value is None and not review_text:
            # print("DEBUG: MovieDetailWindow.submit_rating_review(): No rating or review provided.")
            QMessageBox.warning(self, 'No Input', 'Please provide a rating or a review.')
            return

        success = True
        message_parts = []

        # Submit Rating if selected
        if rating_value is not None:
            # print(f"DEBUG: MovieDetailWindow.submit_rating_review(): Attempting to submit rating: {rating_value}")
            # Pass the float rating_value directly
            rating_result = self.rating_service.add_rating(user_id, self.tmdb_id, rating_value)
            # print(f"DEBUG: MovieDetailWindow.submit_rating_review(): Rating service result: {rating_result}")

            if rating_result['success']:
                message_parts.append("Rating submitted successfully.")
                print(f"DEBUG: MovieDetailWindow.submit_rating_review: Emitting movie_data_updated signal for tmdbID {self.tmdb_id}")
                # Emit signal indicating movie data changed
                global_signals.movie_data_updated.emit(self.tmdb_id)
            else:
                success = False
                message_parts.append(rating_result['message'])

        # Submit Review if provided
        if review_text:
            # print(f"DEBUG: MovieDetailWindow.submit_rating_review(): Attempting to submit review: {review_text[:50]}...") # Print first 50 chars
            review_result = self.review_service.add_review(user_id, self.tmdb_id, review_text)
            # print(f"DEBUG: MovieDetailWindow.submit_rating_review(): Review service result: {review_result}")

            if review_result['success']:
                message_parts.append("Review submitted successfully.")
                # Emit signal indicating movie data changed (even if only review changed)
                print(f"DEBUG: MovieDetailWindow.submit_rating_review: Emitting movie_data_updated signal for tmdbID {self.tmdb_id} (Review)")
                global_signals.movie_data_updated.emit(self.tmdb_id)
            else:
                success = False
                message_parts.append(review_result['message'])

        if success:
            # print("DEBUG: MovieDetailWindow.submit_rating_review(): All submissions successful.")
            QMessageBox.information(self, 'Success', " ".join(message_parts))
            # Reload movie details to show updated average rating and review count
            self.load_movie_details()
            # Clear the input fields after successful submission
            if rating_value is not None:
                # Deselect all rating buttons
                for btn in self.rating_buttons:
                    btn.setChecked(False)
                # Reset internal tracking
                self._current_selected_rating = None
                self.selected_rating = None
            if review_text:
                self.review_text_input.clear()
        else:
            # print("DEBUG: MovieDetailWindow.submit_rating_review(): Some submissions failed.")
            QMessageBox.critical(self, 'Error', " ".join(message_parts))
        # print("DEBUG: MovieDetailWindow.submit_rating_review(): Finished.")

# Example for standalone testing (usually called from gui_home.py)
# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     # Simulate login for testing rating/review functionality
#     session = SessionManager()
#     session.login(1, "test@example.com", "user")
#     detail_window = MovieDetailWindow(862) # Example TMDB ID
#     detail_window.show()
#     sys.exit(app.exec_())
