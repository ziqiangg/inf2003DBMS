# database/repositories/rating_repository.py
from database.db_connection import get_mysql_connection, close_connection
from database.sql_queries import (
    INSERT_RATING, UPDATE_RATING, DELETE_RATING,
    GET_RATING_BY_USER_AND_MOVIE, GET_RATINGS_FOR_MOVIE, GET_AVERAGE_RATING_FOR_MOVIE
)

class RatingRepository:
    def __init__(self):
        pass

    def create_rating(self, user_id, tmdb_id, rating):
        """Inserts a new rating or updates if it exists."""
        connection = get_mysql_connection()
        if not connection:
            return False

        cursor = connection.cursor()
        try:
            cursor.execute(INSERT_RATING, (user_id, tmdb_id, rating))
            connection.commit()
            # For INSERT ... ON DUPLICATE KEY UPDATE:
            # - rowcount = 1: New row inserted
            # - rowcount = 2: Row updated (rare for this query)
            # - rowcount = 0: Row updated to same value (no change)
            # All indicate the desired state is achieved, so success if no exception.
            # Using rowcount >= 0 correctly reflects this outcome based on the query's behavior.
            return cursor.rowcount >= 0
        except Exception as e:
            print(f"Error creating/updating rating: {e}")
            connection.rollback()
            return False
        finally:
            cursor.close()
            close_connection(connection)

    def update_rating(self, user_id, tmdb_id, new_rating):
        """Updates an existing rating."""
        connection = get_mysql_connection()
        if not connection:
            return False

        cursor = connection.cursor()
        try:
            cursor.execute(UPDATE_RATING, (new_rating, user_id, tmdb_id))
            connection.commit()
            # For a standard UPDATE:
            # - rowcount = 1: Exactly one row was updated (success)
            # - rowcount = 0: No rows matched the WHERE clause (rating didn't exist, failure)
            # - rowcount > 1: Should not happen with composite PK (userID, tmdbID)
            # We only consider it a success if an existing row was actually modified.
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating rating: {e}")
            connection.rollback()
            return False
        finally:
            cursor.close()
            close_connection(connection)

    def delete_rating(self, user_id, tmdb_id):
        """Deletes a rating."""
        connection = get_mysql_connection()
        if not connection:
            return False

        cursor = connection.cursor()
        try:
            cursor.execute(DELETE_RATING, (user_id, tmdb_id))
            connection.commit()
            # For DELETE:
            # - rowcount = 1: Exactly one row was deleted (success)
            # - rowcount = 0: No rows matched the WHERE clause (rating didn't exist, failure)
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting rating: {e}")
            connection.rollback()
            return False
        finally:
            cursor.close()
            close_connection(connection)

    def get_rating_by_user_and_movie(self, user_id, tmdb_id):
        """Fetches a specific rating by user and movie."""
        connection = get_mysql_connection()
        if not connection:
            return None

        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(GET_RATING_BY_USER_AND_MOVIE, (user_id, tmdb_id))
            rating = cursor.fetchone()
            return rating
        except Exception as e:
            print(f"Error fetching rating: {e}")
            return None
        finally:
            cursor.close()
            close_connection(connection)

    def get_ratings_for_movie(self, tmdb_id):
        """Fetches all ratings for a specific movie."""
        connection = get_mysql_connection()
        if not connection:
            return []

        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(GET_RATINGS_FOR_MOVIE, (tmdb_id,))
            ratings = cursor.fetchall()
            return ratings
        except Exception as e:
            print(f"Error fetching ratings for movie: {e}")
            return []
        finally:
            cursor.close()
            close_connection(connection)

    def get_average_rating_for_movie(self, tmdb_id):
        """Fetches the average rating and count for a specific movie."""
        connection = get_mysql_connection()
        if not connection:
            return 0.0, 0

        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(GET_AVERAGE_RATING_FOR_MOVIE, (tmdb_id,))
            result = cursor.fetchone()
            avg_rating = result['avg_rating'] if result['avg_rating'] is not None else 0.0
            count_rating = result['rating_count'] if result['rating_count'] is not None else 0
            return float(avg_rating), int(count_rating)
        except Exception as e:
            print(f"Error fetching average rating for movie: {e}")
            return 0.0, 0
        finally:
            cursor.close()
            close_connection(connection)
