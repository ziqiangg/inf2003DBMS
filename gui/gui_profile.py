# gui/gui_profile.py (Adding Delete Account button)
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QFormLayout, QScrollArea, QFrame, QMessageBox, QGridLayout, QSpacerItem,
    QListWidget, QListWidgetItem, QLineEdit, QSizePolicy
)
from PyQt5.QtCore import Qt
from gui.session_manager import SessionManager
from gui.gui_signals import global_signals
from database.services.movie_service import MovieService
from database.services.rating_service import RatingService
from database.services.user_service import UserService
from gui.gui_movie_detail import MovieDetailWindow

class ProfileWindow(QWidget):
    def __init__(self, session_manager):
        super().__init__()
        self.session_manager = session_manager
        self.movie_service = MovieService()
        self.rating_service = RatingService()
        self.user_service = UserService()

        self.current_user_id = self.session_manager.get_current_user_id()
        self.current_user_email = self.session_manager.get_current_user_email()
        self.current_user_role = self.session_manager.get_current_user_role()

        self.selected_user_id = self.current_user_id
        self.selected_user_email = self.current_user_email
        
        # Keep reference to the CRUD window
        self.movie_crud_window = None

        self.setWindowTitle('Profile')
        self.setGeometry(200, 200, 800, 600)

        self.init_ui()
        global_signals.movie_data_updated.connect(self.on_movie_data_updated)
        self.load_profile_data()

    def on_movie_data_updated(self, tmdb_id):
        """Reloads the profile data if the updated movie is relevant to the currently viewed profile."""
        print(f"DEBUG: ProfileWindow.on_movie_data_updated: Received signal for tmdbID {tmdb_id}. Reloading data for selected user ID {self.selected_user_id}.")
        self.load_profile_data()

    def showEvent(self, event):
        print("DEBUG: ProfileWindow.showEvent called - Window is being shown, reloading data.")
        self.load_profile_data()
        super().showEvent(event)

    def closeEvent(self, event):
        print("DEBUG: ProfileWindow.closeEvent called - Window is about to close.")
        try:
            global_signals.movie_data_updated.disconnect(self.on_movie_data_updated)
            print("DEBUG: ProfileWindow.closeEvent: Disconnected movie_data_updated signal.")
        except TypeError:
            print("DEBUG: ProfileWindow.closeEvent: Signal was already disconnected or not connected.")
        event.accept()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # --- User Info Section with Delete Button ---
        info_frame = QFrame()
        info_main_layout = QVBoxLayout(info_frame)
        
        # Create a horizontal layout for email and delete button
        top_row_layout = QHBoxLayout()
        
        # Left side: Email and Role info
        left_info_layout = QFormLayout()
        self.email_label = QLabel(self.current_user_email)
        self.role_label = QLabel(f"Role: {self.current_user_role}")
        left_info_layout.addRow("Email:", self.email_label)
        left_info_layout.addRow("Current Session Role:", self.role_label)
        
        top_row_layout.addLayout(left_info_layout)
        
        # Add stretch to push delete button to the right
        top_row_layout.addStretch()
        
        # Right side: Delete Account button (only for regular users viewing their own profile)
        if self.current_user_role != 'admin':
            delete_button = QPushButton("Delete Account")
            delete_button.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
                QPushButton:pressed {
                    background-color: #bd2130;
                }
            """)
            delete_button.setFixedWidth(150)
            delete_button.clicked.connect(self.delete_account)
            top_row_layout.addWidget(delete_button)
        
        info_main_layout.addLayout(top_row_layout)
        main_layout.addWidget(info_frame)

        # --- Conditional UI based on Role ---
        if self.current_user_role == 'admin':
            self.setup_admin_ui(main_layout)
        else:
            self.setup_user_ui(main_layout)

        # --- Back Button ---
        back_button_layout = QHBoxLayout()
        back_button_layout.addStretch()
        back_button = QPushButton("Back to Home")
        back_button.clicked.connect(self.close)
        back_button_layout.addWidget(back_button)
        main_layout.addLayout(back_button_layout)

        self.setLayout(main_layout)

    def delete_account(self):
        """Handles the delete account action with user confirmation."""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Delete Account")
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setText("Are you sure you want to delete your account?")
        msg_box.setInformativeText(
            "This action will:\n"
            "• Remove your email and password from the system\n"
            "• Keep your reviews and ratings visible to others\n"
            "• Prevent you from logging in again\n\n"
            "This action cannot be undone."
        )
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        
        yes_button = msg_box.button(QMessageBox.Yes)
        yes_button.setText("Delete My Account")
        no_button = msg_box.button(QMessageBox.No)
        no_button.setText("Cancel")
        
        response = msg_box.exec_()
        
        if response == QMessageBox.Yes:
            print(f"DEBUG: User confirmed account deletion for userID {self.current_user_id}")
            
            result = self.user_service.delete_user(self.current_user_id)
            
            if result['success']:
                QMessageBox.information(
                    self,
                    "Account Deleted",
                    result['message'] + "\n\nYou will now be logged out."
                )
                
                # Log out the user
                self.session_manager.logout()
                
                # Emit signal to notify HomeWindow to update UI
                global_signals.user_logged_out.emit()
                
                # Close this window
                self.close()
                
            else:
                QMessageBox.critical(
                    self,
                    "Deletion Failed",
                    f"Failed to delete account: {result['message']}"
                )
                print(f"ERROR: Account deletion failed for userID {self.current_user_id}: {result['message']}")
        else:
            print("DEBUG: User cancelled account deletion")

    def setup_admin_ui(self, main_layout):
        """Sets up the UI elements specific to the admin profile view."""
        # --- Manage Movies (CRUD) Button ---
        crud_button_layout = QHBoxLayout()
        crud_button_layout.addStretch()
        manage_movies_button = QPushButton("Manage Movies")
        manage_movies_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;  
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        manage_movies_button.setFixedWidth(200)
        manage_movies_button.clicked.connect(self.open_movie_crud_window)
        crud_button_layout.addWidget(manage_movies_button)
        main_layout.addLayout(crud_button_layout)

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

        # --- Display Selected User Info with Remove User Button ---
        self.selected_user_info_frame = QFrame()
        selected_info_main_layout = QVBoxLayout(self.selected_user_info_frame)

        # Create horizontal layout for user info and remove button
        user_info_row_layout = QHBoxLayout()

        # Left side: User info
        selected_info_layout = QFormLayout()
        self.selected_user_email_label = QLabel(self.selected_user_email)
        self.selected_user_id_label = QLabel(str(self.selected_user_id))
        selected_info_layout.addRow("Viewing Profile For Email:", self.selected_user_email_label)
        selected_info_layout.addRow("User ID:", self.selected_user_id_label)

        user_info_row_layout.addLayout(selected_info_layout)
        
        # Add stretch to push remove button to the right
        user_info_row_layout.addStretch()
        
        # Right side: Remove User button
        self.remove_user_button = QPushButton("Remove User")
        self.remove_user_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                cursor: not-allowed;
            }
        """)
        self.remove_user_button.setFixedWidth(150)
        self.remove_user_button.clicked.connect(self.remove_user)
        user_info_row_layout.addWidget(self.remove_user_button)
        
        selected_info_main_layout.addLayout(user_info_row_layout)
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

        self.rated_movies_list.itemClicked.connect(self.open_movie_detail_from_list)

        # Update button state based on selected user
        self.update_remove_user_button_state()

    def remove_user(self):
        """Handles the admin removing a user account with role validation."""
        # First, get the full user data to check their role
        user_data = self.user_service.user_repo.get_user_by_email(self.selected_user_email)
        
        if not user_data:
            QMessageBox.warning(
                self,
                "User Not Found",
                "Could not find user information. Please try searching again."
            )
            return
        
        # Check if the user is an admin
        if user_data.get('role') == 'admin':
            QMessageBox.warning(
                self,
                "Cannot Remove Admin",
                "You cannot remove administrator accounts.\n\n"
                "Only regular user accounts can be removed."
            )
            print(f"DEBUG: Admin attempted to remove admin account (userID: {self.selected_user_id})")
            return
        
        # Check if trying to remove self (though this shouldn't happen in admin view)
        if self.selected_user_id == self.current_user_id:
            QMessageBox.warning(
                self,
                "Cannot Remove Self",
                "You cannot remove your own account from this interface.\n\n"
                "Please use the 'Delete Account' button if you wish to delete your own account."
            )
            return
        
        # Create detailed confirmation dialog
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Remove User Account")
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setText(f"Are you sure you want to remove this user account?")
        msg_box.setInformativeText(
            f"User: {self.selected_user_email}\n"
            f"User ID: {self.selected_user_id}\n\n"
            "This action will:\n"
            "• Remove the user's email and password from the system\n"
            "• Keep their reviews and ratings visible\n"
            "• Prevent them from logging in again\n\n"
            "This action cannot be undone."
        )
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        
        yes_button = msg_box.button(QMessageBox.Yes)
        yes_button.setText("Remove User")
        no_button = msg_box.button(QMessageBox.No)
        no_button.setText("Cancel")
        
        response = msg_box.exec_()
        
        if response == QMessageBox.Yes:
            print(f"DEBUG: Admin confirmed removal of user account (userID: {self.selected_user_id})")
            
            # Call the service layer to perform soft delete
            result = self.user_service.delete_user(self.selected_user_id)
            
            if result['success']:
                QMessageBox.information(
                    self,
                    "User Removed",
                    f"User account has been successfully removed.\n\n"
                    f"Email: {self.selected_user_email}\n"
                    f"User ID: {self.selected_user_id}\n\n"
                    "Their reviews and ratings remain in the system."
                )
                
                # Clear the selected user display
                self.selected_user_email_label.setText("No user selected")
                self.selected_user_id_label.setText("N/A")
                self.rated_movies_list.clear()
                self.search_email_input.clear()
                
                # Reset selected user to admin's own profile
                self.selected_user_id = self.current_user_id
                self.selected_user_email = self.current_user_email
                
                # Update button state
                self.update_remove_user_button_state()
                
                print(f"DEBUG: Successfully removed user account (userID: {self.selected_user_id})")
            else:
                QMessageBox.critical(
                    self,
                    "Removal Failed",
                    f"Failed to remove user account:\n\n{result['message']}"
                )
                print(f"ERROR: User removal failed for userID {self.selected_user_id}: {result['message']}")
        else:
            print("DEBUG: Admin cancelled user removal")

    def update_remove_user_button_state(self):
        """Updates the Remove User button's enabled state based on selected user."""
        if not hasattr(self, 'remove_user_button'):
            return
        
        # Disable button if viewing own profile or if no user is selected
        if self.selected_user_id == self.current_user_id or not self.selected_user_id:
            self.remove_user_button.setEnabled(False)
            self.remove_user_button.setToolTip("Cannot remove your own account")
        else:
            # Check if selected user is an admin
            user_data = self.user_service.user_repo.get_user_by_email(self.selected_user_email)
            if user_data and user_data.get('role') == 'admin':
                self.remove_user_button.setEnabled(False)
                self.remove_user_button.setToolTip("Cannot remove administrator accounts")
            else:
                self.remove_user_button.setEnabled(True)
                self.remove_user_button.setToolTip("Remove this user account")

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

        self.rated_movies_list.itemClicked.connect(self.open_movie_detail_from_list)

    def search_user_by_email(self):
        """Handles the admin search for a user by email using UserService."""
        email_to_search = self.search_email_input.text().strip()
        if not email_to_search:
            QMessageBox.warning(self, 'Search Error', 'Please enter an email address to search.')
            return

        searched_user_data = self.user_service.user_repo.get_user_by_email(email_to_search)

        if searched_user_data:
            self.selected_user_id = searched_user_data['userID']
            self.selected_user_email = searched_user_data['email']
            self.selected_user_email_label.setText(self.selected_user_email)
            self.selected_user_id_label.setText(str(self.selected_user_id))
            self.load_profile_data()
            self.update_remove_user_button_state()
        else:
            QMessageBox.information(self, 'User Not Found', f'No user found with email: {email_to_search}')

    def load_profile_data(self):
        """Loads the rated/reviewed movies for the currently selected user (self.selected_user_id)."""
        if not self.selected_user_id:
            print(f"DEBUG: ProfileWindow.load_profile_data: selected_user_id is None or 0.")
            return

        print(f"DEBUG: ProfileWindow.load_profile_data: Loading data for userID {self.selected_user_id}")

        # Get the raw data from the service (includes ratings and reviews)
        user_interactions = self.rating_service.get_user_ratings_and_reviews_for_profile(self.selected_user_id)
        print(f"DEBUG: ProfileWindow.load_profile_data: Retrieved {len(user_interactions)} interactions (ratings/reviews) via service.")

        # --- GUI LOGIC CHANGE: Separate, Sort, and Combine ---
        # 1. Separate interactions based on presence of rating
        rated_movies = [] # For movies with a rating (may or may not have a review)
        reviewed_only_movies = [] # For movies with only a review (no rating)

        for item in user_interactions:
            if item['rating'] is not None:
                rated_movies.append(item)
            else: # item['rating'] is None
                reviewed_only_movies.append(item)

        # 2. Sort each list according to the rules
        # Sort rated movies by rating value (descending)
        rated_movies.sort(key=lambda x: x['rating'], reverse=True)
        # Sort reviewed-only movies by review_timeStamp (descending)
        # Note: The unified query sets review_timeStamp correctly for review-only entries.
        # We need to ensure the processed list from the service correctly maps the timestamp.
        # Assuming the service logic correctly assigns 'timeStamp' based on review_timeStamp for review-only entries.
        # If the service sets 'timeStamp' correctly, use it:
        reviewed_only_movies.sort(key=lambda x: x.get('timeStamp'), reverse=True)
        # If the service doesn't set 'timeStamp' correctly for review-only, you might need to rely on
        # the original repository query's 'review_timeStamp' field if accessible here,
        # or ensure the service correctly populates 'timeStamp' when rating is None.

        # 3. Combine the two lists: rated first, then reviewed-only
        sorted_interactions = rated_movies + reviewed_only_movies

        print(f"DEBUG: ProfileWindow.load_profile_data: After separating/sorting, {len(rated_movies)} rated and {len(reviewed_only_movies)} review-only movies.")

        print("DEBUG: ProfileWindow.load_profile_data: Clearing existing list.")
        self.rated_movies_list.clear()

        print("DEBUG: ProfileWindow.load_profile_data: Starting to populate list widget with sorted data.")
        for i, interaction in enumerate(sorted_interactions):
            print(f"DEBUG: ProfileWindow.load_profile_data: Processing sorted interaction {i+1}: {interaction}")
            try:
                tmdb_id = interaction['tmdbID']
                movie_title = interaction['title']
                rating_value = interaction['rating']
                review_text = interaction['review']
                # The 'timeStamp' here should be correctly set by the service based on the interaction type
                timestamp = interaction.get('timeStamp', 'N/A')

                # Construct item text based on presence of rating and review
                if rating_value is not None:
                    item_text = f"{movie_title} - Rating: {rating_value}/5"
                    # If there's also a review, add it on the next line
                    if review_text:
                        item_text += f"\nReview: {review_text}"
                    # Optionally, show timestamp if rating has one (though it's None from the query)
                    # item_text += f" (Time: {timestamp})" # This would show (Time: None) based on query
                else: # rating_value is None, must be review-only
                    item_text = f"{movie_title} - Review (No Rating) (Time: {timestamp})"
                    # Add the review text
                    item_text += f"\nReview: {review_text if review_text else 'No Review Text'}"

                print(f"DEBUG: ProfileWindow.load_profile_data: Item text for tmdbID {tmdb_id}: {item_text[:50]}...")

                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, tmdb_id)

                self.rated_movies_list.addItem(item)
                print(f"DEBUG: ProfileWindow.load_profile_data: Added item for tmdbID {tmdb_id} to list.")

            except KeyError as e:
                print(f"ERROR: ProfileWindow.load_profile_data: Missing key in interaction data: {e}. Interaction: {interaction}")
                continue
            except Exception as e:
                print(f"ERROR: ProfileWindow.load_profile_data: Unexpected error processing interaction {i+1}: {e}. Interaction: {interaction}")
                import traceback
                traceback.print_exc()
                continue

        print("DEBUG: ProfileWindow.load_profile_data: Finished populating list widget with sorted data.")

    def open_movie_detail_from_list(self, item):
        """Opens the MovieDetailWindow for the movie associated with the clicked list item."""
        tmdb_id = item.data(Qt.UserRole)
        if tmdb_id:
            print(f"DEBUG: ProfileWindow.open_movie_detail_from_list: Opening detail for tmdbID {tmdb_id}")
            detail_window = MovieDetailWindow(tmdb_id)
            detail_window.show()
        else:
            print("DEBUG: ProfileWindow.open_movie_detail_from_list: No tmdbID found in item data.")
            
    def open_movie_crud_window(self):
        """Opens the MovieCrudWindow for creating/editing movies."""
        from gui.gui_movie_crud import MovieCrudWindow
        if self.movie_crud_window is None or not self.movie_crud_window.isVisible():
            self.movie_crud_window = MovieCrudWindow(parent=self)
        self.movie_crud_window.show()
        self.movie_crud_window.raise_()  # Bring window to front
        print("DEBUG: Opening Movie CRUD window")