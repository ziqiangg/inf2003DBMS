# database/repositories/genre_repository.py
from database.db_connection import MySQLConnectionManager
from database.sql_queries import (
    GET_ALL_GENRES, GET_GENRES_FOR_MOVIE, GET_MOVIES_BY_GENRE,
    INSERT_GENRE
)
import threading

class GenreRepository:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(GenreRepository, cls).__new__(cls)
                    cls._instance.db_manager = MySQLConnectionManager()
        return cls._instance

    def get_all_genres(self):
        """Fetches all genres ordered by name."""
        connection = self.db_manager.get_connection()
        if not connection:
            return []

        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(GET_ALL_GENRES)
            genres = cursor.fetchall()
            return genres
        except Exception as e:
            print(f"Error fetching all genres: {e}")
            return []
        finally:
            cursor.close()
            self.db_manager.close_connection(connection)

    def get_genres_for_movie(self, tmdb_id):
        """Fetches genres associated with a specific movie."""
        connection = self.db_manager.get_connection()
        if not connection:
            return []

        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(GET_GENRES_FOR_MOVIE, (tmdb_id,))
            genres = cursor.fetchall()
            return genres
        except Exception as e:
            print(f"Error fetching genres for movie {tmdb_id}: {e}")
            return []
        finally:
            cursor.close()
            self.db_manager.close_connection(connection)

    def get_movies_by_genre(self, genre_name):
        """Fetches movies associated with a specific genre."""
        connection = self.db_manager.get_connection()
        if not connection:
            return []

        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(GET_MOVIES_BY_GENRE, (genre_name,))
            movies = cursor.fetchall()
            return movies
        except Exception as e:
            print(f"Error fetching movies for genre {genre_name}: {e}")
            return []
        finally:
            cursor.close()
            self.db_manager.close_connection(connection)

    def create_genre(self, genre_name):
        """Inserts a new genre."""
        connection = self.db_manager.get_connection()
        if not connection:
            return False

        cursor = connection.cursor()
        try:
            cursor.execute(INSERT_GENRE, (genre_name,))
            connection.commit()
            return cursor.rowcount > 0 # Returns True if a row was inserted
        except Exception as e:
            print(f"Error creating genre: {e}")
            connection.rollback()
            return False
        finally:
            cursor.close()
            self.db_manager.close_connection(connection)

    #should technically not be possible to update genre names
    # def update_genre(self, genre_id, new_genre_name):
    #     """Updates an existing genre."""
    #     connection = get_mysql_connection()
    #     if not connection:
    #         return False

    #     cursor = connection.cursor()
    #     try:
    #         cursor.execute(UPDATE_GENRE, (new_genre_name, genre_id))
    #         connection.commit()
    #         return cursor.rowcount > 0 # Returns True if a row was updated
    #     except Exception as e:
    #         print(f"Error updating genre: {e}")
    #         connection.rollback()
    #         return False
    #     finally:
    #         cursor.close()
    #         close_connection(connection)

    # def delete_genre(self, genre_id):
    #     """Deletes a genre. Note: This might fail due to foreign key constraints."""
    #     connection = get_mysql_connection()
    #     if not connection:
    #         return False

    #     cursor = connection.cursor()
    #     try:
    #         cursor.execute(DELETE_GENRE, (genre_id,))
    #         connection.commit()
    #         return cursor.rowcount > 0 # Returns True if a row was deleted
    #     except Exception as e:
    #         print(f"Error deleting genre: {e}")
    #         connection.rollback()
    #         return False
    #     finally:
    #         cursor.close()
    #         close_connection(connection)
