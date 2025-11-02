# database/repositories/rating_repository.py
from database.db_connection import MySQLConnectionManager
from database.sql_queries import (
    GET_USER_RATINGS_AND_REVIEWS_UNIFIED, INSERT_RATING, UPDATE_RATING, DELETE_RATING,
    GET_RATING_BY_USER_AND_MOVIE, GET_RATINGS_FOR_MOVIE,
    GET_SUM_AND_COUNT_RATINGS_FOR_MOVIE, GET_USER_RATINGS,
    UPDATE_MOVIE_AGGREGATES_ATOMIC  # Add this import
)
import threading

class RatingRepository:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(RatingRepository, cls).__new__(cls)
                    cls._instance.db_manager = MySQLConnectionManager()
        return cls._instance

    def create_rating(self, user_id, tmdb_id, rating):
        """Inserts a new rating or updates if it exists, with atomic aggregate update."""
        connection = self.db_manager.get_connection()
        if not connection:
            return False

        cursor = connection.cursor()
        try:
            # Start transaction
            connection.start_transaction()
            
            # 1. Insert/update the rating
            cursor.execute(INSERT_RATING, (user_id, tmdb_id, rating))
            
            # 2. Recalculate and update aggregates atomically
            cursor.execute(UPDATE_MOVIE_AGGREGATES_ATOMIC, (tmdb_id, tmdb_id, tmdb_id))
            
            # Commit both operations together
            connection.commit()
            return True
            
        except Exception as e:
            print(f"Error creating/updating rating: {e}")
            connection.rollback()
            return False
        finally:
            cursor.close()
            self.db_manager.close_connection(connection)

    def update_rating(self, user_id, tmdb_id, new_rating):
        """Updates an existing rating with atomic aggregate update."""
        connection = self.db_manager.get_connection()
        if not connection:
            return False

        cursor = connection.cursor()
        try:
            # Start transaction
            connection.start_transaction()
            
            # 1. Update the rating
            cursor.execute(UPDATE_RATING, (new_rating, user_id, tmdb_id))
            
            # Check if update was successful
            if cursor.rowcount == 0:
                connection.rollback()
                return False
            
            # 2. Recalculate and update aggregates atomically
            cursor.execute(UPDATE_MOVIE_AGGREGATES_ATOMIC, (tmdb_id, tmdb_id, tmdb_id))
            
            # Commit both operations together
            connection.commit()
            return True
            
        except Exception as e:
            print(f"Error updating rating: {e}")
            connection.rollback()
            return False
        finally:
            cursor.close()
            self.db_manager.close_connection(connection)

    def delete_rating(self, user_id, tmdb_id):
        """Deletes a rating with atomic aggregate update."""
        connection = self.db_manager.get_connection()
        if not connection:
            return False

        cursor = connection.cursor()
        try:
            # Start transaction
            connection.start_transaction()
            
            # 1. Delete the rating
            cursor.execute(DELETE_RATING, (user_id, tmdb_id))
            
            # Check if deletion was successful
            if cursor.rowcount == 0:
                connection.rollback()
                return False
            
            # 2. Recalculate and update aggregates atomically
            cursor.execute(UPDATE_MOVIE_AGGREGATES_ATOMIC, (tmdb_id, tmdb_id, tmdb_id))
            
            # Commit both operations together
            connection.commit()
            return True
            
        except Exception as e:
            print(f"Error deleting rating: {e}")
            connection.rollback()
            return False
        finally:
            cursor.close()
            self.db_manager.close_connection(connection)

    def get_rating_by_user_and_movie(self, user_id, tmdb_id):
        """Fetches a specific rating by user and movie."""
        connection = self.db_manager.get_connection()
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
            self.db_manager.close_connection(connection)

    def get_ratings_for_movie(self, tmdb_id):
        """Fetches all ratings for a specific movie."""
        connection = self.db_manager.get_connection()
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
            self.db_manager.close_connection(connection)

    def get_sum_and_count_ratings_for_movie(self, tmdb_id):
        """Fetches the sum and count of ratings for a specific movie."""
        connection = self.db_manager.get_connection()
        if not connection:
            return 0.0, 0 # Return 0 for sum and 0 for count if connection fails
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(GET_SUM_AND_COUNT_RATINGS_FOR_MOVIE, (tmdb_id,))
            result = cursor.fetchone()
            sum_rating = result['sum_ratings'] if result['sum_ratings'] is not None else 0.0
            count_rating = result['rating_count'] if result['rating_count'] is not None else 0
            return float(sum_rating), int(count_rating) # Ensure correct types
        except Exception as e:
            print(f"Error fetching sum and count ratings for movie {tmdb_id}: {e}")
            return 0.0, 0 # Return 0 for sum and 0 for count on error
        finally:
            cursor.close()
            self.db_manager.close_connection(connection)

    def get_ratings_for_user_sorted_by_rating(self, user_id):
        """
        Fetches all ratings for a specific user, including movie titles, sorted by rating descending.
        This method uses the existing GET_USER_RATINGS query.
        """
        connection = self.db_manager.get_connection()
        if not connection:
            return []

        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(GET_USER_RATINGS, (user_id,))
            ratings = cursor.fetchall()
            return ratings
        except Exception as e:
            print(f"Error fetching ratings for user {user_id}: {e}")
            return []
        finally:
            cursor.close()
            self.db_manager.close_connection(connection)

    #for profile page
    def get_user_ratings_and_reviews_unified(self, user_id):
        """Fetches all ratings and reviews for a specific user, unified into a single list."""
        connection = self.db_manager.get_connection()
        if not connection:
            print(f"ERROR: RatingRepository.get_user_ratings_and_reviews_unified: No connection for userID {user_id}")
            return []

        cursor = connection.cursor(dictionary=True)
        try:
            print(f"DEBUG: RatingRepository.get_user_ratings_and_reviews_unified: Executing query for userID {user_id}")
            print(f"DEBUG: Query: {GET_USER_RATINGS_AND_REVIEWS_UNIFIED}")
            print(f"DEBUG: Parameters: ({user_id}, {user_id}, {user_id})")
            
            # Execute the unified query, passing the user_id three times for the subquery
            cursor.execute(GET_USER_RATINGS_AND_REVIEWS_UNIFIED, (user_id, user_id, user_id))
            results = cursor.fetchall()
            
            print(f"DEBUG: RatingRepository.get_user_ratings_and_reviews_unified: Query returned {len(results)} rows")
            if len(results) > 0:
                print(f"DEBUG: First result: {results[0]}")
            else:
                print(f"DEBUG: No results returned from database for userID {user_id}")
                
                # Additional debugging - check if user has any ratings at all
                cursor.execute("SELECT COUNT(*) as count FROM Ratings WHERE userID = %s", (user_id,))
                rating_count = cursor.fetchone()
                print(f"DEBUG: User has {rating_count['count']} total ratings in Ratings table")
                
                # Check if user has any reviews
                cursor.execute("SELECT COUNT(*) as count FROM Reviews WHERE userID = %s", (user_id,))
                review_count = cursor.fetchone()
                print(f"DEBUG: User has {review_count['count']} total reviews in Reviews table")
            
            return results
        except Exception as e:
            print(f"ERROR: RatingRepository.get_user_ratings_and_reviews_unified: Exception for userID {user_id}: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            cursor.close()
            self.db_manager.close_connection(connection)
