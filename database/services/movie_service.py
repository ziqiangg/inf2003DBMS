# database/services/movie_service.py

from database.repositories.movie_repository import MovieRepository

class MovieService:
    def __init__(self):
        self.movie_repo = MovieRepository()

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
        return self.movie_repo.get_movie_by_id(tmdb_id)


# Example usage (optional, for testing):
# if __name__ == "__main__":
#     service = MovieService()
#     result = service.get_movies_for_homepage(page_number=1, movies_per_page=20, max_pages=10)
#     print(f"Current Page: {result['current_page']}, Total Pages: {result['total_pages']}")
#     print(f"Movies on Page: {len(result['movies'])}")
#     print(f"Pages to Show: {result['page_numbers']}")