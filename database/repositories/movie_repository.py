# database/repositories/movie_repository.py

from database.db_connection import get_mysql_connection, close_connection
from database.sql_queries import GET_MOVIES_PAGINATED, COUNT_ALL_MOVIES, GET_MOVIE_BY_ID

class MovieRepository:
    def __init__(self):
        pass

    def get_movies_paginated(self, page_number, movies_per_page):
        """Fetches a specific page of movies."""
        connection = get_mysql_connection()
        if not connection:
            return [], 0 # Return empty list and 0 total count on connection failure
        cursor = connection.cursor(dictionary=True)
        try:
            offset = (page_number - 1) * movies_per_page
            cursor.execute(GET_MOVIES_PAGINATED, (movies_per_page, offset))
            movies = cursor.fetchall()
            return movies
        except Exception as e:
            print(f"Error fetching paginated movies: {e}")
            return [], 0 # Return empty list on error
        finally:
            cursor.close()
            close_connection(connection)

    def count_all_movies(self):
        """Counts the total number of movies in the database."""
        connection = get_mysql_connection()
        if not connection:
            return 0
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(COUNT_ALL_MOVIES)
            result = cursor.fetchone()
            return result['total_count'] if result else 0
        except Exception as e:
            print(f"Error counting movies: {e}")
            return 0
        finally:
            cursor.close()
            close_connection(connection)

    def get_movie_by_id(self, tmdb_id):
        """Fetches a single movie by its TMDB ID."""
        connection = get_mysql_connection()
        if not connection:
            return None
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(GET_MOVIE_BY_ID, (tmdb_id,))
            movie = cursor.fetchone()
            return movie
        except Exception as e:
            print(f"Error fetching movie by ID: {e}")
            return None
        finally:
            cursor.close()
            close_connection(connection)

# Example usage (optional, for testing):
# if __name__ == "__main__":
#     repo = MovieRepository()
#     page_1_movies, total = repo.get_movies_paginated(1, 20)
#     print(f"Page 1 Movies: {len(page_1_movies)}, Total Movies: {total}")
#     count = repo.count_all_movies()
#     print(f"Total Count: {count}")