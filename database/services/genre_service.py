# database/services/genre_service.py
from database.repositories.genre_repository import GenreRepository
import threading

class GenreService:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(GenreService, cls).__new__(cls)
                    cls._instance.genre_repo = GenreRepository()
        return cls._instance

    def get_all_genres(self):
        """Retrieves all genres.
        
        Returns:
            dict: Response with success status and list of genre dictionaries
        """
        genres = self.genre_repo.get_all_genres()
        
        # Format genres consistently
        formatted_genres = []
        for genre in genres:
            if isinstance(genre, dict):
                formatted_genres.append({
                    'genreID': genre.get('genreID'),
                    'genreName': genre.get('genreName')
                })
            else:
                try:
                    formatted_genres.append({
                        'genreID': genre[0] if len(genre) > 0 else None,
                        'genreName': genre[1] if len(genre) > 1 else str(genre)
                    })
                except (TypeError, IndexError):
                    formatted_genres.append({
                        'genreID': None,
                        'genreName': str(genre)
                    })
        
        return {
            "success": True,
            "genres": formatted_genres
        }

    def get_genres_for_movie(self, tmdb_id):
        """Retrieves genres for a specific movie.
        
        Args:
            tmdb_id (int): The tmdbID of the movie
            
        Returns:
            dict: Response with success status and list of genre dictionaries
        """
        genres = self.genre_repo.get_genres_for_movie(tmdb_id)
        
        # Ensure genres are returned as list of dicts with consistent structure
        formatted_genres = []
        for genre in genres:
            if isinstance(genre, dict):
                # Already a dict, ensure it has genreName key
                formatted_genres.append({
                    'genreID': genre.get('genreID'),
                    'genreName': genre.get('genreName')
                })
            elif isinstance(genre, str):
                # If repository returned just strings, wrap them
                formatted_genres.append({
                    'genreID': None,
                    'genreName': genre
                })
            else:
                # Handle tuple/list format from SQL queries
                try:
                    formatted_genres.append({
                        'genreID': genre[0] if len(genre) > 0 else None,
                        'genreName': genre[1] if len(genre) > 1 else str(genre)
                    })
                except (TypeError, IndexError):
                    formatted_genres.append({
                        'genreID': None,
                        'genreName': str(genre)
                    })
        
        return {
            "success": True,
            "genres": formatted_genres
        }

    def get_movies_by_genre(self, genre_name):
        """Retrieves movies for a specific genre.
        
        Args:
            genre_name (str): Name of the genre
            
        Returns:
            dict: Response with success status and list of movies
        """
        movies = self.genre_repo.get_movies_by_genre(genre_name)
        return {
            "success": True,
            "movies": movies
        }

    def add_genre(self, genre_name):
        """Adds a new genre (Admin functionality)."""
        if not genre_name or len(genre_name.strip()) == 0:
             return {"success": False, "message": "Genre name cannot be empty."}

        success = self.genre_repo.create_genre(genre_name.strip())
        if not success:
            return {"success": False, "message": "Failed to add genre in the database or genre already exists."}

        return {"success": True, "message": "Genre added successfully."}

    #should technically not be possible to update genre names
    # def update_genre(self, genre_id, new_genre_name):
    #     """Updates an existing genre (Admin functionality)."""
    #     if not new_genre_name or len(new_genre_name.strip()) == 0:
    #          return {"success": False, "message": "Genre name cannot be empty."}

    #     success = self.genre_repo.update_genre(genre_id, new_genre_name.strip())
    #     if not success:
    #         return {"success": False, "message": "Failed to update genre in the database or genre does not exist."}

    #     return {"success": True, "message": "Genre updated successfully."}

    # def delete_genre(self, genre_id):
    #     """Deletes a genre (Admin functionality). Note: May fail due to FK constraints."""
    #     success = self.genre_repo.delete_genre(genre_id)
    #     if not success:
    #         return {"success": False, "message": "Failed to delete genre in the database, likely due to existing movie associations."}

    #     return {"success": True, "message": "Genre deleted successfully."}
