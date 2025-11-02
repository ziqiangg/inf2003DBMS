# database/services/review_service.py
from database.repositories.review_repository import ReviewRepository

class ReviewService:
    def __init__(self):
        self.review_repo = ReviewRepository()

    def add_review(self, user_id, tmdb_id, review_text):
        """Adds or updates a review."""
        if not review_text or len(review_text.strip()) == 0:
             return {"success": False, "message": "Review text cannot be empty."}

        success = self.review_repo.create_review(user_id, tmdb_id, review_text.strip())
        if not success:
            return {"success": False, "message": "Failed to add/update review in the database."}

        return {"success": True, "message": "Review added/updated successfully."}

    def update_review(self, user_id, tmdb_id, new_review_text):
        """Updates an existing review."""
        if not new_review_text or len(new_review_text.strip()) == 0:
             return {"success": False, "message": "Review text cannot be empty."}

        success = self.review_repo.update_review(user_id, tmdb_id, new_review_text.strip())
        if not success:
            return {"success": False, "message": "Failed to update review in the database or review does not exist."}

        return {"success": True, "message": "Review updated successfully."}

    def delete_review(self, user_id, tmdb_id):
        """Deletes a review."""
        success = self.review_repo.delete_review(user_id, tmdb_id)
        if not success:
            return {"success": False, "message": "Failed to delete review in the database or review does not exist."}

        return {"success": True, "message": "Review deleted successfully."}

    def get_user_review_for_movie(self, user_id, tmdb_id):
        """Retrieves a specific user's review for a movie."""
        review = self.review_repo.get_review_by_user_and_movie(user_id, tmdb_id)
        return {
            "success": True,
            "review": review
        }

    def get_reviews_for_movie(self, tmdb_id):
        """Retrieves the 3 most recent reviews for a specific movie."""
        reviews = self.review_repo.get_reviews_for_movie(tmdb_id)
        return {
            "success": True,
            "reviews": reviews
        }

    def get_reviews_for_user(self, user_id):
        """
        Retrieves all reviews written by a specific user, sorted by timestamp descending.
        This method calls the corresponding method in the ReviewRepository.
        """
        reviews = self.review_repo.get_reviews_for_user(user_id)
        return {
            "success": True,
            "reviews": reviews
        }
