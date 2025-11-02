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

# --- Movie Queries ---

# Query to get next tmdbID
GET_NEXT_TMDB_ID = """
SELECT COALESCE(MAX(tmdbID), 0) + 1 AS next_id FROM Movies;
"""

# Query to insert a new movie
INSERT_MOVIE = """
INSERT INTO Movies (tmdbID, title, link, runtime, poster, overview, releaseDate)
VALUES (%s, %s, %s, %s, %s, %s, %s);
"""

# Query to check if a genre exists
CHECK_GENRE_EXISTS = """
SELECT genreID FROM Genre WHERE genreName = %s;
"""

# Query to get next available genre ID
GET_NEXT_GENRE_ID = """
SELECT COALESCE(MAX(genreID), 0) + 1 AS next_id FROM Genre;
"""

# Query to insert a new genre
INSERT_GENRE = """
INSERT INTO Genre (genreID, genreName)
VALUES (%s, %s);
"""

# Query to insert a movie-genre relationship
INSERT_MOVIE_GENRE = """
INSERT INTO Movie_Genre (tmdbID, genreID)
VALUES (%s, %s);
"""

# Query to list all genres
LIST_ALL_GENRES = """
SELECT genreID, genreName FROM Genre ORDER BY genreID;
"""

# -- Query to get movies for the home page with pagination, sorted by release date (newest first)
GET_MOVIES_PAGINATED = """
SELECT *
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
SELECT *
FROM Movies m
WHERE m.tmdbID = %s;
"""

# Query for single-field movie search (title)
SEARCH_MOVIES_BY_TITLE = """
SELECT m.tmdbID, m.title, m.poster, m.overview, m.releaseDate, m.runtime, m.totalRatings, m.countRatings
FROM Movies m
WHERE m.title LIKE %s;
"""

# # Base query for movie search with all filters
# BASE_MOVIE_SEARCH = """
# SELECT DISTINCT m.tmdbID, m.title, m.poster, m.overview, m.releaseDate, 
#        m.runtime, m.totalRatings, m.countRatings
# FROM Movies m
# {joins}
# WHERE {where_clauses}
# ORDER BY m.releaseDate DESC, m.tmdbID DESC
# {limit_clause}
# """

# Repository builds SQL dynamically, but these helpers can be used or referenced.
# SEARCH_MOVIES_BY_TITLE_GENRE_YEAR = """
# SELECT DISTINCT m.tmdbID, m.title, m.poster, m.overview, m.releaseDate, m.runtime, m.totalRatings, m.countRatings
# FROM Movies m
# JOIN Movie_Genre mg ON m.tmdbID = mg.tmdbID
# JOIN Genre g ON mg.genreID = g.genreID
# WHERE m.title LIKE %s AND g.genreName = %s AND YEAR(m.releaseDate) = %s
# ORDER BY m.releaseDate DESC, m.tmdbID DESC;
# """

# SEARCH_MOVIES_BY_TITLE_GENRE = """
# SELECT DISTINCT m.tmdbID, m.title, m.poster, m.overview, m.releaseDate, m.runtime, m.totalRatings, m.countRatings
# FROM Movies m
# JOIN Movie_Genre mg ON m.tmdbID = mg.tmdbID
# JOIN Genre g ON mg.genreID = g.genreID
# WHERE m.title LIKE %s AND g.genreName = %s
# ORDER BY m.releaseDate DESC, m.tmdbID DESC;
# """

# SEARCH_MOVIES_BY_TITLE_YEAR = """
# SELECT m.tmdbID, m.title, m.poster, m.overview, m.releaseDate, m.runtime, m.totalRatings, m.countRatings
# FROM Movies m
# WHERE m.title LIKE %s AND YEAR(m.releaseDate) = %s
# ORDER BY m.releaseDate DESC, m.tmdbID DESC;
# """

# SEARCH_MOVIES_BY_GENRE = """
# SELECT DISTINCT m.tmdbID, m.title, m.poster, m.overview, m.releaseDate, m.runtime, m.totalRatings, m.countRatings
# FROM Movies m
# JOIN Movie_Genre mg ON m.tmdbID = mg.tmdbID
# JOIN Genre g ON mg.genreID = g.genreID
# WHERE g.genreName = %s
# ORDER BY m.releaseDate DESC, m.tmdbID DESC;
# """

