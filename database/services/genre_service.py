# database/services/genre_service.py
from database.repositories.genre_repository import GenreRepository

class GenreService:
    def __init__(self):
        self.genre_repo = GenreRepository()

    def get_all_genres(self):
        """Retrieves all genres."""
        return self.genre_repo.get_all_genres()

    def get_genres_for_movie(self, tmdb_id):
        """Retrieves genres for a specific movie."""
        return self.genre_repo.get_genres_for_movie(tmdb_id)

    def get_movies_by_genre(self, genre_name):
        """Retrieves movies for a specific genre."""
        return self.genre_repo.get_movies_by_genre(genre_name)

    def add_genre(self, genre_name):
        """Adds a new genre (Admin functionality)."""
        if not genre_name or len(genre_name.strip()) == 0:
             return {"success": False, "message": "Genre name cannot be empty."}

        success = self.genre_repo.create_genre(genre_name.strip())
        if not success:
            return {"success": False, "message": "Failed to add genre in the database or genre already exists."}

        return {"success": True, "message": "Genre added successfully."}

    def update_genre(self, genre_id, new_genre_name):
        """Updates an existing genre (Admin functionality)."""
        if not new_genre_name or len(new_genre_name.strip()) == 0:
             return {"success": False, "message": "Genre name cannot be empty."}

        success = self.genre_repo.update_genre(genre_id, new_genre_name.strip())
        if not success:
            return {"success": False, "message": "Failed to update genre in the database or genre does not exist."}

        return {"success": True, "message": "Genre updated successfully."}

    def delete_genre(self, genre_id):
        """Deletes a genre (Admin functionality). Note: May fail due to FK constraints."""
        success = self.genre_repo.delete_genre(genre_id)
        if not success:
            return {"success": False, "message": "Failed to delete genre in the database, likely due to existing movie associations."}

        return {"success": True, "message": "Genre deleted successfully."}
