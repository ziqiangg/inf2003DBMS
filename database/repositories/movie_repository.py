# database/repositories/movie_repository.py

from database.db_connection import get_mysql_connection, close_connection
from database.sql_queries import (
    GET_MOVIES_PAGINATED, COUNT_ALL_MOVIES, GET_MOVIE_BY_ID,
    SEARCH_MOVIES_BY_TITLE, GET_DISTINCT_YEARS,
    SEARCH_MOVIES_BY_TITLE_FULLTEXT, SEARCH_MOVIES_BY_TITLE_FULLTEXT_BOOLEAN,
    INSERT_MOVIE, INSERT_MOVIE_GENRE, CHECK_GENRE_EXISTS, INSERT_GENRE,
    LIST_ALL_GENRES, GET_NEXT_GENRE_ID, GET_NEXT_TMDB_ID, UPDATE_MOVIE,
    DELETE_MOVIE_GENRES, DELETE_MOVIE,
    GET_RATING_COUNT_FOR_MOVIE, GET_REVIEW_COUNT_FOR_MOVIE,
    DELETE_MOVIE_RATINGS, DELETE_MOVIE_REVIEWS,
    UPDATE_MOVIE_AGGREGATES 
)

class MovieRepository:
    def __init__(self):
        pass
        
    def create_movie(self, movie_data):
        """Creates a new movie and associates it with genres.
        
        Args:
            movie_data (dict): Dictionary containing movie information with keys:
                - title (required)
                - link (optional)
                - runtime (required)
                - poster (optional)
                - overview (optional)
                - releaseDate (required)
                - genres (list, required)
                
        Returns:
            dict: Dictionary containing:
                - success (bool): Whether the operation was successful
                - message (str): Success/error message
                - movie_id (int): ID of the created movie (if successful)
        """
        connection = get_mysql_connection()
        if not connection:
            return {"success": False, "message": "Could not connect to database"}
            
        cursor = connection.cursor(dictionary=True)
        try:
            # Start transaction by turning off autocommit
            connection.autocommit = False
            
            # Get the next available tmdbID
            cursor.execute(GET_NEXT_TMDB_ID)
            next_id_result = cursor.fetchone()
            movie_id = next_id_result['next_id']
            print(f"DEBUG: Next available tmdbID: {movie_id}")

            # Insert the movie with the predetermined ID
            cursor.execute(INSERT_MOVIE, (
                movie_id,
                movie_data["title"],
                movie_data.get("link"),
                movie_data["runtime"],
                movie_data.get("poster"),
                movie_data.get("overview"),
                movie_data["releaseDate"]
            ))
            print(f"DEBUG: Inserted movie with tmdbID: {movie_id}")
            
            # First, let's debug what genres exist
            print("DEBUG: Current genres in database:")
            cursor.execute(LIST_ALL_GENRES)
            existing_genres = cursor.fetchall()
            for genre in existing_genres:
                print(f"  - ID: {genre['genreID']}, Name: {genre['genreName']}")

            # Insert genre relationships
            for genre_name in movie_data["genres"]:
                try:
                    print(f"\nDEBUG: Processing genre: {genre_name}")
                    
                    # Check if genre exists
                    cursor.execute(CHECK_GENRE_EXISTS, (genre_name,))
                    genre_result = cursor.fetchone()
                    
                    if genre_result:
                        print(f"DEBUG: Genre '{genre_name}' exists with ID: {genre_result['genreID']}")
                        genre_id = genre_result['genreID']
                    else:
                        print(f"DEBUG: Genre '{genre_name}' doesn't exist, creating it")
                        # Get next available ID
                        cursor.execute(GET_NEXT_GENRE_ID)
                        next_id = cursor.fetchone()['next_id']
                        print(f"DEBUG: Next available genre ID: {next_id}")
                        
                        # Insert new genre
                        cursor.execute(INSERT_GENRE, (next_id, genre_name))
                        print(f"DEBUG: Inserted new genre with ID: {next_id}")
                        
                        genre_id = next_id
                    
                    print(f"DEBUG: Attempting to link movie {movie_id} with genre {genre_id}")
                    # Now insert the movie-genre relationship
                    cursor.execute(INSERT_MOVIE_GENRE, (movie_id, genre_id))
                    print(f"DEBUG: Successfully linked movie with genre")
                    
                except Exception as e:
                    print(f"DEBUG: Error handling genre {genre_name}: {e}")
                    import traceback
                    traceback.print_exc()
                    connection.rollback()
                    return {
                        "success": False,
                        "message": f"Failed to associate genre '{genre_name}' with movie"
                    }
            
            # Commit transaction
            connection.commit()
            
            return {
                "success": True,
                "message": "Movie created successfully",
                "movie_id": movie_id
            }
            
        except Exception as e:
            print(f"Error creating movie: {e}")
            connection.rollback()
            return {"success": False, "message": str(e)}
        finally:
            cursor.close()
            close_connection(connection)

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
            
    def get_movie_stats(self, tmdb_id):
        """Get stats about a movie's ratings and reviews.
        
        Args:
            tmdb_id (int): The tmdbID of the movie
            
        Returns:
            dict: Dictionary containing:
                - rating_count: Number of ratings
                - review_count: Number of reviews
        """
        connection = get_mysql_connection()
        if not connection:
            return {"rating_count": 0, "review_count": 0}
            
        cursor = connection.cursor(dictionary=True)
        try:
            # Get rating count
            cursor.execute(GET_RATING_COUNT_FOR_MOVIE, (tmdb_id,))  
            rating_result = cursor.fetchone()
            rating_count = rating_result['count'] if rating_result else 0
            
            # Get review count
            cursor.execute(GET_REVIEW_COUNT_FOR_MOVIE, (tmdb_id,))  
            review_result = cursor.fetchone()
            review_count = review_result['count'] if review_result else 0
            
            return {
                "rating_count": rating_count,
                "review_count": review_count
            }
        except Exception as e:
            print(f"Error getting movie stats: {e}")
            return {"rating_count": 0, "review_count": 0}
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

    def search_movies_by_title_fulltext(self, search_term, use_boolean=False):
        """Searches movies using FULLTEXT indexing for better performance.
        
        Args:
            search_term (str): The search term
            use_boolean (bool): Whether to use BOOLEAN MODE for advanced patterns
            
        Returns:
            list: List of matching movies with relevance scores
        """
        connection = get_mysql_connection()
        if not connection:
            return []
        cursor = connection.cursor(dictionary=True)
        try:
            if use_boolean:
                cursor.execute(SEARCH_MOVIES_BY_TITLE_FULLTEXT_BOOLEAN, (search_term, search_term))
            else:
                cursor.execute(SEARCH_MOVIES_BY_TITLE_FULLTEXT, (search_term, search_term))
            movies = cursor.fetchall()
            return movies
        except Exception as e:
            print(f"Error in FULLTEXT search: {e}")
            return []
        finally:
            cursor.close()
            close_connection(connection)

    def search_movies_by_title_like(self, search_term):
        """Fallback search using LIKE for short search terms.
        
        Args:
            search_term (str): The search term
            
        Returns:
            list: List of matching movies
        """
        connection = get_mysql_connection()
        if not connection:
            return []
        cursor = connection.cursor(dictionary=True)
        try:
            search_pattern = f"%{search_term}%"
            cursor.execute(SEARCH_MOVIES_BY_TITLE, (search_pattern,))
            movies = cursor.fetchall()
            return movies
        except Exception as e:
            print(f"Error in LIKE search: {e}")
            return []
        finally:
            cursor.close()
            close_connection(connection)

    def smart_search_by_title(self, search_term):
        """Smart search that chooses the best method based on search term length.
        
        - Very short terms (< 3 chars): Use LIKE search
        - Short terms (3 chars): Use LIKE search  
        - Medium/Long terms (4+ chars): Use FULLTEXT, fallback to LIKE if no results
        
        Args:
            search_term (str): The search term
            
        Returns:
            list: List of matching movies
        """
        if not search_term or len(search_term.strip()) == 0:
            return []
        
        search_term = search_term.strip()
        
        # For very short search terms, FULLTEXT won't work due to minimum word length (default 4)
        if len(search_term) < 4:
            print(f"DEBUG: Using LIKE search for short term: '{search_term}'")
            return self.search_movies_by_title_like(search_term)
        
        # Try FULLTEXT search first for longer terms
        print(f"DEBUG: Trying FULLTEXT search for term: '{search_term}'")
        results = self.search_movies_by_title_fulltext(search_term)
        
        # If FULLTEXT returns nothing, fall back to LIKE search
        if not results:
            print(f"DEBUG: FULLTEXT returned no results, falling back to LIKE search")
            results = self.search_movies_by_title_like(search_term)
        
        return results

