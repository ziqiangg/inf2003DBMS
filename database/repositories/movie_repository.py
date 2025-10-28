# database/repositories/movie_repository.py

from database.db_connection import get_mysql_connection, close_connection
from database.sql_queries import (
    GET_MOVIES_PAGINATED, COUNT_ALL_MOVIES, GET_MOVIE_BY_ID,
    SEARCH_MOVIES_BY_TITLE, GET_DISTINCT_YEARS, GET_MIN_MAX_YEAR
)

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

    def search_movies_by_title(self, search_term):
        """Fetches movies matching the search term in the title."""
        connection = get_mysql_connection()
        if not connection:
            return []
        cursor = connection.cursor(dictionary=True)
        try:
            # Use % to match any title containing the search_term
            search_pattern = f"%{search_term}%"
            cursor.execute(SEARCH_MOVIES_BY_TITLE, (search_pattern,))
            movies = cursor.fetchall()
            return movies
        except Exception as e:
            print(f"Error searching movies by title: {e}")
            return []
        finally:
            cursor.close()
            close_connection(connection)

    def search_movies(self, search_term=None, genre=None, year=None, min_avg_rating=None):
        """Searches movies by optional title, genre and year filters.

        If all filters are None/empty, returns an empty list (no-op).
        The method builds a dynamic SQL query while keeping the returned columns
        consistent with other movie queries.
        """
        # Normalize empty strings to None
        if search_term is not None:
            search_term = search_term.strip()
            if search_term == "":
                search_term = None
        if genre is not None:
            genre = genre.strip() if isinstance(genre, str) and genre.strip() != "" else None
        if year is not None:
            # allow year as string or int
            # also allow year to be a tuple (min_year, max_year) handled below
            try:
                if isinstance(year, (list, tuple)):
                    # leave as-is, repository will process range
                    pass
                else:
                    year = int(year)
            except Exception:
                year = None

        # If no filters provided, return empty list to avoid accidental full scans
        if not search_term and not genre and not year and min_avg_rating is None:
            return []

        connection = get_mysql_connection()
        if not connection:
            return []

        cursor = connection.cursor(dictionary=True)
        try:
            # Base select
            query = (
                "SELECT DISTINCT m.tmdbID, m.title, m.poster, m.overview, m.releaseDate, "
                "m.runtime, m.totalRatings, m.countRatings FROM Movies m"
            )
            params = []
            # Add joins if genre filter is used
            if genre:
                query += " JOIN Movie_Genre mg ON m.tmdbID = mg.tmdbID JOIN Genre g ON mg.genreID = g.genreID"

            where_clauses = []
            if search_term:
                where_clauses.append("m.title LIKE %s")
                params.append(f"%{search_term}%")
            if genre:
                where_clauses.append("g.genreName = %s")
                params.append(genre)
            # Year filter: support single year, tuple/list ranges, or None
            if isinstance(year, (list, tuple)) and len(year) == 2:
                min_year, max_year = year
                try:
                    min_year = int(min_year) if min_year is not None else None
                except Exception:
                    min_year = None
                try:
                    max_year = int(max_year) if max_year is not None else None
                except Exception:
                    max_year = None

                if min_year is not None and max_year is not None:
                    if min_year == max_year:
                        where_clauses.append("YEAR(m.releaseDate) = %s")
                        params.append(min_year)
                    else:
                        where_clauses.append("YEAR(m.releaseDate) BETWEEN %s AND %s")
                        params.extend([min_year, max_year])
                elif min_year is not None:
                    where_clauses.append("YEAR(m.releaseDate) >= %s")
                    params.append(min_year)
                elif max_year is not None:
                    where_clauses.append("YEAR(m.releaseDate) <= %s")
                    params.append(max_year)
            elif year:
                try:
                    year_int = int(year)
                    where_clauses.append("YEAR(m.releaseDate) = %s")
                    params.append(year_int)
                except Exception:
                    pass

            # Minimum average rating filter (uses stored totalRatings/countRatings)
            if min_avg_rating is not None:
                try:
                    min_avg = float(min_avg_rating)
                    # Use CASE to avoid division by zero
                    where_clauses.append("(CASE WHEN m.countRatings > 0 THEN m.totalRatings / m.countRatings ELSE 0 END) >= %s")
                    params.append(min_avg)
                except Exception:
                    pass

            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)

            query += " ORDER BY m.releaseDate DESC, m.tmdbID DESC;"

            cursor.execute(query, tuple(params))
            movies = cursor.fetchall()
            return movies
        except Exception as e:
            print(f"Error searching movies with filters: {e}")
            return []
        finally:
            cursor.close()
            close_connection(connection)

    def get_available_years(self):
        """Returns a list of years actually present in Movies.releaseDate, descending.

        This uses the `GET_DISTINCT_YEARS` query so the dropdown reflects only
        years that exist in the database (no artificial continuous ranges).
        """
        connection = get_mysql_connection()
        if not connection:
            return []
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(GET_DISTINCT_YEARS)
            rows = cursor.fetchall()
            # Extract year values, filter None, ensure descending order
            years = [r['year'] for r in rows if r and r.get('year')]
            # Ensure they are integers and sorted descending
            try:
                years = sorted({int(y) for y in years}, reverse=True)
            except Exception:
                # If conversion fails, return as-is
                pass
            return years
        except Exception as e:
            print(f"Error fetching available years: {e}")
            return []
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