# SEARCH_MOVIES_BY_YEAR = """
# SELECT m.tmdbID, m.title, m.poster, m.overview, m.releaseDate, m.runtime, m.totalRatings, m.countRatings
# FROM Movies m
# WHERE YEAR(m.releaseDate) = %s
# ORDER BY m.releaseDate DESC, m.tmdbID DESC;
# """

# Get all distinct years present in Movies.releaseDate (for populating year dropdowns)
GET_DISTINCT_YEARS = """
SELECT DISTINCT YEAR(releaseDate) as year FROM Movies WHERE releaseDate IS NOT NULL ORDER BY year DESC;
"""

# # Get the minimum and maximum year present in Movies.releaseDate
# GET_MIN_MAX_YEAR = """
# SELECT MIN(YEAR(releaseDate)) AS min_year, MAX(YEAR(releaseDate)) AS max_year
# FROM Movies
# WHERE releaseDate IS NOT NULL;
# """

# --- Rating Queries ---
# Query to insert a new rating
INSERT_RATING = """
INSERT INTO Ratings (userID, tmdbID, rating) VALUES (%s, %s, %s)
ON DUPLICATE KEY UPDATE rating = VALUES(rating);
"""
# Query to update an existing rating
UPDATE_RATING = """
UPDATE Ratings SET rating = %s WHERE userID = %s AND tmdbID = %s;
"""
# Query to delete a rating
DELETE_RATING = """
DELETE FROM Ratings WHERE userID = %s AND tmdbID = %s;
"""
# Query to get a specific rating by user and movie
GET_RATING_BY_USER_AND_MOVIE = """
SELECT userID, tmdbID, rating FROM Ratings WHERE userID = %s AND tmdbID = %s;
"""
# Query to get all ratings for a specific movie
GET_RATINGS_FOR_MOVIE = """
SELECT userID, rating FROM Ratings WHERE tmdbID = %s;
"""

# Query to get total sum and count of ratings for a specific movie
GET_SUM_AND_COUNT_RATINGS_FOR_MOVIE = """
SELECT SUM(rating) AS sum_ratings, COUNT(rating) AS rating_count FROM Ratings WHERE tmdbID = %s;
"""

# --- Review Queries ---
# Query to insert a new review
INSERT_REVIEW = """
INSERT INTO Reviews (userID, tmdbID, review) VALUES (%s, %s, %s)
ON DUPLICATE KEY UPDATE review = VALUES(review);
"""
# Query to update an existing review
UPDATE_REVIEW = """
UPDATE Reviews SET review = %s WHERE userID = %s AND tmdbID = %s;
"""
# Query to delete a review
DELETE_REVIEW = """
DELETE FROM Reviews WHERE userID = %s AND tmdbID = %s;
"""
# Query to get a specific review by user and movie
GET_REVIEW_BY_USER_AND_MOVIE = """
SELECT userID, tmdbID, review, timeStamp FROM Reviews WHERE userID = %s AND tmdbID = %s;
"""
# Query to get all reviews for a specific movie (limiting to 3 most recent)
GET_REVIEWS_FOR_MOVIE = """
SELECT r.userID, u.email, r.review, r.timeStamp
FROM Reviews r
JOIN Users u ON r.userID = u.userID
WHERE r.tmdbID = %s
ORDER BY r.timeStamp DESC
LIMIT 3;
"""

# --- Genre Queries ---
# Query to get all genres
GET_ALL_GENRES = """
SELECT genreID, genreName FROM Genre ORDER BY genreName;
"""
# Query to get genres associated with a specific movie
GET_GENRES_FOR_MOVIE = """
SELECT g.genreID, g.genreName
FROM Genre g
JOIN Movie_Genre mg ON g.genreID = mg.genreID
WHERE mg.tmdbID = %s;
"""
# Query to get movies associated with a specific genre
GET_MOVIES_BY_GENRE = """
SELECT DISTINCT m.tmdbID, m.title, m.poster, m.overview, m.releaseDate, m.runtime, m.totalRatings, m.countRatings
FROM Movies m
JOIN Movie_Genre mg ON m.tmdbID = mg.tmdbID
JOIN Genre g ON mg.genreID = g.genreID
WHERE g.genreName = %s;
"""
# Query to get all genres for the dropdown/filtering 
GET_GENRES_FOR_FILTER = """
SELECT genreName FROM Genre ORDER BY genreName;
"""