# deprecated 
# def search_by_title_like(self, search_term):
#     """
#     Fallback search using LIKE for short search terms or when FULLTEXT returns no results.
#     """
#     query = """
#         SELECT tmdbID, title, releaseDate, poster, overview, runtime, link,
#                (totalRatings/NULLIF(countRatings, 0)) as avgRating,
#                countRatings
#         FROM Movies
#         WHERE title LIKE %s
#         ORDER BY countRatings DESC, title ASC
#         LIMIT 50
#     """
#     try:
#         cursor = self.connection.cursor(dictionary=True)
#         cursor.execute(query, (f"%{search_term}%",))
#         results = cursor.fetchall()
#         cursor.close()
#         return results
#     except Exception as e:
#         print(f"Error in LIKE search: {e}")
#         return []

# def search_by_title(self, search_term):
#     """
#     Smart search that chooses the best method based on search term length.
#     - Short terms (< 4 chars): Use LIKE search
#     - Long terms: Use FULLTEXT, fallback to LIKE if no results
#     """
#     if not search_term or len(search_term.strip()) == 0:
#         return []
    
#     search_term = search_term.strip()
    
#     # For very short search terms, FULLTEXT may not work due to minimum word length
#     if len(search_term) < 4:
#         return self.search_by_title_like(search_term)
    
