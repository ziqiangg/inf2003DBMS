# In rating_service.py
from database.repositories.rating_repository import RatingRepository
from database.repositories.review_repository import ReviewRepository
from database.repositories.movie_repository import MovieRepository
from database.db_connection import get_mysql_connection, close_connection

class RatingService:
    def __init__(self):
        self.rating_repo = RatingRepository()

    def add_rating(self, user_id, tmdb_id, rating_value):
        """Adds or updates a rating and updates the movie's sum and count."""
        if rating_value < 0 or rating_value > 5:
             return {"success": False, "message": "Rating must be between 0 and 5."}

        success = self.rating_repo.create_rating(user_id, tmdb_id, rating_value)
        if not success:
            return {"success": False, "message": "Failed to add/update rating in the database."}

        # Calculate the NEW sum and count from the Ratings table
        sum_ratings, count_ratings = self.rating_repo.get_sum_and_count_ratings_for_movie(tmdb_id)

        # Update the Movies table with the NEW sum and count
        update_movie_query = "UPDATE Movies SET totalRatings = %s, countRatings = %s WHERE tmdbID = %s;"
        connection = get_mysql_connection()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute(update_movie_query, (sum_ratings, count_ratings, tmdb_id))
                connection.commit()
                # print(f"DEBUG: Updated movie {tmdb_id} totalRatings (sum) to {sum_ratings}, countRatings to {count_ratings}")
            except Exception as e:
                print(f"Error updating movie sum/count ratings: {e}")
                connection.rollback()
            finally:
                cursor.close()
                close_connection(connection)
        else:
            print("Error: Could not get database connection to update movie sum/count ratings.")
            # Consider returning failure here if update is critical
        return {"success": True, "message": "Rating added/updated successfully."}

    def update_rating(self, user_id, tmdb_id, new_rating_value):
        """Updates an existing rating and recalculates the movie's sum and count."""
        if new_rating_value < 0 or new_rating_value > 5:
             return {"success": False, "message": "Rating must be between 0 and 5."}

        success = self.rating_repo.update_rating(user_id, tmdb_id, new_rating_value)
        if not success:
            return {"success": False, "message": "Failed to update rating in the database or rating does not exist."}

        # Recalculate the NEW sum and count from the Ratings table
        sum_ratings, count_ratings = self.rating_repo.get_sum_and_count_ratings_for_movie(tmdb_id)

        # Update the Movies table with the NEW sum and count
        update_movie_query = "UPDATE Movies SET totalRatings = %s, countRatings = %s WHERE tmdbID = %s;"
        connection = get_mysql_connection()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute(update_movie_query, (sum_ratings, count_ratings, tmdb_id))
                connection.commit()
            except Exception as e:
                print(f"Error updating movie sum/count ratings: {e}")
                connection.rollback()
            finally:
                cursor.close()
                close_connection(connection)
        else:
            print("Error: Could not get database connection to update movie sum/count ratings.")
            # Consider returning failure here if update is critical
        return {"success": True, "message": "Rating updated successfully."}
    
    def get_user_rating_for_movie(self, user_id, tmdb_id):
        """Retrieves a specific user's rating for a movie."""
        return self.rating_repo.get_rating_by_user_and_movie(user_id, tmdb_id)

    def delete_rating(self, user_id, tmdb_id):
        """Deletes a rating and recalculates the movie's sum and count."""
        success = self.rating_repo.delete_rating(user_id, tmdb_id)
        if not success:
            return {"success": False, "message": "Failed to delete rating in the database or rating does not exist."}

        # Recalculate the NEW sum and count from the Ratings table
        sum_ratings, count_ratings = self.rating_repo.get_sum_and_count_ratings_for_movie(tmdb_id)

        # Update the Movies table with the NEW sum and count
        update_movie_query = "UPDATE Movies SET totalRatings = %s, countRatings = %s WHERE tmdbID = %s;"
        connection = get_mysql_connection()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute(update_movie_query, (sum_ratings, count_ratings, tmdb_id))
                connection.commit()
            except Exception as e:
                print(f"Error updating movie sum/count ratings: {e}")
                connection.rollback()
            finally:
                cursor.close()
                close_connection(connection)
        else:
            print("Error: Could not get database connection to update movie sum/count ratings.")
            # Consider returning failure here if update is critical
        return {"success": True, "message": "Rating deleted successfully."}

    # You might want to update get_movie_average_and_count to reflect the new logic
    def get_movie_average_and_count(self, tmdb_id):
        """Retrieves the sum of ratings and count for a specific movie."""
        # This method name is now misleading if it returns sum and count.
        # Consider renaming it to get_movie_sum_and_count or get_movie_aggregates.
        return self.rating_repo.get_sum_and_count_ratings_for_movie(tmdb_id)

    # a helper method for avg
    def get_movie_average(self, tmdb_id):
        """Calculates and returns the average rating for a specific movie."""
        sum_ratings, count_ratings = self.get_movie_average_and_count(tmdb_id) # Call the renamed method
        if count_ratings > 0:
            return sum_ratings / count_ratings
        else:
            return 0.0 # Or None, depending on desired behavior for unrated movies
    
    #for profile page
    def get_user_ratings_and_reviews_for_profile(self, user_id):
        """
        Retrieves all ratings and reviews for a specific user, combined into a single list
        sorted primarily by rating (descending), then by review timestamp (descending) for movies only reviewed.
        This method now uses the unified query in the RatingRepository for efficiency.
        """
        # Fetch the combined and sorted list directly from the repository using the unified query
        combined_results = self.rating_repo.get_user_ratings_and_reviews_unified(user_id)

        # The repository query returns a list where each item has keys like:
        # {'tmdbID': ..., 'title': ..., 'rating': ..., 'review_text': ..., 'rating_timeStamp': ..., 'review_timeStamp': ...}
        # We just need to return this list, potentially reformatting it slightly to match the old structure
        # if the GUI expects a specific format (e.g., 'type', 'timeStamp', 'review').
        # The unified query already handles the complex sorting.

        processed_list = []
        for item in combined_results:
            processed_item = {
                'tmdbID': item['tmdbID'],
                'title': item['title'],
                # Use 'rating' from the unified result (could be a number or None)
                'rating': item['rating'],
                # Use 'review_text' from the unified result (could be text or None)
                'review': item['review_text'],
                # Decide which timestamp to use based on presence of rating/review
                # Use review_timeStamp if rating is None (meaning it's a review-only entry)
                # Use rating_timeStamp if rating exists (though rating_timeStamp might be NULL in the unified query if Ratings table lacks it)
                'timeStamp': item['review_timeStamp'] if item['rating'] is None else item['rating_timeStamp']
            }
            # Determine the 'type' based on whether rating or review exists
            if item['rating'] is not None:
                processed_item['type'] = 'rating'
            else:
                processed_item['type'] = 'review'

            processed_list.append(processed_item)

        # The sorting is already done by the SQL query, so the processed_list is correctly ordered.
        return processed_list