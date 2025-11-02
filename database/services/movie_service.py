# database/services/movie_service.py

from database.repositories.movie_repository import MovieRepository

class MovieService:
    def __init__(self):
        self.movie_repo = MovieRepository()
        
    def create_movie(self, movie_data):
        """Creates a new movie with associated genres.
    
        Args:
            movie_data (dict): Dictionary containing movie information
        
        Returns:
            dict: Result of the operation with success status and movie_id
        """
        # Validate required fields
        required_fields = ["title", "runtime", "releaseDate", "genres"]
        for field in required_fields:
            if field not in movie_data or not movie_data[field]:
                return {
                    "success": False,
                    "message": f"Missing required field: {field}"
                }
    
        # Additional validation
        if movie_data["runtime"] < 0:
            return {
                "success": False,
                "message": "Runtime cannot be negative"
            }
        
        if not isinstance(movie_data["genres"], list) or len(movie_data["genres"]) == 0:
            return {
                "success": False,
                "message": "At least one genre must be specified"
            }
        
        # Create the movie - repository returns tmdb_id or None
        tmdb_id = self.movie_repo.create_movie(movie_data)
    
        if tmdb_id:
            return {
                "success": True,
                "message": "Movie created successfully",
                "movie_id": tmdb_id  # Return the new tmdb_id
            }
        else:
            return {
                "success": False,
                "message": "Failed to create movie in database"
            }

    def get_movies_for_homepage(self, page_number=1, movies_per_page=20, max_pages=10):
        """
        Retrieves movies for the homepage with pagination constraints.
        Limits the total number of pages to max_pages.
        """
        # Validate inputs
        if page_number < 1:
            page_number = 1
        if movies_per_page < 1:
            movies_per_page = 20 # Default

        # Calculate the maximum possible page number based on total movies
        total_movies = self.movie_repo.count_all_movies()
        total_pages = (total_movies + movies_per_page - 1) // movies_per_page # Ceiling division

        # Apply the maximum pages constraint
        max_possible_page = min(max_pages, total_pages)
        if page_number > max_possible_page:
             page_number = max_possible_page # Navigate to last allowed page if requested page is too high

        # Fetch the movies for the calculated page number
        movies = self.movie_repo.get_movies_paginated(page_number, movies_per_page)

        # Calculate the range of pages to display in the UI (e.g., 1-10)
        start_page = max(1, page_number - 4) # Show 4 pages before current
        end_page = min(max_possible_page, start_page + 9) # Show up to 10 pages total
        # Ensure we always show 10 pages if possible within max_pages
        if end_page - start_page < 9 and start_page > 1:
            start_page = max(1, end_page - 9)

        page_numbers_to_show = list(range(start_page, end_page + 1))

        return {
            "movies": movies,
            "current_page": page_number,
            "total_pages": max_possible_page, # Use the constrained total
            "page_numbers": page_numbers_to_show,
            "has_next": page_number < max_possible_page,
            "has_prev": page_number > 1
        }

    def get_movie_detail(self, tmdb_id):
        """Retrieves details for a specific movie."""
        movie = self.movie_repo.get_movie_by_id(tmdb_id)
        if movie:
            return {
                "success": True,
                "movie": movie
            }
        else:
            return {
                "success": False,
                "message": "Movie not found"
            }

    def search_movies_by_title(self, search_term=None, genre=None, year=None, min_avg_rating=None, page_number=1, movies_per_page=20, max_pages=10):
        """Searches for movies by title with pagination, optionally filtering by genre, year and/or minimum average rating.

        Args:
            search_term (str, optional): Movie title to search for.
            genre (str, optional): Genre to filter by.
            year (int or tuple, optional): Year or (start_year, end_year) tuple to filter by.
            min_avg_rating (float, optional): Minimum average rating (e.g., 3.0 for 3+).
            page_number (int): Page number to retrieve (default: 1)
            movies_per_page (int): Number of movies per page (default: 20)
            max_pages (int): Maximum number of pages to allow (default: 10)

        Note:
            The year parameter can be:
            - int: Single year to match exactly
            - tuple: (start_year, end_year) for a range search
            - None: No year filtering

        Returns:
            dict: Dictionary containing:
                - movies: List of movies for the current page
                - current_page: Current page number
                - total_pages: Total number of pages
                - has_next: Whether there are more pages
                - has_prev: Whether there are previous pages
        """
        # Normalize year parameter for both count and search
        year_param = None
        if isinstance(year, (tuple, list)) and len(year) == 2:
            # It's a range, pass it through as is
            year_param = year
        elif year is not None:
            # Single year, ensure it's an integer
            try:
                year_param = int(year)
            except (TypeError, ValueError):
                year_param = None
        
        # Get total count of matching movies first
        total_movies = self.movie_repo.count_search_results(search_term, genre, year_param, min_avg_rating)
        
        # Calculate total pages
        total_pages = (total_movies + movies_per_page - 1) // movies_per_page
        
        # Apply max pages constraint
        max_possible_page = min(max_pages, total_pages)
        if page_number > max_possible_page:
            page_number = max_possible_page
        
        # Get paginated results
        movies = self.movie_repo.search_movies(
            search_term=search_term,
            genre=genre,
            year=year_param,
            min_avg_rating=min_avg_rating,
            offset=(page_number - 1) * movies_per_page,
            limit=movies_per_page
        )
        
        return {
            "movies": movies,
            "current_page": page_number,
            "total_pages": max_possible_page,
            "has_next": page_number < max_possible_page,
            "has_prev": page_number > 1
        }

    def get_movie_stats(self, tmdb_id):
        """Gets statistics about a movie's ratings and reviews.

        Args:
            tmdb_id (int): The tmdbID of the movie
    
        Returns:
            dict: Dictionary containing success status and stats
        """
        stats = self.movie_repo.get_movie_stats(tmdb_id)
        return {
            "success": True,
            "rating_count": stats.get('rating_count', 0),
            "review_count": stats.get('review_count', 0)
        }

    def get_available_years(self):
        """Returns list of available release years from the repository."""
        years = self.movie_repo.get_available_years()
        return {
            "success": True,
            "years": years
        }

    def update_movie(self, movie_data):
        """Updates an existing movie with associated genres.
    
        Args:
            movie_data (dict): Dictionary containing movie information including tmdbID
        
        Returns:
            dict: Result of the operation with success status
        """
        # Validate required fields
        if "tmdbID" not in movie_data:
            return {
                "success": False,
                "message": "Missing tmdbID for update operation"
            }
    
        required_fields = ["title", "runtime", "releaseDate", "genres"]
        for field in required_fields:
            if field not in movie_data or movie_data[field] is None:
                return {
                    "success": False,
                    "message": f"Missing required field: {field}"
                }
    
        # Additional validation
        if movie_data["runtime"] < 0:
            return {
                "success": False,
                "message": "Runtime cannot be negative"
            }
        
        if not isinstance(movie_data["genres"], list) or len(movie_data["genres"]) == 0:
            return {
                "success": False,
                "message": "At least one genre must be specified"
            }
    
        # Update the movie - repository returns True/False
        success = self.movie_repo.update_movie(movie_data)
    
        if success:
            return {
                "success": True,
                "message": "Movie updated successfully",
                "movie_id": movie_data["tmdbID"]
            }
        else:
            return {
                "success": False,
                "message": "Failed to update movie in database"
            }

    def delete_movie(self, tmdb_id):
        """Deletes a movie and all associated data.
        
        Args:
            tmdb_id (int): The tmdb_id of the movie to delete
            
        Returns:
            dict: Result of the operation with success status
        """
        if not tmdb_id:
            return {
                "success": False,
                "message": "Invalid tmdbID"
            }
        
        # Delete the movie - repository returns True/False
        success = self.movie_repo.delete_movie(tmdb_id)
        
        if success:
            return {
                "success": True,
                "message": "Movie deleted successfully"
            }
        else:
            return {
                "success": False,
                "message": "Failed to delete movie. Movie may not exist or database error occurred."
            }

    def update_movie_aggregates(self, tmdb_id, total_ratings, count_ratings):
        """Updates the aggregated rating information for a movie.
    
        Note: This method is now deprecated as rating operations handle 
    aggregates atomically within transactions. Kept for backwards compatibility.
    
        Args:
            tmdb_id (int): The tmdb_id of the movie
            total_ratings (float): Sum of all ratings
            count_ratings (int): Count of ratings
        
        Returns:
            dict: Result of the operation with success status
        """
        if total_ratings < 0 or count_ratings < 0:
            return {
                "success": False,
                "message": "Rating values cannot be negative"
            }
    
        success = self.movie_repo.update_movie_aggregates(tmdb_id, total_ratings, count_ratings)
    
        if success:
            return {
                "success": True,
                "message": "Movie aggregates updated successfully"
            }
        else:
            return {
                "success": False,
                "message": "Failed to update movie aggregates"
            }


# Example usage (optional, for testing):
# if __name__ == "__main__":
#     service = MovieService()
#     result = service.get_movies_for_homepage(page_number=1, movies_per_page=20, max_pages=10)
#     print(f"Current Page: {result['current_page']}, Total Pages: {result['total_pages']}")
#     print(f"Movies on Page: {len(result['movies'])}")
#     print(f"Pages to Show: {result['page_numbers']}")