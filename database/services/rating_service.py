# database/services/rating_service.py
from database.repositories.rating_repository import RatingRepository
from database.repositories.movie_repository import MovieRepository
from database.db_connection import get_mysql_connection, close_connection

class RatingService:
    def __init__(self):
        self.rating_repo = RatingRepository()

    def add_rating(self, user_id, tmdb_id, rating_value):
        """Adds or updates a rating and updates the movie's average."""
        if rating_value < 0 or rating_value > 5:
             return {"success": False, "message": "Rating must be between 0 and 5."}

        # Create or update the rating record
        success = self.rating_repo.create_rating(user_id, tmdb_id, rating_value)
        if not success:
            return {"success": False, "message": "Failed to add/update rating in the database."}

        # Calculate and update the movie's average rating
        avg_rating, count_rating = self.rating_repo.get_average_rating_for_movie(tmdb_id)
        update_movie_query = "UPDATE Movies SET totalRatings = %s, countRatings = %s WHERE tmdbID = %s;"
        connection = get_mysql_connection()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute(update_movie_query, (avg_rating, count_rating, tmdb_id))
                connection.commit()
                # print(f"DEBUG: Updated movie {tmdb_id} average rating to {avg_rating}, count {count_rating}") # Optional debug print
            except Exception as e:
                print(f"Error updating movie average rating: {e}")
                connection.rollback()
            finally:
                cursor.close()
                close_connection(connection)

        return {"success": True, "message": "Rating added/updated successfully."}

    def update_rating(self, user_id, tmdb_id, new_rating_value):
        """Updates an existing rating and recalculates the movie's average."""
        if new_rating_value < 0 or new_rating_value > 5:
             return {"success": False, "message": "Rating must be between 0 and 5."}

        success = self.rating_repo.update_rating(user_id, tmdb_id, new_rating_value)
        if not success:
            return {"success": False, "message": "Failed to update rating in the database or rating does not exist."}

        # Recalculate and update the movie's average rating
        avg_rating, count_rating = self.rating_repo.get_average_rating_for_movie(tmdb_id)
        update_movie_query = "UPDATE Movies SET totalRatings = %s, countRatings = %s WHERE tmdbID = %s;"
        connection = get_mysql_connection()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute(update_movie_query, (avg_rating, count_rating, tmdb_id))
                connection.commit()
            except Exception as e:
                print(f"Error updating movie average rating: {e}")
                connection.rollback()
            finally:
                cursor.close()
                close_connection(connection)

        return {"success": True, "message": "Rating updated successfully."}

    def delete_rating(self, user_id, tmdb_id):
        """Deletes a rating and recalculates the movie's average."""
        success = self.rating_repo.delete_rating(user_id, tmdb_id)
        if not success:
            return {"success": False, "message": "Failed to delete rating in the database or rating does not exist."}

        # Recalculate and update the movie's average rating after deletion
        avg_rating, count_rating = self.rating_repo.get_average_rating_for_movie(tmdb_id)
        update_movie_query = "UPDATE Movies SET totalRatings = %s, countRatings = %s WHERE tmdbID = %s;"
        connection = get_mysql_connection()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute(update_movie_query, (avg_rating, count_rating, tmdb_id))
                connection.commit()
            except Exception as e:
                print(f"Error updating movie average rating: {e}")
                connection.rollback()
            finally:
                cursor.close()
                close_connection(connection)

        return {"success": True, "message": "Rating deleted successfully."}

    def get_user_rating_for_movie(self, user_id, tmdb_id):
        """Retrieves a specific user's rating for a movie."""
        return self.rating_repo.get_rating_by_user_and_movie(user_id, tmdb_id)

    def get_all_ratings_for_movie(self, tmdb_id):
        """Retrieves all ratings for a specific movie."""
        return self.rating_repo.get_ratings_for_movie(tmdb_id)

    def get_movie_average_and_count(self, tmdb_id):
        """Retrieves the average rating and count for a specific movie."""
        return self.rating_repo.get_average_rating_for_movie(tmdb_id)
