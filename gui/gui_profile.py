# gui/gui_profile.py (Adding showEvent and closeEvent handlers)
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QFormLayout, QScrollArea, QFrame, QMessageBox, QGridLayout, QSpacerItem,
    QListWidget, QListWidgetItem, QLineEdit, QSizePolicy
)
from PyQt5.QtCore import Qt
# No need to import get_mysql_connection or close_connection directly in the GUI anymore
from gui.session_manager import SessionManager
from gui.gui_signals import global_signals
from database.services.movie_service import MovieService
from database.services.rating_service import RatingService # Updated to use the new combined method
# from database.services.review_service import ReviewService #fetching list of review+rating from RatingService
from database.services.user_service import UserService # Needed for admin search
from gui.gui_movie_detail import MovieDetailWindow

class ProfileWindow(QWidget):
    def __init__(self, session_manager):
        super().__init__()
        self.session_manager = session_manager
        self.movie_service = MovieService()
        self.rating_service = RatingService() # Updated to use the new combined method
        self.user_service = UserService() # For admin user search - Now properly used

        self.current_user_id = self.session_manager.get_current_user_id()
        self.current_user_email = self.session_manager.get_current_user_email()
        self.current_user_role = self.session_manager.get_current_user_role()

        self.selected_user_id = self.current_user_id # For admin view, defaults to current user's profile
        self.selected_user_email = self.current_user_email

        self.setWindowTitle('Profile')
        self.setGeometry(200, 200, 800, 600)

        self.init_ui()
        # Connect to the global signal to reload data when a movie's rating/review changes
        global_signals.movie_data_updated.connect(self.on_movie_data_updated)
        self.load_profile_data()

    def on_movie_data_updated(self, tmdb_id):
        """Reloads the profile data if the updated movie is relevant to the currently viewed profile."""
        print(f"DEBUG: ProfileWindow.on_movie_data_updated: Received signal for tmdbID {tmdb_id}. Reloading data for selected user ID {self.selected_user_id}.")
        # Note: This reloads the *entire* profile list for the *selected* user.
        # A more granular update (e.g., only refreshing the item for tmdb_id if it exists)
        # is possible but more complex. Reloading the full list is simpler and ensures consistency.
        print(f"DEBUG: ProfileWindow.on_movie_data_updated: Received signal for tmdbID {tmdb_id}. Reloading data for selected user ID {self.selected_user_id}.")
        self.load_profile_data()

    # Debug showEvent
    def showEvent(self, event):
        print("DEBUG: ProfileWindow.showEvent called - Window is being shown, reloading data.")
        # Reload data every time the window is shown to reflect potential changes
        # from the MovieDetailWindow
        self.load_profile_data()
        super().showEvent(event) # Call the parent class's showEvent

    # Debug closeEvent
    def closeEvent(self, event):
        print("DEBUG: ProfileWindow.closeEvent called - Window is about to close.")
        # Disconnect the signal when the window closes to prevent potential errors
        # if the signal is emitted after this window is destroyed
        try:
            global_signals.movie_data_updated.disconnect(self.on_movie_data_updated)
            print("DEBUG: ProfileWindow.closeEvent: Disconnected movie_data_updated signal.")
        except TypeError:
            # This exception is raised if the signal was not connected or already disconnected
            print("DEBUG: ProfileWindow.closeEvent: Signal was already disconnected or not connected.")
        event.accept()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # --- User Info Section ---
        info_frame = QFrame()
        info_layout = QFormLayout(info_frame)
        self.role_label = QLabel(f"Role: {self.current_user_role}")
        info_layout.addRow("Email:", QLabel(self.current_user_email))
        info_layout.addRow("Current Session Role:", self.role_label)

        main_layout.addWidget(info_frame)

        # --- Conditional UI based on Role ---
        if self.current_user_role == 'admin':
            self.setup_admin_ui(main_layout)
        else: # User or any other role treated as 'user'
            self.setup_user_ui(main_layout)

        # --- Back Button ---
        back_button_layout = QHBoxLayout()
        back_button_layout.addStretch()
        back_button = QPushButton("Back to Home")
        back_button.clicked.connect(self.close)
        back_button_layout.addWidget(back_button)
        main_layout.addLayout(back_button_layout)

        self.setLayout(main_layout)

    def setup_admin_ui(self, main_layout):
        """Sets up the UI elements specific to the admin profile view."""
        # --- Search Section ---
        search_frame = QFrame()
        search_layout = QHBoxLayout(search_frame)
        self.search_email_input = QLineEdit()
        self.search_email_input.setPlaceholderText("Enter user email to view their profile...")
        search_button = QPushButton("Search User")
        search_button.clicked.connect(self.search_user_by_email)
        search_layout.addWidget(QLabel("Search User Email:"))
        search_layout.addWidget(self.search_email_input)
        search_layout.addWidget(search_button)
        main_layout.addWidget(search_frame)

        # --- Display Selected User Info ---
        self.selected_user_info_frame = QFrame()
        selected_info_layout = QFormLayout(self.selected_user_info_frame)
        self.selected_user_email_label = QLabel(self.selected_user_email)
        self.selected_user_id_label = QLabel(str(self.selected_user_id))
        selected_info_layout.addRow("Viewing Profile For Email:", self.selected_user_email_label)
        selected_info_layout.addRow("User ID:", self.selected_user_id_label)
        main_layout.addWidget(self.selected_user_info_frame)

        # --- Rated Movies List ---
        rated_movies_frame = QFrame()
        rated_movies_layout = QVBoxLayout(rated_movies_frame)
        rated_movies_label = QLabel("Movies Rated/Reviewed by Selected User (Sorted by Rating Desc, then Review Time Desc):")
        rated_movies_label.setStyleSheet("font-weight: bold;")
        self.rated_movies_list = QListWidget()
        rated_movies_layout.addWidget(rated_movies_label)
        rated_movies_layout.addWidget(self.rated_movies_list)
        main_layout.addWidget(rated_movies_frame)

        # Connect list item click to open movie detail
        self.rated_movies_list.itemClicked.connect(self.open_movie_detail_from_list)

    def setup_user_ui(self, main_layout):
        """Sets up the UI elements specific to the standard user profile view."""
        # --- Rated Movies List ---
        rated_movies_frame = QFrame()
        rated_movies_layout = QVBoxLayout(rated_movies_frame)
        rated_movies_label = QLabel("Your Rated/Reviewed Movies (Sorted by Rating Desc, then Review Time Desc):")
        rated_movies_label.setStyleSheet("font-weight: bold;")
        self.rated_movies_list = QListWidget()
        rated_movies_layout.addWidget(rated_movies_label)
        rated_movies_layout.addWidget(self.rated_movies_list)
        main_layout.addWidget(rated_movies_frame)

        # Connect list item click to open movie detail
        self.rated_movies_list.itemClicked.connect(self.open_movie_detail_from_list)

    def search_user_by_email(self):
        """Handles the admin search for a user by email using UserService."""
        email_to_search = self.search_email_input.text().strip()
        if not email_to_search:
            QMessageBox.warning(self, 'Search Error', 'Please enter an email address to search.')
            return

        # Use UserService to find the user by email via its repository
        searched_user_data = self.user_service.user_repo.get_user_by_email(email_to_search)

        if searched_user_data:
            # Assuming the repository returns a dictionary like {'userID': ..., 'email': ..., 'role': ...}
            self.selected_user_id = searched_user_data['userID']
            self.selected_user_email = searched_user_data['email']
            # Update the display
            self.selected_user_email_label.setText(self.selected_user_email)
            self.selected_user_id_label.setText(str(self.selected_user_id))
            # Reload the list for the searched user
            self.load_profile_data()
        else:
            QMessageBox.information(self, 'User Not Found', f'No user found with email: {email_to_search}')


    def load_profile_data(self):
        """Loads the rated/reviewed movies for the currently selected user (self.selected_user_id)."""
        if not self.selected_user_id:
            print(f"DEBUG: ProfileWindow.load_profile_data: selected_user_id is None or 0.")
            return

        print(f"DEBUG: ProfileWindow.load_profile_data: Loading data for userID {self.selected_user_id}")

        user_interactions = self.rating_service.get_user_ratings_and_reviews_for_profile(self.selected_user_id)
        print(f"DEBUG: ProfileWindow.load_profile_data: Retrieved {len(user_interactions)} interactions (ratings/reviews) via service.")
        # Print the first few interactions for debugging
        for i, interaction in enumerate(user_interactions[:2]): # Print first 2
            print(f"DEBUG: ProfileWindow.load_profile_data: Interaction {i+1}: {interaction}")

        # Clear the existing list
        print("DEBUG: ProfileWindow.load_profile_data: Clearing existing list.")
        self.rated_movies_list.clear()

        # Populate the list widget
        print("DEBUG: ProfileWindow.load_profile_data: Starting to populate list widget.")
        for i, interaction in enumerate(user_interactions):
            print(f"DEBUG: ProfileWindow.load_profile_data: Processing interaction {i+1}: {interaction}") # Debug print for each item
            try:
                tmdb_id = interaction['tmdbID']
                movie_title = interaction['title']
                rating_value = interaction['rating']
                review_text = interaction['review']
                timestamp = interaction.get('timeStamp', 'N/A')

                # Determine display text based on whether it's a rating or a review
                if rating_value is not None:
                    # This entry represents a rating
                    item_text = f"{movie_title} - Rating: {rating_value}/5 (Time: {timestamp})"
                    if review_text: # If there was also a review fetched in this row (possible if logic changes)
                         item_text += f"\nReview: {review_text}"
                else:
                    # This entry represents a review for an unrated movie
                    # Use the review timestamp for display
                    item_text = f"{movie_title} - Review (No Rating) (Time: {timestamp})\nReview: {review_text if review_text else 'No Review Text'}"

                print(f"DEBUG: ProfileWindow.load_profile_data: Item text for tmdbID {tmdb_id}: {item_text[:50]}...") # Print first 50 chars of text

                # Create the QListWidgetItem
                item = QListWidgetItem(item_text)
                # Store the tmdb_id as user data within the item for easy retrieval on click
                item.setData(Qt.UserRole, tmdb_id)

                # Add the item to the list
                self.rated_movies_list.addItem(item)
                print(f"DEBUG: ProfileWindow.load_profile_data: Added item for tmdbID {tmdb_id} to list.")

            except KeyError as e:
                print(f"ERROR: ProfileWindow.load_profile_data: Missing key in interaction data: {e}. Interaction: {interaction}")
                continue # Skip to the next interaction
            except Exception as e:
                print(f"ERROR: ProfileWindow.load_profile_data: Unexpected error processing interaction {i+1}: {e}. Interaction: {interaction}")
                import traceback
                traceback.print_exc() # Print the full traceback for detailed debugging
                continue

        print("DEBUG: ProfileWindow.load_profile_data: Finished populating list widget.")

    def open_movie_detail_from_list(self, item):
        """Opens the MovieDetailWindow for the movie associated with the clicked list item."""
        tmdb_id = item.data(Qt.UserRole) # Retrieve the stored tmdb_id
        if tmdb_id:
            print(f"DEBUG: ProfileWindow.open_movie_detail_from_list: Opening detail for tmdbID {tmdb_id}")
            detail_window = MovieDetailWindow(tmdb_id)
            detail_window.show()
        else:
            print("DEBUG: ProfileWindow.open_movie_detail_from_list: No tmdbID found in item data.")

# Example for standalone testing (usually called from gui_home.py)
# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     # Simulate a logged-in session for testing
#     session = SessionManager()
#     session.login(1, "test@example.com", "user") # or "admin"
#     profile_window = ProfileWindow(session_manager=session)
#     profile_window.show()
#     sys.exit(app.exec_())