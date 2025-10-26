# database/repositories/review_repository.py
from database.db_connection import get_mysql_connection, close_connection
from database.sql_queries import (
    INSERT_REVIEW, UPDATE_REVIEW, DELETE_REVIEW,
    GET_REVIEW_BY_USER_AND_MOVIE, GET_REVIEWS_FOR_MOVIE, 
    GET_USER_REVIEWS
)

class ReviewRepository:
    def __init__(self):
        pass

    def create_review(self, user_id, tmdb_id, review_text):
        """Inserts a new review or updates if it exists."""
        connection = get_mysql_connection()
        if not connection:
            return False

        cursor = connection.cursor()
        try:
            cursor.execute(INSERT_REVIEW, (user_id, tmdb_id, review_text))
            connection.commit()
            # For INSERT ... ON DUPLICATE KEY UPDATE:
            # - rowcount = 1: New row inserted
            # - rowcount = 2: Row updated (rare for this query structure)
            # - rowcount = 0: Row updated to same value (no change)
            # All indicate the desired state is achieved, so success if no exception.
            return cursor.rowcount >= 0
        except Exception as e:
            print(f"Error creating/updating review: {e}")
            connection.rollback()
            return False
        finally:
            cursor.close()
            close_connection(connection)

    def update_review(self, user_id, tmdb_id, new_review_text):
        """Updates an existing review."""
        connection = get_mysql_connection()
        if not connection:
            return False

        cursor = connection.cursor()
        try:
            cursor.execute(UPDATE_REVIEW, (new_review_text, user_id, tmdb_id))
            connection.commit()
            return cursor.rowcount > 0 # Returns True if a row was updated (must exist and value changed)
        except Exception as e:
            print(f"Error updating review: {e}")
            connection.rollback()
            return False
        finally:
            cursor.close()
            close_connection(connection)

    def delete_review(self, user_id, tmdb_id):
        """Deletes a review."""
        connection = get_mysql_connection()
        if not connection:
            return False

        cursor = connection.cursor()
        try:
            cursor.execute(DELETE_REVIEW, (user_id, tmdb_id))
            connection.commit()
            return cursor.rowcount > 0 # Returns True if a row was deleted
        except Exception as e:
            print(f"Error deleting review: {e}")
            connection.rollback()
            return False
        finally:
            cursor.close()
            close_connection(connection)

    def get_review_by_user_and_movie(self, user_id, tmdb_id):
        """Fetches a specific review by user and movie."""
        connection = get_mysql_connection()
        if not connection:
            return None

        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(GET_REVIEW_BY_USER_AND_MOVIE, (user_id, tmdb_id))
            review = cursor.fetchone()
            return review
        except Exception as e:
            print(f"Error fetching review: {e}")
            return None
        finally:
            cursor.close()
            close_connection(connection)

    def get_reviews_for_movie(self, tmdb_id):
        """Fetches the 3 most recent reviews for a specific movie."""
        connection = get_mysql_connection()
        if not connection:
            return []

        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(GET_REVIEWS_FOR_MOVIE, (tmdb_id,))
            reviews = cursor.fetchall()
            return reviews
        except Exception as e:
            print(f"Error fetching reviews for movie: {e}")
            return []
        finally:
            cursor.close()
            close_connection(connection)

    def get_reviews_for_user(self, user_id):
        """
        Fetches all reviews written by a specific user, sorted by timestamp descending.
        This method uses the existing GET_USER_REVIEWS query.
        """
        connection = get_mysql_connection()
        if not connection:
            return []

        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(GET_USER_REVIEWS, (user_id,))
            reviews = cursor.fetchall()
            return reviews
        except Exception as e:
            print(f"Error fetching reviews for user {user_id}: {e}")
            return []
        finally:
            cursor.close()
            close_connection(connection)
