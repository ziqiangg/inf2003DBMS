# In rating_service.py
from database.repositories.rating_repository import RatingRepository
from database.services.review_service import ReviewService  
from database.services.movie_service import MovieService   

import threading

class RatingService:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(RatingService, cls).__new__(cls)
                    cls._instance.rating_repo = RatingRepository()
                    cls._instance.review_service = ReviewService()
                    cls._instance.movie_service = MovieService()
        return cls._instance

    def add_rating(self, user_id, tmdb_id, rating_value):
        """Adds or updates a rating (repository now handles atomic updates)."""
        # Validation
        if rating_value < 0 or rating_value > 5:
            return {"success": False, "message": "Rating must be between 0 and 5."}
        
        # Repository handles transaction and aggregate update
        success = self.rating_repo.create_rating(user_id, tmdb_id, rating_value)
        
        if not success:
            return {"success": False, "message": "Failed to add/update rating in the database."}
        
        return {"success": True, "message": "Rating added/updated successfully."}

    def update_rating(self, user_id, tmdb_id, new_rating_value):
        """Updates an existing rating (repository now handles atomic updates)."""
        # Validation
        if new_rating_value < 0 or new_rating_value > 5:
            return {"success": False, "message": "Rating must be between 0 and 5."}
        
        # Repository handles transaction and aggregate update
        success = self.rating_repo.update_rating(user_id, tmdb_id, new_rating_value)
        
        if not success:
            return {"success": False, "message": "Failed to update rating or rating does not exist."}
        
        return {"success": True, "message": "Rating updated successfully."}
    
    def get_user_rating_for_movie(self, user_id, tmdb_id):
        """Retrieves a specific user's rating for a movie."""
        rating = self.rating_repo.get_rating_by_user_and_movie(user_id, tmdb_id)
        return {
            "success": True,
            "rating": rating
        }

    def delete_rating(self, user_id, tmdb_id):
        """Deletes a rating (repository now handles atomic updates)."""
        # Repository handles transaction and aggregate update
        success = self.rating_repo.delete_rating(user_id, tmdb_id)
        
        if not success:
            return {"success": False, "message": "Failed to delete rating or rating does not exist."}
        
        # Also delete associated review if exists
        review = self.review_service.get_user_review_for_movie(user_id, tmdb_id)
        if review:
            self.review_service.delete_review(user_id, tmdb_id)
        
        return {"success": True, "message": "Rating (and review if present) deleted successfully."}

    def get_movie_average_and_count(self, tmdb_id):
        """Retrieves the sum of ratings and count for a specific movie."""
        sum_ratings, count_ratings = self.rating_repo.get_sum_and_count_ratings_for_movie(tmdb_id)
        
        # Wrap the result consistently
        avg_rating = (sum_ratings / count_ratings) if count_ratings > 0 else 0.0
        
        return {
            "success": True,
            "sum_ratings": sum_ratings,
            "count_ratings": count_ratings,
            "average_rating": avg_rating  # Add computed average for convenience
        }

    def get_movie_average(self, tmdb_id):
        """Calculates and returns the average rating for a specific movie."""
        sum_ratings, count_ratings = self.get_movie_average_and_count(tmdb_id)
        if count_ratings > 0:
            avg = sum_ratings / count_ratings
        else:
            avg = 0.0
        
        return {
            "success": True,
            "average_rating": avg,
            "count": count_ratings
        }

    def get_user_ratings_and_reviews_for_profile(self, user_id):
        """Retrieves all ratings and reviews for a specific user, combined into a single list."""
        print(f"DEBUG: RatingService.get_user_ratings_and_reviews_for_profile: Called for userID {user_id}")
        
        combined_results = self.rating_repo.get_user_ratings_and_reviews_unified(user_id)
        
        print(f"DEBUG: RatingService.get_user_ratings_and_reviews_for_profile: Received {len(combined_results)} results from repository")

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

        print(f"DEBUG: RatingService.get_user_ratings_and_reviews_for_profile: Processed {len(processed_list)} items")
        
        return {
            "success": True,
            "interactions": processed_list
        }