# SHOULD TECHNICALLY NEVER BE USED DUE TO FOREIGN KEY CONSTRAINTS
# Query to update an existing genre (Admin functionality)
# UPDATE_GENRE = """
# UPDATE Genre SET genreName = %s WHERE genreID = %s;
# """

# DELETE_GENRE = """
# DELETE FROM Genre WHERE genreID = %s;
# """

# Query to update movie details
UPDATE_MOVIE = """
UPDATE Movies 
SET title = %s, 
    link = %s, 
    runtime = %s, 
    poster = %s, 
    overview = %s, 
    releaseDate = %s
WHERE tmdbID = %s;
"""

# Query to delete all existing movie-genre relationships for a movie
DELETE_MOVIE_GENRES = """
DELETE FROM Movie_Genre WHERE tmdbID = %s;
"""

# Query to delete a movie and its relationships
DELETE_MOVIE = """
DELETE FROM Movies WHERE tmdbID = %s;
"""

# --- Profile Page Queries ---

# Query to get all ratings for a specific user sort desc (for profile page)
GET_USER_RATINGS = """
SELECT r.tmdbID, m.title, r.rating
FROM Ratings r
JOIN Movies m ON r.tmdbID = m.tmdbID
WHERE r.userID = %s
ORDER BY r.rating DESC;
"""

# Query to get all reviews for a specific user sort by timeStamp (for profile page)
GET_USER_REVIEWS = """
SELECT rev.tmdbID, m.title, rev.review, rev.timeStamp
FROM Reviews rev
JOIN Movies m ON rev.tmdbID = m.tmdbID
WHERE rev.userID = %s
ORDER BY rev.timeStamp DESC;
"""

# Query to get both ratings and reviews for a specific user, unified for sorting on profile page
# This query gets ratings with their rating value and a NULL review
# It gets reviews for movies without ratings with a NULL rating and the review timestamp
# Then it combines them and sorts primarily by rating DESC, then by review timestamp DESC (or another suitable field for unrated movies)
GET_USER_RATINGS_AND_REVIEWS_UNIFIED = """
(
    -- Get all ratings for the user, including the movie title
    SELECT
        r.tmdbID,
        m.title,
        r.rating,
        NULL as review_text, -- No review for this entry
        NULL as rating_timeStamp, -- Ratings table does not have timeStamp, so use NULL
        NULL as review_timeStamp -- No review timestamp in this part
    FROM Ratings r
    JOIN Movies m ON r.tmdbID = m.tmdbID
    WHERE r.userID = %s
)
UNION ALL
(
    -- Get all reviews for the user for movies they have NOT rated
    SELECT
        rev.tmdbID,
        m.title,
        NULL as rating, -- No rating for this entry
        rev.review as review_text,
        NULL as rating_timeStamp, -- No rating timestamp in this part
        rev.timeStamp as review_timeStamp -- Include review timestamp
    FROM Reviews rev
    JOIN Movies m ON rev.tmdbID = m.tmdbID
    WHERE rev.userID = %s
      AND rev.tmdbID NOT IN (SELECT tmdbID FROM Ratings WHERE userID = %s)
)
ORDER BY
    -- Sort primarily by rating descending (NULL ratings come last)
    CASE WHEN rating IS NOT NULL THEN 0 ELSE 1 END, -- Put rated movies first
    rating DESC, -- Then by rating value descending
    review_timeStamp DESC; -- Then by review timestamp descending for unrated movies with reviews
"""

# Example: Query to get all cast and crew for a specific movie from MongoDB (this will be handled differently)
# GET_MOVIE_CAST_CREW = "..." # This will likely be a MongoDB query handled in db_mongo_pre_function.py or a dedicated service