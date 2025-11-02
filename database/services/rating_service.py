# In rating_service.py
from database.repositories.rating_repository import RatingRepository
from database.services.review_service import ReviewService  
from database.services.movie_service import MovieService   

class RatingService:
    def __init__(self):
        self.rating_repo = RatingRepository()
        self.review_service = ReviewService()  
        self.movie_service = MovieService()    

    def _update_movie_aggregates(self, tmdb_id):
        """Helper method to recalculate and update movie rating aggregates.
        
        Args:
            tmdb_id (int): The movie's tmdbID
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Calculate the NEW sum and count from the Ratings table
        sum_ratings, count_ratings = self.rating_repo.get_sum_and_count_ratings_for_movie(tmdb_id)

        # Update through the proper service layer
        result = self.movie_service.update_movie_aggregates(tmdb_id, sum_ratings, count_ratings)
        
        if not result["success"]:
            print(f"Warning: Failed to update aggregates for movie {tmdb_id}")
            return False
        
        return True

    def add_rating(self, user_id, tmdb_id, rating_value):
        """Adds or updates a rating and updates the movie's sum and count."""
        if rating_value < 0 or rating_value > 5:
            return {"success": False, "message": "Rating must be between 0 and 5."}

        success = self.rating_repo.create_rating(user_id, tmdb_id, rating_value)
        if not success:
            return {"success": False, "message": "Failed to add/update rating in the database."}

        # Update movie aggregates through proper service layer
        if not self._update_movie_aggregates(tmdb_id):
            # Rating was saved but aggregates failed to update
            # Consider if this should return failure or just log warning
            print(f"Warning: Rating saved but failed to update movie {tmdb_id} aggregates")
        
        return {"success": True, "message": "Rating added/updated successfully."}

    def update_rating(self, user_id, tmdb_id, new_rating_value):
        """Updates an existing rating and recalculates the movie's sum and count."""
        if new_rating_value < 0 or new_rating_value > 5:
            return {"success": False, "message": "Rating must be between 0 and 5."}

        success = self.rating_repo.update_rating(user_id, tmdb_id, new_rating_value)
        if not success:
            return {"success": False, "message": "Failed to update rating in the database or rating does not exist."}

        # Update movie aggregates through proper service layer
        if not self._update_movie_aggregates(tmdb_id):
            print(f"Warning: Rating updated but failed to update movie {tmdb_id} aggregates")
        
        return {"success": True, "message": "Rating updated successfully."}
    
    def get_user_rating_for_movie(self, user_id, tmdb_id):
        """Retrieves a specific user's rating for a movie."""
        return self.rating_repo.get_rating_by_user_and_movie(user_id, tmdb_id)

    def delete_rating(self, user_id, tmdb_id):
        """Deletes a rating and recalculates the movie's sum and count."""
        success = self.rating_repo.delete_rating(user_id, tmdb_id)
        if not success:
            return {"success": False, "message": "Failed to delete rating in the database or rating does not exist."}

        # Update movie aggregates through proper service layer
        if not self._update_movie_aggregates(tmdb_id):
            print(f"Warning: Rating deleted but failed to update movie {tmdb_id} aggregates")
        
        return {"success": True, "message": "Rating deleted successfully."}

    def get_movie_average_and_count(self, tmdb_id):
        """Retrieves the sum of ratings and count for a specific movie."""
        return self.rating_repo.get_sum_and_count_ratings_for_movie(tmdb_id)

    def get_movie_average(self, tmdb_id):
        """Calculates and returns the average rating for a specific movie."""
        sum_ratings, count_ratings = self.get_movie_average_and_count(tmdb_id)
        if count_ratings > 0:
            return sum_ratings / count_ratings
        else:
            return 0.0
    
    def get_user_ratings_and_reviews_for_profile(self, user_id):
        """
        Retrieves all ratings and reviews for a specific user, combined into a single list
        sorted primarily by rating (descending), then by review timestamp (descending) for movies only reviewed.
        """
        combined_results = self.rating_repo.get_user_ratings_and_reviews_unified(user_id)

        processed_list = []
        for item in combined_results:
            processed_item = {
                'tmdbID': item['tmdbID'],
                'title': item['title'],
                'rating': item['rating'],
                'review': item['review_text'],
                'timeStamp': item['review_timeStamp'] if item['rating'] is None else item['rating_timeStamp']
            }
            
            if item['rating'] is not None:
                processed_item['type'] = 'rating'
            else:
                processed_item['type'] = 'review'

            processed_list.append(processed_item)

        return processed_list