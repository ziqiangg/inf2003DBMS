from database.services.movie_service import MovieService

def test_movies_pagination():
    movie_service = MovieService()
    result = movie_service.get_movies_for_homepage(page_number=1, movies_per_page=20, max_pages=10)
    
    print("Movie Pagination Test Results:")
    print(f"Current Page: {result['current_page']}")
    print(f"Total Pages: {result['total_pages']}")
    print(f"Number of movies on current page: {len(result['movies'])}")
    print(f"Has Previous: {result['has_prev']}")
    print(f"Has Next: {result['has_next']}")
    
    if not result['movies']:
        print("\nNo movies found in the database!")
    else:
        print(f"\nSample movie from results:")
        movie = result['movies'][0]
        print(f"Title: {movie.get('title')}")
        print(f"Release Date: {movie.get('releaseDate')}")

if __name__ == "__main__":
    test_movies_pagination()