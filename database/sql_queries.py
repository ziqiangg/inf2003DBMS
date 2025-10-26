# database/sql_queries.py

# --- User Queries ---

# Query to check if a user exists by email during registration
CHECK_USER_EXISTS_BY_EMAIL = """
SELECT userID FROM Users WHERE email = %s;
"""

# Query to insert a new user during registration
INSERT_NEW_USER = """
INSERT INTO Users (email, passwordHash, role) VALUES (%s, %s, 'user');
"""

# Query to retrieve user information by email during login
GET_USER_BY_EMAIL = """
SELECT * FROM Users WHERE email = %s;
"""

# Query to delete a user account (soft delete - only email and password are removed)
SOFT_DELETE_USER = """
UPDATE Users SET email = NULL, passwordHash = NULL WHERE userID = %s;
"""

# --- Movie Queries (Existing + pagination) ---

# -- Query to get movies for the home page with pagination, sorted by release date (newest first)
GET_MOVIES_PAGINATED = """
SELECT m.tmdbID, m.title, m.poster, m.overview, m.releaseDate, m.runtime, m.totalRatings, m.countRatings
FROM Movies m
ORDER BY m.releaseDate DESC, m.tmdbID DESC -- Order by release date descending, then by ID descending as a secondary sort to ensure stability
LIMIT %s OFFSET %s;
"""

# Query to count total number of movies (for calculating total pages)
COUNT_ALL_MOVIES = """
SELECT COUNT(*) as total_count FROM Movies;
"""

# You can keep any existing movie queries here if needed for the home page or other features
GET_MOVIE_BY_ID = """
SELECT m.tmdbID, m.title, m.poster, m.overview, m.releaseDate, m.runtime, m.totalRatings, m.countRatings
FROM Movies m
WHERE m.tmdbID = %s;
"""

# Example: Query to get top-rated movies for the home page (optional)
GET_TOP_RATED_MOVIES = """
SELECT m.tmdbID, m.title, m.poster, m.totalRatings
FROM Movies m
WHERE m.countRatings > 0
ORDER BY m.totalRatings DESC
LIMIT 10;
"""

# Example: Query to get movies by genre for the home page (optional)
GET_MOVIES_BY_GENRE = """
SELECT DISTINCT m.tmdbID, m.title, m.poster, m.overview, m.releaseDate, m.runtime, m.totalRatings, m.countRatings
FROM Movies m
JOIN Movie_Genre mg ON m.tmdbID = mg.tmdbID
JOIN Genre g ON mg.genreID = g.genreID
WHERE g.genreName = %s;
"""

# Example: Query for single-field movie search (title)
SEARCH_MOVIES_BY_TITLE = """
SELECT m.tmdbID, m.title, m.poster, m.overview, m.releaseDate, m.runtime, m.totalRatings, m.countRatings
FROM Movies m
WHERE m.title LIKE %s;
"""

# Example: Query for single-field movie search (genre)
SEARCH_MOVIES_BY_GENRE = """
SELECT DISTINCT m.tmdbID, m.title, m.poster, m.overview, m.releaseDate, m.runtime, m.totalRatings, m.countRatings
FROM Movies m
JOIN Movie_Genre mg ON m.tmdbID = mg.tmdbID
JOIN Genre g ON mg.genreID = g.genreID
WHERE g.genreName = %s;
"""

# Example: Query for single-field movie search (year)
SEARCH_MOVIES_BY_YEAR = """
SELECT m.tmdbID, m.title, m.poster, m.overview, m.releaseDate, m.runtime, m.totalRatings, m.countRatings
FROM Movies m
WHERE YEAR(m.releaseDate) = %s;
"""

# Example: Query for advanced multi-field search (Genre + Year)
ADVANCED_SEARCH_GENRE_YEAR = """
SELECT DISTINCT m.tmdbID, m.title, m.poster, m.overview, m.releaseDate, m.runtime, m.totalRatings, m.countRatings
FROM Movies m
JOIN Movie_Genre mg ON m.tmdbID = mg.tmdbID
JOIN Genre g ON mg.genreID = g.genreID
WHERE g.genreName = %s AND YEAR(m.releaseDate) = %s;
"""

# Example: Query for advanced multi-field search (Genre + Min Rating)
ADVANCED_SEARCH_GENRE_MIN_RATING = """
SELECT DISTINCT m.tmdbID, m.title, m.poster, m.overview, m.releaseDate, m.runtime, m.totalRatings, m.countRatings
FROM Movies m
WHERE m.totalRatings >= %s AND m.tmdbID IN (
    SELECT mg.tmdbID
    FROM Movie_Genre mg
    JOIN Genre g ON mg.genreID = g.genreID
    WHERE g.genreName = %s
);
"""

# Example: Query for advanced multi-field search (Year + Min Rating)
ADVANCED_SEARCH_YEAR_MIN_RATING = """
SELECT m.tmdbID, m.title, m.poster, m.overview, m.releaseDate, m.runtime, m.totalRatings, m.countRatings
FROM Movies m
WHERE YEAR(m.releaseDate) = %s AND m.totalRatings >= %s;
"""

# Example: Query for advanced multi-field search (Genre + Year + Min Rating)
ADVANCED_SEARCH_GENRE_YEAR_MIN_RATING = """
SELECT DISTINCT m.tmdbID, m.title, m.poster, m.overview, m.releaseDate, m.runtime, m.totalRatings, m.countRatings
FROM Movies m
JOIN Movie_Genre mg ON m.tmdbID = mg.tmdbID
JOIN Genre g ON mg.genreID = g.genreID
WHERE g.genreName = %s AND YEAR(m.releaseDate) = %s AND m.totalRatings >= %s;
"""

# Example: Query to get genres for dropdown/filtering
GET_ALL_GENRES = """
SELECT genreName FROM Genre ORDER BY genreName;
"""

# Example: Query to get all ratings for a specific user (for profile page)
GET_USER_RATINGS = """
SELECT r.tmdbID, m.title, r.rating, r.timeStamp
FROM Ratings r
JOIN Movies m ON r.tmdbID = m.tmdbID
WHERE r.userID = %s
ORDER BY r.rating DESC;
"""

# Example: Query to get all reviews for a specific user (for profile page)
GET_USER_REVIEWS = """
SELECT rev.tmdbID, m.title, rev.review, rev.timeStamp
FROM Reviews rev
JOIN Movies m ON rev.tmdbID = m.tmdbID
WHERE rev.userID = %s
ORDER BY rev.timeStamp DESC;
"""

# Example: Query to get average rating for a specific movie
GET_MOVIE_AVERAGE_RATING = """
SELECT totalRatings, countRatings FROM Movies WHERE tmdbID = %s;
"""

# Example: Query to get all reviews for a specific movie
GET_MOVIE_REVIEWS = """
SELECT r.userID, u.email, r.review, r.timeStamp
FROM Reviews r
JOIN Users u ON r.userID = u.userID
WHERE r.tmdbID = %s
ORDER BY r.timeStamp DESC;
"""

# Example: Query to get all cast and crew for a specific movie from MongoDB (this will be handled differently)
# GET_MOVIE_CAST_CREW = "..." # This will likely be a MongoDB query handled in db_mongo_pre_function.py or a dedicated service