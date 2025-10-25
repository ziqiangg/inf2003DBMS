# MooV

## 🎬 Overview
A **hybrid DBMS** that combines **MySQL** and **MongoDB** to efficiently manage a comprehensive movie rating platform with 45,000+ movies and 400,000+ user ratings.

## Architecture
- **MySQL (Relational):** Structured data including movies, users, ratings, genres, reviews
- **MongoDB (Non-Relational):** Unstructured data inclding movie crew and cast

## Key Features
- **Multi-tier user system:** Guest, registered user, and admin roles with granular permissions
- **Performance optimization:** Denormalized rating aggregations for sub-second query response
- **Scalable design:** Hybrid approach leverages strengths of both SQL and NoSQL databases
- **Data integrity:** MySQL ensures ACID compliance for critical transactional data

## 🗃️ Database Schema

### Tables OLD NEED TO UPDATE

#### Movies 
```sql
CREATE TABLE Movies (
    tmdbID INT PRIMARY KEY,
    title TEXT,
    link TEXT,
    release_date TEXT,
    runtime INT,
    poster TEXT,
    overview TEXT,  
    totalRatings DOUBLE DEFAULT 0,
    countRatings INT DEFAULT 0
);
```

#### Genre
```sql
CREATE TABLE Genre (
    genreID INT PRIMARY KEY,
    genreName VARCHAR(100)
);
```

#### Movie_Genre
```sql
CREATE TABLE Movie_Genre (
    tmdbID INT,
    genreID INT,
    PRIMARY KEY (tmdbID, genreID),
    FOREIGN KEY (tmdbID) REFERENCES Movies(tmdbID),
    FOREIGN KEY (genreID) REFERENCES Genre(genreID)
);
```

#### Ratings
```sql
CREATE TABLE Ratings (
    userID INT,
    tmdbID INT,
    rating DOUBLE,
    PRIMARY KEY (userID, tmdbID),
    FOREIGN KEY (tmdbID) REFERENCES Movies(tmdbID),
    FOREIGN KEY (userID) REFERENCES Users(userID)
);
```

#### Reviews
```sql
CREATE TABLE Reviews (
    userID INT,
    tmdbID INT,
    review TEXT,
    PRIMARY KEY (userID, tmdbID),
    FOREIGN KEY (tmdbID) REFERENCES Movies(tmdbID),
    FOREIGN KEY (userID) REFERENCES Users(userID)
);
```

#### Users
```sql
CREATE TABLE Users (
    userID INT PRIMARY KEY AUTO_INCREMENT,
    passwordHash VARCHAR(255) NOT NULL,
    Email VARCHAR(255) UNIQUE NOT NULL,
    roles ENUM('user', 'admin') DEFAULT 'user'
);
```

## 🚀 Setup Instructions

### Installation

1. **Clone the repository**
```bash
   git clone [https://github.com/FCSIT/database]
   cd database
```

2. **Install required dependencies**
```bash
   python -m pip install -r requirements.txt
```
3. **Create database**
```sql
   CREATE DATABASE INF2003_DBS_P1_20;
   USE INF2003_DBS_P1_20;
```
4. **Run setup script**
```bash
   mysql -u root -p INF2003_DBS_P1_20 < schema.sql
```

## Testing Connection

Run 2 files to test your database connections:

- `test.py` - Check your connection to SQL Workbench
- `test_mongodb.py` - Check your connection to MongoDB

This is to check your connection to both SQL Workbench & MongoDB.

---

## Database Folder

### Files:
- `connection` - SQL database connection settings
- `mongodb_connection` - MongoDB connection settings

**Contains:** All the IP addresses and access role accounts

---

## Utils Folder

### Purpose:
Prepare SQL statements (it is a check role and SQL instead of letting user directly use SQL)

### Function:
- Role validation before SQL execution
- Security layer for database operations
- Prevents direct SQL access by users

---

## Queries & Pre_function Folders

### Queries:
- **Purpose:** SQL statements for different user roles
- **Contains:** Role-based SQL queries (guest, user, admin)

### Pre_function:
- **Purpose:** Prepare functions to display if linking to MongoDB
- **Function:** Bridge between SQL and MongoDB operations

---

## GUI Folder

### Main Files:

#### `gui_main.py`
- **Purpose:** Store tabs
- **Function:** Main application window with tab management

#### `gui_home.py`
- **Purpose:** The main page
- **Function:** Home dashboard and primary navigation

#### Other GUI Files:
- Store UI of individual pages
- Applied to `gui_main` & `gui_home`
- Each file handles specific page functionality

---

## Project Architecture
![Schema Diagram](images/schema.png)