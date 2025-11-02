from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFormLayout, QLineEdit, QTextEdit, QDateEdit, QListWidget,
    QMessageBox, QSpinBox, QComboBox, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QListWidgetItem, QGroupBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize
from database.services.movie_service import MovieService
from database.services.genre_service import GenreService
from database.services.cast_crew_service import CastCrewService
from gui.gui_signals import global_signals

class MovieForm(QWidget):
    """A reusable movie form widget for both create and edit operations"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.movie_service = MovieService()
        self.genre_service = GenreService()
        self.cast_crew_service = CastCrewService()
        self.movie_data = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Title
        self.title_input = QLineEdit()
        form_layout.addRow('Title:', self.title_input)

        # Link (optional)
        self.link_input = QLineEdit()
        form_layout.addRow('Link (optional):', self.link_input)

        # Runtime
        self.runtime_input = QSpinBox()
        self.runtime_input.setRange(0, 999)  # Most movies are under 1000 minutes
        form_layout.addRow('Runtime (minutes):', self.runtime_input)

        # Poster URL
        self.poster_input = QLineEdit()
        form_layout.addRow('Poster URL:', self.poster_input)

        # Overview
        self.overview_input = QTextEdit()
        self.overview_input.setPlaceholderText("Enter movie overview/description...")
        form_layout.addRow('Overview:', self.overview_input)

        # Release Date
        self.release_date_input = QDateEdit()
        self.release_date_input.setCalendarPopup(True)
        self.release_date_input.setDate(QDate.currentDate())
        form_layout.addRow('Release Date:', self.release_date_input)

        # Genres
        genres_container = QWidget()
        genres_container_layout = QVBoxLayout(genres_container)
        genres_container_layout.setContentsMargins(0, 0, 0, 0)

        # Genre selection controls
        selection_widget = QWidget()
        selection_layout = QHBoxLayout(selection_widget)
        selection_layout.setContentsMargins(0, 0, 0, 0)

        self.genre_combo = QComboBox()
        # Load genres into combo box
        genre_result = self.genre_service.get_all_genres()
        if genre_result.get('success'):
            genres = genre_result.get('genres', [])
            for genre in genres:
                self.genre_combo.addItem(genre['genreName'])
        
        add_genre_btn = QPushButton("Add Genre")
        add_genre_btn.clicked.connect(self.add_genre_to_list)
        
        selection_layout.addWidget(self.genre_combo)
        selection_layout.addWidget(add_genre_btn)
        genres_container_layout.addWidget(selection_widget)

        # Genre list with custom items (including remove buttons)
        self.genre_list = QListWidget()
        self.genre_list.setMaximumHeight(150)
        genres_container_layout.addWidget(self.genre_list)

        form_layout.addRow('Genres:', genres_container)

        layout.addLayout(form_layout)
        self.setLayout(layout)

        cast_crew_group = QGroupBox("Cast & Crew")
        cast_crew_layout = QVBoxLayout(cast_crew_group)

        # Cast Section
        cast_section_layout = QVBoxLayout()
        cast_section_layout.addWidget(QLabel("Cast"))

        # Cast Input Fields
        cast_input_layout = QHBoxLayout()
        self.cast_name_input = QLineEdit()
        self.cast_name_input.setPlaceholderText("Actor Name")
        self.cast_character_input = QLineEdit()
        self.cast_character_input.setPlaceholderText("Character")
        # self.cast_actor_id_input = QLineEdit() # REMOVED
        # self.cast_actor_id_input.setValidator(QtGui.QIntValidator()) # REMOVED

        cast_input_layout.addWidget(self.cast_name_input)
        cast_input_layout.addWidget(self.cast_character_input)
        # cast_input_layout.addWidget(self.cast_actor_id_input) # REMOVED

        # Cast Add Button
        self.add_cast_btn = QPushButton("Add Cast Member")
        self.add_cast_btn.clicked.connect(self.add_cast_member_to_form)

        cast_section_layout.addLayout(cast_input_layout)
        cast_section_layout.addWidget(self.add_cast_btn)

        # Cast Display List
        self.cast_display_list = QListWidget()
        self.cast_display_list.setMaximumHeight(100)
        cast_section_layout.addWidget(self.cast_display_list)

        cast_crew_layout.addLayout(cast_section_layout)

        # Crew Section
        crew_section_layout = QVBoxLayout()
        crew_section_layout.addWidget(QLabel("Crew"))

        # Crew Input Fields
        crew_input_layout = QHBoxLayout()
        self.crew_name_input = QLineEdit()
        self.crew_name_input.setPlaceholderText("Crew Member Name")
        self.crew_job_input = QLineEdit()
        self.crew_job_input.setPlaceholderText("Job")
        self.crew_department_input = QLineEdit()
        self.crew_department_input.setPlaceholderText("Department")
        # self.crew_person_id_input = QLineEdit() # REMOVED
        # self.crew_person_id_input.setValidator(QtGui.QIntValidator()) # REMOVED

        crew_input_layout.addWidget(self.crew_name_input)
        crew_input_layout.addWidget(self.crew_job_input)
        crew_input_layout.addWidget(self.crew_department_input)
        # crew_input_layout.addWidget(self.crew_person_id_input) # REMOVED

        # Crew Add Button
        self.add_crew_btn = QPushButton("Add Crew Member")
        self.add_crew_btn.clicked.connect(self.add_crew_member_to_form)

        crew_section_layout.addLayout(crew_input_layout)
        crew_section_layout.addWidget(self.add_crew_btn)

        # Crew Display List (with custom items and remove buttons)
        self.crew_display_list = QListWidget()
        self.crew_display_list.setMaximumHeight(100)
        crew_section_layout.addWidget(self.crew_display_list)

        cast_crew_layout.addLayout(crew_section_layout)

        layout.addWidget(cast_crew_group)
        self.setLayout(layout)

    # Create custom list item widgets for cast/crew with remove buttons
    def create_cast_item(self, name, character):
        """Create a custom list item with cast member details and a remove button"""
        item = QListWidgetItem(self.cast_display_list)

        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)

        label = QLabel(f"{name} as {character}")
        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(20, 20)
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff4444;
                border-radius: 10px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff0000;
            }
        """)
        # Connect the remove button to remove the item from the list
        remove_btn.clicked.connect(lambda: self.cast_display_list.takeItem(self.cast_display_list.row(item)))

        layout.addWidget(label)
        layout.addWidget(remove_btn)
        layout.addStretch()

        widget.setLayout(layout)
        item.setSizeHint(widget.sizeHint())
        # Store the data in the item itself for retrieval later
        item.setData(Qt.UserRole, {"name": name, "character": character})
        self.cast_display_list.setItemWidget(item, widget)
        return item

    def create_crew_item(self, name, job, department):
        """Create a custom list item with crew member details and a remove button"""
        item = QListWidgetItem(self.crew_display_list)

        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)

        label = QLabel(f"{name} - {job} ({department})")
        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(20, 20)
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff4444;
                border-radius: 10px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff0000;
            }
        """)
        # Connect the remove button to remove the item from the list
        remove_btn.clicked.connect(lambda: self.crew_display_list.takeItem(self.crew_display_list.row(item)))

        layout.addWidget(label)
        layout.addWidget(remove_btn)
        layout.addStretch()

        widget.setLayout(layout)
        item.setSizeHint(widget.sizeHint())
        # Store the data in the item itself for retrieval later
        item.setData(Qt.UserRole, {"name": name, "job": job, "department": department})
        self.crew_display_list.setItemWidget(item, widget)
        return item

    def add_cast_member_to_form(self):
        """Add a cast member to the display list based on input fields, checking for duplicates by name."""
        name = self.cast_name_input.text().strip()
        character = self.cast_character_input.text().strip()
        # actor_id_text = self.cast_actor_id_input.text().strip() # REMOVED

        if not name or not character: # Removed actor_id_text check
            QMessageBox.warning(self, "Input Error", "Please fill in all cast member fields (Name, Character).")
            return

        # Check for duplicate in the display list before adding (using name)
        duplicate_found = False
        for i in range(self.cast_display_list.count()):
            item = self.cast_display_list.item(i)
            existing_data = item.data(Qt.UserRole)
            if existing_data and existing_data['name'] == name:
                duplicate_found = True
                # Optionally, ask user if they want to update the character
                reply = QMessageBox.question(
                    self, 'Duplicate Actor Name',
                    f"Actor '{name}' already exists in the list. Update character from '{existing_data['character']}' to '{character}'?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    # Update the existing item's text and data
                    existing_data['character'] = character
                    # Find the label widget within the item's custom widget
                    item_widget = self.cast_display_list.itemWidget(item)
                    label = item_widget.layout().itemAt(0).widget() # First item in the QHBoxLayout is the label
                    label.setText(f"{name} as {character}")
                    # Update the data stored in the item
                    item.setData(Qt.UserRole, existing_data)
                    # Clear inputs after update
                    self.cast_name_input.clear()
                    self.cast_character_input.clear()
                break # Exit the loop after handling the duplicate

        if not duplicate_found:
            # Create a custom item with a remove button
            self.create_cast_item(name, character)

            # Clear inputs after adding
            self.cast_name_input.clear()
            self.cast_character_input.clear()

    def add_crew_member_to_form(self):
        """Add a crew member to the display list based on input fields, checking for duplicates by name and job."""
        name = self.crew_name_input.text().strip()
        job = self.crew_job_input.text().strip()
        department = self.crew_department_input.text().strip()
        # person_id_text = self.crew_person_id_input.text().strip() # REMOVED

        if not name or not job or not department: # Removed person_id_text check
            QMessageBox.warning(self, "Input Error", "Please fill in all crew member fields (Name, Job, Department).")
            return

        # Check for duplicate in the display list before adding (using name and job)
        duplicate_found = False
        for i in range(self.crew_display_list.count()):
            item = self.crew_display_list.item(i)
            existing_data = item.data(Qt.UserRole)
            if existing_data and existing_data['name'] == name and existing_data['job'] == job:
                duplicate_found = True
                # Optionally, ask user if they want to update the department
                reply = QMessageBox.question(
                    self, 'Duplicate Name and Job',
                    f"Person '{name}' with job '{job}' already exists in the list. Update department from '{existing_data['department']}' to '{department}'?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    # Update the existing item's text and data
                    existing_data['department'] = department
                    # Find the label widget within the item's custom widget
                    item_widget = self.crew_display_list.itemWidget(item)
                    label = item_widget.layout().itemAt(0).widget() # First item in the QHBoxLayout is the label
                    label.setText(f"{name} - {job} ({department})")
                    # Update the data stored in the item
                    item.setData(Qt.UserRole, existing_data)
                    # Clear inputs after update
                    self.crew_name_input.clear()
                    self.crew_job_input.clear()
                    self.crew_department_input.clear()
                break # Exit the loop after handling the duplicate

        if not duplicate_found:
            #  Create a custom item with a remove button
            self.create_crew_item(name, job, department)

            # Clear inputs after adding
            self.crew_name_input.clear()
            self.crew_job_input.clear()
            self.crew_department_input.clear()

    def create_genre_item(self, genre_name):
        """Create a custom list item with a genre and remove button"""
        item = QListWidgetItem(self.genre_list)
        
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)
        
        label = QLabel(genre_name)
        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(20, 20)
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff4444;
                border-radius: 10px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff0000;
            }
        """)
        remove_btn.clicked.connect(lambda: self.genre_list.takeItem(self.genre_list.row(item)))
        
        layout.addWidget(label)
        layout.addWidget(remove_btn)
        layout.addStretch()
        
        widget.setLayout(layout)
        item.setSizeHint(widget.sizeHint())
        self.genre_list.setItemWidget(item, widget)
        return item

    def add_genre_to_list(self):
        """Add selected genre to the list if not already present"""
        current_genre = self.genre_combo.currentText()
        # Get current genres from list
        current_items = []
        for i in range(self.genre_list.count()):
            item_widget = self.genre_list.itemWidget(self.genre_list.item(i))
            label = item_widget.layout().itemAt(0).widget()
            current_items.append(label.text())
        
        if current_genre not in current_items:
            self.create_genre_item(current_genre)

    def clear_form(self):
        """Clear all form fields"""
        self.title_input.clear()
        self.link_input.clear()
        self.runtime_input.setValue(0)
        self.poster_input.clear()
        self.overview_input.clear()
        self.release_date_input.setDate(QDate.currentDate())
        self.genre_list.clear()
        self.cast_display_list.clear() # Clear cast list
        self.crew_display_list.clear() # Clear crew list
        self.movie_data = None

    def load_movie_data(self, movie_data):
        """Load movie data into the form for editing"""
        self.movie_data = movie_data
        if not movie_data:
            return

        self.title_input.setText(movie_data['title'])
        self.link_input.setText(movie_data.get('link', ''))
        self.runtime_input.setValue(movie_data.get('runtime', 0) or 0)
        self.poster_input.setText(movie_data.get('poster', ''))
        self.overview_input.setText(movie_data.get('overview', ''))

        # Set release date
        if movie_data.get('releaseDate'):
            release_date = QDate.fromString(str(movie_data['releaseDate']), "yyyy-MM-dd")
            self.release_date_input.setDate(release_date)

        # Load genres
        self.genre_list.clear()
        genre_result = self.genre_service.get_genres_for_movie(movie_data['tmdbID'])
        if genre_result.get('success'):
            genres = genre_result.get('genres', [])
            for genre in genres:
                self.create_genre_item(genre['genreName'])

        # Load Cast and Crew data
        if movie_data.get('tmdbID'):
            tmdb_id = movie_data['tmdbID']
            
            cast_result = self.cast_crew_service.get_cast_for_movie(tmdb_id)
            if cast_result.get('success'):
                cast_data = cast_result.get('cast', [])
                self.cast_display_list.clear()
                for person in cast_data:
                    self.create_cast_item(person['name'], person['character'])

            crew_result = self.cast_crew_service.get_crew_for_movie(tmdb_id)
            if crew_result.get('success'):
                crew_data = crew_result.get('crew', [])
                self.crew_display_list.clear()
                for person in crew_data:
                    self.create_crew_item(person['name'], person['job'], person['department'])

    def get_movie_data(self):
        """Get the current form data as a dictionary, including cast/crew lists."""
        # Get genres from custom list items
        genres = []
        for i in range(self.genre_list.count()):
            item_widget = self.genre_list.itemWidget(self.genre_list.item(i))
            label = item_widget.layout().itemAt(0).widget()
            genres.append(label.text())

        # : Get cast and crew data from the custom display list items (Removed ID from stored data)
        cast_list = []
        for i in range(self.cast_display_list.count()):
            item = self.cast_display_list.item(i)
            # Retrieve data stored in the item using Qt.UserRole
            cast_data = item.data(Qt.UserRole)
            cast_list.append(cast_data)

        crew_list = []
        for i in range(self.crew_display_list.count()):
            item = self.crew_display_list.item(i)
            # Retrieve data stored in the item using Qt.UserRole
            crew_data = item.data(Qt.UserRole)
            crew_list.append(crew_data)

        movie_data = {
            "title": self.title_input.text().strip(),
            "link": self.link_input.text().strip() or None,
            "runtime": self.runtime_input.value(),
            "poster": self.poster_input.text().strip() or None,
            "overview": self.overview_input.toPlainText().strip() or None,
            "releaseDate": self.release_date_input.date().toString("yyyy-MM-dd"),
            "genres": genres,
            "cast": cast_list,
            "crew": crew_list
        }
        if self.movie_data:
            movie_data["tmdbID"] = self.movie_data["tmdbID"]
        return movie_data
    
    # Helper methods to handle saving cast/crew data when the movie is saved/updated (Removed ID from calls)
    def save_cast_data(self, tmdb_id):
        """Saves the cast data from the form to the MongoDB database."""
        cast_list = self.get_movie_data()["cast"] # Re-fetch cast list
        for person in cast_list:
            result = self.cast_crew_service.add_cast_member(
                tmdb_id, person['name'], person['character'] # Removed actor_id from call
            )
            if not result["success"]:
                print(f"Warning: Could not save cast member {person['name']}: {result['message']}")

    def save_crew_data(self, tmdb_id):
        """Saves the crew data from the form to the MongoDB database."""
        crew_list = self.get_movie_data()["crew"] # Re-fetch crew list
        for person in crew_list:
            result = self.cast_crew_service.add_crew_member(
                tmdb_id, person['name'], person['job'], person['department'] # Removed person_id from call
            )
            if not result["success"]:
                print(f"Warning: Could not save crew member {person['name']}: {result['message']}")