#     # Try FULLTEXT search first
#     results = self.search_by_title_fulltext(search_term)
    
#     # If FULLTEXT returns nothing, fall back to LIKE search
#     if not results:
#         results = self.search_by_title_like(search_term)
    
#     return results


    def count_search_results(self, search_term=None, genre=None, year=None, min_avg_rating=None):
        """Counts the total number of movies matching the search criteria.
        
        Uses FULLTEXT for title-only searches with 4+ characters.
        """
        connection = get_mysql_connection()
        if not connection:
            return 0
        cursor = connection.cursor(dictionary=True)
        try:
            # Use FULLTEXT for counting when applicable
            use_fulltext = (search_term and len(search_term) >= 4 and 
                          not genre and not year and min_avg_rating is None)
            
            if use_fulltext:
                # Count FULLTEXT results
                query = """
                SELECT COUNT(DISTINCT m.tmdbID) as total 
                FROM Movies m
                WHERE MATCH(m.title) AGAINST(%s IN NATURAL LANGUAGE MODE)
                """
                params = [search_term]
            else:
                # Build dynamic count query
                query = "SELECT COUNT(DISTINCT m.tmdbID) as total FROM Movies m"
                params = []
                
                if genre:
                    query += " JOIN Movie_Genre mg ON m.tmdbID = mg.tmdbID JOIN Genre g ON mg.genreID = g.genreID"

                where_clauses = []
                if search_term:
                    where_clauses.append("m.title LIKE %s")
                    params.append(f"%{search_term}%")
                if genre:
                    where_clauses.append("g.genreName = %s")
                    params.append(genre)
                if isinstance(year, (list, tuple)) and len(year) == 2:
                    min_year, max_year = year
                    try:
                        min_year = int(min_year) if min_year is not None else None
                        max_year = int(max_year) if max_year is not None else None
                        
                        if min_year is not None and max_year is not None:
                            where_clauses.append("YEAR(m.releaseDate) BETWEEN %s AND %s")
                            params.extend([min_year, max_year])
                    except (TypeError, ValueError):
                        pass
                elif year:
                    try:
                        year_int = int(year)
                        where_clauses.append("YEAR(m.releaseDate) = %s")
                        params.append(year_int)
                    except (TypeError, ValueError):
                        pass
                if min_avg_rating is not None:
                    where_clauses.append("(CASE WHEN m.countRatings > 0 THEN m.totalRatings / m.countRatings ELSE 0 END) >= %s")
                    params.append(float(min_avg_rating))

                if where_clauses:
                    query += " WHERE " + " AND ".join(where_clauses)

            cursor.execute(query, tuple(params))
            result = cursor.fetchone()
            return result['total'] if result else 0
        except Exception as e:
            print(f"Error counting search results: {e}")
            return 0
        finally:
            cursor.close()
            close_connection(connection)

    def search_movies(self, search_term=None, genre=None, year=None, min_avg_rating=None, offset=0, limit=None):
        """Searches movies by optional title, genre and year filters with pagination.
        
        Uses FULLTEXT indexing for title-only searches with 4+ characters.
        """
        # Normalize empty strings to None
        if search_term is not None:
            search_term = search_term.strip()
            if search_term == "":
                search_term = None
        if genre is not None:
            genre = genre.strip() if isinstance(genre, str) and genre.strip() != "" else None
        if year is not None:
            try:
                if isinstance(year, (list, tuple)):
                    pass
                else:
                    year = int(year)
            except Exception:
                year = None

        # If no filters provided, return empty list
        if not search_term and not genre and not year and min_avg_rating is None:
            return []

        connection = get_mysql_connection()
        if not connection:
            return []

        cursor = connection.cursor(dictionary=True)
        try:
            # OPTIMIZATION: Use FULLTEXT for title-only searches with 4+ characters
            use_fulltext = (search_term and len(search_term) >= 4 and 
                          not genre and not year and min_avg_rating is None)
            
            if use_fulltext:
                # Use optimized FULLTEXT search for title-only queries
                print(f"DEBUG: Using FULLTEXT optimization for title: '{search_term}'")
                cursor.execute(SEARCH_MOVIES_BY_TITLE_FULLTEXT, (search_term, search_term))
                all_results = cursor.fetchall()
                
                # Apply offset and limit in Python (FULLTEXT query has LIMIT 50)
                limit = limit if limit else 20
                start = offset
                end = offset + limit
                movies = all_results[start:end]
                
                print(f"DEBUG: FULLTEXT found {len(all_results)} total, returning {len(movies)} for page")
                return movies
            else:
                # Build dynamic query for multi-filter searches or short terms
                query = (
                    "SELECT DISTINCT m.tmdbID, m.title, m.poster, m.overview, m.releaseDate, "
                    "m.runtime, m.totalRatings, m.countRatings FROM Movies m"
                )
                params = []
                
                # Add joins if genre filter is used
                if genre:
                    query += " JOIN Movie_Genre mg ON m.tmdbID = mg.tmdbID JOIN Genre g ON mg.genreID = g.genreID"

                where_clauses = []
                
                # Use LIKE for title in multi-filter scenarios or short terms
                if search_term:
                    where_clauses.append("m.title LIKE %s")
                    params.append(f"%{search_term}%")
                    
                if genre:
                    where_clauses.append("g.genreName = %s")
                    params.append(genre)
                    
                # Year filter handling
                if isinstance(year, (list, tuple)) and len(year) == 2:
                    min_year, max_year = year
                    try:
                        min_year = int(min_year) if min_year is not None else None
                        max_year = int(max_year) if max_year is not None else None
                        
                        if min_year is not None and max_year is not None:
                            where_clauses.append("YEAR(m.releaseDate) BETWEEN %s AND %s")
                            params.extend([min_year, max_year])
                    except (TypeError, ValueError) as e:
                        print(f"DEBUG: Error converting year values: {e}")
                elif year:
                    try:
                        year_int = int(year)
                        where_clauses.append("YEAR(m.releaseDate) = %s")
                        params.append(year_int)
                    except Exception:
                        pass

                # Minimum average rating filter
                if min_avg_rating is not None:
                    try:
                        min_avg = float(min_avg_rating)
                        where_clauses.append("(CASE WHEN m.countRatings > 0 THEN m.totalRatings / m.countRatings ELSE 0 END) >= %s")
                        params.append(min_avg)
                    except Exception:
                        pass

                if where_clauses:
                    query += " WHERE " + " AND ".join(where_clauses)

                query += " ORDER BY m.releaseDate DESC, m.tmdbID DESC"

                # Ensure offset and limit are valid
                try:
                    offset = max(0, int(offset)) if offset is not None else 0
                    limit = max(1, int(limit)) if limit is not None else 20
                except (TypeError, ValueError):
                    offset = 0
                    limit = 20

                # Add LIMIT and OFFSET
                query += " LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
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

    def update_movie(self, movie_data):
        """Updates an existing movie and its genres.
        
        Args:
            movie_data (dict): Dictionary containing movie information with keys:
                - tmdbID (required)
                - title (required)
                - link (optional)
                - runtime (required)
                - poster (optional)
                - overview (optional)
                - releaseDate (required)
                - genres (list, required)
                
        Returns:
            dict: Dictionary containing:
                - success (bool): Whether the operation was successful
                - message (str): Success/error message
        """
        connection = get_mysql_connection()
        if not connection:
            return {"success": False, "message": "Could not connect to database"}
            
        cursor = connection.cursor(dictionary=True)
        try:
            # Start transaction
            connection.autocommit = False
            
            # Update movie details
            cursor.execute(UPDATE_MOVIE, (
                movie_data["title"],
                movie_data.get("link"),
                movie_data["runtime"],
                movie_data.get("poster"),
                movie_data.get("overview"),
                movie_data["releaseDate"],
                movie_data["tmdbID"]
            ))

            # Delete existing genre relationships
            cursor.execute(DELETE_MOVIE_GENRES, (movie_data["tmdbID"],))

            # Insert new genre relationships
            for genre_name in movie_data["genres"]:
                try:
                    # Check if genre exists
                    cursor.execute(CHECK_GENRE_EXISTS, (genre_name,))
                    genre_result = cursor.fetchone()
                    
                    if genre_result:
                        genre_id = genre_result['genreID']
                    else:
                        # Get next available ID
                        cursor.execute(GET_NEXT_GENRE_ID)
                        next_id = cursor.fetchone()['next_id']
                        
                        # Insert new genre
                        cursor.execute(INSERT_GENRE, (next_id, genre_name))
                        genre_id = next_id
                    
                    # Insert the movie-genre relationship
                    cursor.execute(INSERT_MOVIE_GENRE, (movie_data["tmdbID"], genre_id))
                    
                except Exception as e:
                    connection.rollback()
                    return {
                        "success": False,
                        "message": f"Failed to associate genre '{genre_name}' with movie"
                    }
            
            # Commit transaction
            connection.commit()
            
            return {
                "success": True,
                "message": "Movie updated successfully"
            }
            
        except Exception as e:
            connection.rollback()
            return {"success": False, "message": str(e)}
        finally:
            cursor.close()
            close_connection(connection)

    def delete_movie(self, tmdb_id):
        """Deletes a movie and all its related data.
        
        Args:
            tmdb_id (int): The tmdbID of the movie to delete
                
        Raises:
            Exception: If deletion fails
        """
        connection = get_mysql_connection()
        if not connection:
            raise Exception("Could not connect to database")
            
        cursor = connection.cursor(dictionary=True)
        try:
            # Start transaction
            connection.autocommit = False
            
            # Delete all related data first
            # 1. Delete ratings
            cursor.execute(DELETE_MOVIE_RATINGS, (tmdb_id,))  
            
            # 2. Delete reviews
            cursor.execute(DELETE_MOVIE_REVIEWS, (tmdb_id,))  
            
            # 3. Delete movie-genre relationships
            cursor.execute(DELETE_MOVIE_GENRES, (tmdb_id,))
            
            # Finally, delete the movie itself
            cursor.execute(DELETE_MOVIE, (tmdb_id,))
            
            # Commit transaction
            connection.commit()
            
        except Exception as e:
            connection.rollback()
            raise e
        finally:
            cursor.close()
            close_connection(connection)

    def update_movie_aggregates(self, tmdb_id, total_ratings, count_ratings):
        """Updates the aggregated rating sum and count for a movie.
    
        Args:
        tmdb_id (int): The movie's tmdbID
        total_ratings (float): Sum of all ratings for the movie
        count_ratings (int): Number of ratings for the movie
        
        Returns:
        bool: True if successful, False otherwise
        """
        connection = get_mysql_connection()
        if not connection:
            return False

        cursor = connection.cursor()
        try:
            cursor.execute(UPDATE_MOVIE_AGGREGATES, (total_ratings, count_ratings, tmdb_id))
            connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating movie aggregates for tmdbID {tmdb_id}: {e}")
            connection.rollback()
            return False
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