class MovieSearchPanel(QWidget):
    """Advanced search panel for movies with title, genre, and year filters"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.movie_service = MovieService()
        self.genre_service = GenreService()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Search filters
        filters_layout = QHBoxLayout()

        # Title filter
        title_layout = QVBoxLayout()
        title_layout.addWidget(QLabel("Title:"))
        self.title_input = QLineEdit()
        title_layout.addWidget(self.title_input)
        filters_layout.addLayout(title_layout)

        # Genre filter
        genre_layout = QVBoxLayout()
        genre_layout.addWidget(QLabel("Genre:"))
        self.genre_combo = QComboBox()
        self.genre_combo.addItem("All Genres")
        
        genre_result = self.genre_service.get_all_genres()
        if genre_result.get('success'):
            genres = genre_result.get('genres', [])
            for genre in genres:
                self.genre_combo.addItem(genre['genreName'])
        
        genre_layout.addWidget(self.genre_combo)
        filters_layout.addLayout(genre_layout)

        # Year filter
        year_layout = QVBoxLayout()
        year_layout.addWidget(QLabel("Year:"))
        self.year_combo = QComboBox()
        self.year_combo.addItem("All Years")
        
        years_result = self.movie_service.get_available_years()
        if years_result.get('success'):
            years = years_result.get('years', [])
            for year in years:
                self.year_combo.addItem(str(year))
        
        year_layout.addWidget(self.year_combo)
        filters_layout.addLayout(year_layout)

        # Search button
        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.search_movies)
        filters_layout.addWidget(self.search_btn)

        layout.addLayout(filters_layout)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["tmdbID", "Title", "Release Date", "Runtime"])
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.results_table.verticalHeader().setVisible(False)
        layout.addWidget(self.results_table)

        self.setLayout(layout)

    def search_movies(self):
        """Perform movie search with filters"""
        title = self.title_input.text().strip()
        genre = self.genre_combo.currentText()
        genre = None if genre == "All Genres" else genre
        year = self.year_combo.currentText()
        year = None if year == "All Years" else int(year)

        # Search with filters
        results = self.movie_service.search_movies_by_title(
            search_term=title,
            genre=genre,
            year=year
        )["movies"]  # Get the movies from the pagination result

        # Clear and populate table
        self.results_table.setRowCount(0)
        for movie in results:
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            self.results_table.setItem(row, 0, QTableWidgetItem(str(movie['tmdbID'])))
            self.results_table.setItem(row, 1, QTableWidgetItem(movie['title']))
            self.results_table.setItem(row, 2, QTableWidgetItem(str(movie['releaseDate'])))
            self.results_table.setItem(row, 3, QTableWidgetItem(str(movie.get('runtime', ''))))

class MovieCrudWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.movie_service = MovieService()
        self.cast_crew_service = CastCrewService()
        self.parent = parent
        
        self.setWindowTitle('Movie Management')
        self.setGeometry(100, 100, 1000, 800)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Create tab widget
        self.tab_widget = QTabWidget()

        # Create Tab
        create_tab = QWidget()
        create_layout = QVBoxLayout()
        self.create_form = MovieForm()
        create_layout.addWidget(self.create_form)

        # Create buttons
        create_buttons = QHBoxLayout()
        save_new_btn = QPushButton("Save")
        save_new_btn.clicked.connect(self.create_movie)
        cancel_new_btn = QPushButton("Cancel")
        cancel_new_btn.clicked.connect(self.close)
        create_buttons.addStretch()
        create_buttons.addWidget(save_new_btn)
        create_buttons.addWidget(cancel_new_btn)
        create_layout.addLayout(create_buttons)
        create_tab.setLayout(create_layout)

        # Update/Delete Tab
        update_tab = QWidget()
        update_layout = QVBoxLayout()

        # Add search panel
        self.search_panel = MovieSearchPanel()
        update_layout.addWidget(self.search_panel)

        # Add form for editing
        self.edit_form = MovieForm()
        update_layout.addWidget(self.edit_form)

        # Add buttons
        edit_buttons = QHBoxLayout()
        update_btn = QPushButton("Update")
        update_btn.clicked.connect(self.update_movie)
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_movie)
        delete_btn.setStyleSheet("background-color: #dc3545; color: white;")
        cancel_edit_btn = QPushButton("Cancel")
        cancel_edit_btn.clicked.connect(self.close)
        edit_buttons.addStretch()
        edit_buttons.addWidget(update_btn)
        edit_buttons.addWidget(delete_btn)
        edit_buttons.addWidget(cancel_edit_btn)
        update_layout.addLayout(edit_buttons)
        
        update_tab.setLayout(update_layout)

        # Add tabs
        self.tab_widget.addTab(create_tab, "Create Movie")
        self.tab_widget.addTab(update_tab, "Update/Delete Movie")

        layout.addWidget(self.tab_widget)
        self.setLayout(layout)

        # Connect table selection to form update
        self.search_panel.results_table.itemSelectionChanged.connect(self.load_selected_movie)

    def load_selected_movie(self):
        """Load the selected movie into the edit form"""
        table = self.search_panel.results_table
        current_row = table.currentRow()
        if current_row >= 0:
            tmdb_id = int(table.item(current_row, 0).text())
            movie_result = self.movie_service.get_movie_detail(tmdb_id)
            if movie_result.get('success') and movie_result.get('movie'):
                self.edit_form.load_movie_data(movie_result['movie'])

    def create_movie(self):
        """Create a new movie"""
        movie_data = self.create_form.get_movie_data()

        # Validate
        if not movie_data["title"]:
            QMessageBox.warning(self, "Validation Error", "Title is required!")
            return
        if not movie_data["genres"]:
            QMessageBox.warning(self, "Validation Error", "At least one genre is required!")
            return

        try:
            result = self.movie_service.create_movie(movie_data)
            print(f"DEBUG: MovieService.create_movie returned result: {result}")
            if result["success"]:
                tmdb_id = result.get("movie_id")
                print(f"DEBUG: Retrieved tmdbID from result: {tmdb_id}")
                if tmdb_id:
                    self.create_form.cast_crew_service = self.cast_crew_service
                    print(f"DEBUG: About to call save_cast_data for tmdbID {tmdb_id}")
                    self.create_form.save_cast_data(tmdb_id)
                    print(f"DEBUG: About to call save_crew_data for tmdbID {tmdb_id}")
                    self.create_form.save_crew_data(tmdb_id)
                    print(f"DEBUG: Finished calling save_cast_data and save_crew_data for tmdbID {tmdb_id}")
                else:
                    print(f"DEBUG: WARNING: tmdbID was not found in the result: {result}")
                QMessageBox.information(self, "Success", "Movie created successfully!")
                self.create_form.clear_form()
                
                # ADDED: emit a signal to notify other windows
                global_signals.movie_data_updated.emit(tmdb_id)
                self.close()
            else:
                QMessageBox.critical(self, "Error", f"Failed to create movie: {result['message']}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def update_movie(self):
        """Update the selected movie"""
        movie_data = self.edit_form.get_movie_data()
        if not movie_data.get("tmdbID"):
            QMessageBox.warning(self, "Warning", "Please select a movie to update")
            return

        # Validate
        if not movie_data["title"]:
            QMessageBox.warning(self, "Validation Error", "Title is required!")
            return
        if not movie_data["genres"]:
            QMessageBox.warning(self, "Validation Error", "At least one genre is required!")
            return

        # FIXED: Use service layer instead of repository
        stats_result = self.movie_service.get_movie_stats(movie_data["tmdbID"])
        if stats_result.get('success'):
            rating_count = stats_result.get('rating_count', 0)
            review_count = stats_result.get('review_count', 0)
            
            if rating_count > 0 or review_count > 0:
                stats_msg = []
                if rating_count > 0:
                    stats_msg.append(f"{rating_count} rating(s)")
                if review_count > 0:
                    stats_msg.append(f"{review_count} review(s)")
                reply = QMessageBox.question(self, 'Warning',
                    f"This movie has {' and '.join(stats_msg)}. Are you sure you want to update it?\n\n"
                    f"Note: This will not affect existing ratings and reviews.",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    return

        try:
            result = self.movie_service.update_movie(movie_data)
            if result["success"]:
                # After updating the movie, save/overwrite cast/crew data
                tmdb_id = movie_data["tmdbID"]
                # Call the helper methods on the edit_form instance
                self.edit_form.cast_crew_service = self.cast_crew_service
                self.edit_form.save_cast_data(tmdb_id)
                self.edit_form.save_crew_data(tmdb_id)

                QMessageBox.information(self, "Success", "Movie updated successfully!")
                self.search_panel.search_movies()  # Refresh search results
                self.edit_form.clear_form()
                
                # Emit signal to notify other windows
                global_signals.movie_data_updated.emit(tmdb_id)
            else:
                QMessageBox.critical(self, "Error", f"Failed to update movie: {result['message']}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def delete_movie(self):
        """Delete the selected movie"""
        movie_data = self.edit_form.get_movie_data()
        if not movie_data.get("tmdbID"):
            QMessageBox.warning(self, "Warning", "Please select a movie to delete")
            return

        # FIXED: Use service layer instead of repository
        stats_result = self.movie_service.get_movie_stats(movie_data["tmdbID"])
        warning_msg = f"Are you sure you want to delete '{movie_data['title']}'?"

        if stats_result.get('success'):
            rating_count = stats_result.get('rating_count', 0)
            review_count = stats_result.get('review_count', 0)
            
            if rating_count > 0 or review_count > 0:
                stats_msg = []
                if rating_count > 0:
                    stats_msg.append(f"{rating_count} rating(s)")
                if review_count > 0:
                    stats_msg.append(f"{review_count} review(s)")

                warning_msg += f"\n\nWARNING: This movie has {' and '.join(stats_msg)}.\n"
                warning_msg += "All associated ratings and reviews will also be deleted."

        reply = QMessageBox.question(self, 'Delete Movie',
            warning_msg,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                # Delete cast/crew data from MongoDB BEFORE deleting the movie from MySQL
                tmdb_id = movie_data["tmdbID"]
                print(f"DEBUG: Attempting to delete cast/crew for tmdbID {tmdb_id} before deleting movie.")
                cast_result = self.cast_crew_service.delete_all_cast_for_movie(tmdb_id)
                crew_result = self.cast_crew_service.delete_all_crew_for_movie(tmdb_id)

                if not cast_result["success"]:
                    print(f"WARNING: Could not delete cast for movie {tmdb_id}: {cast_result['message']}")
                if not crew_result["success"]:
                    print(f"WARNING: Could not delete crew for movie {tmdb_id}: {crew_result['message']}")

                # Now, delete the main movie entry
                result = self.movie_service.delete_movie(tmdb_id)
                if result["success"]:
                    QMessageBox.information(self, "Success", "Movie deleted successfully!")
                    self.search_panel.search_movies()  # Refresh search results
                    self.edit_form.clear_form()
                    
                    # Emit signal to notify other windows
                    global_signals.movie_data_updated.emit(tmdb_id)
                else:
                    QMessageBox.critical(self, "Error", f"Failed to delete movie: {result['message']}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")