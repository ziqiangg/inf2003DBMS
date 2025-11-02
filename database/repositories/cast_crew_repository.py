# database/repositories/cast_crew_repository.py
from database.db_mongo_connection import get_mongo_connection
from pymongo.errors import PyMongoError

class CastCrewRepository:
    def __init__(self):
        # Don't store connection or collections - get fresh ones per operation
        pass

    def _get_cast_collection(self):
        """Helper to get cast collection for each operation."""
        db = get_mongo_connection()
        return db['MovieCastLink'] if db is not None else None

    def _get_crew_collection(self):
        """Helper to get crew collection for each operation."""
        db = get_mongo_connection()
        return db['MovieCrewLink'] if db is not None else None

    def get_cast_for_movie(self, tmdb_id):
        """Fetches the cast for a specific movie from MongoDB."""
        cast_collection = self._get_cast_collection()
        if cast_collection is None:
            print("MongoDB connection not available for Cast collection.")
            return []

        try:
            cursor = cast_collection.find({"tmdbID": tmdb_id})
            cast_list = list(cursor)
            for person in cast_list:
                person.pop('_id', None)
            return cast_list
        except PyMongoError as e:
            print(f"Error fetching cast for movie {tmdb_id} from MongoDB: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error fetching cast for movie {tmdb_id}: {e}")
            return []

    def get_crew_for_movie(self, tmdb_id):
        """Fetches the crew for a specific movie from MongoDB."""
        crew_collection = self._get_crew_collection()
        if crew_collection is None:
            print("MongoDB connection not available for Crew collection.")
            return []

        try:
            cursor = crew_collection.find({"tmdbID": tmdb_id})
            crew_list = list(cursor)
            for person in crew_list:
                person.pop('_id', None)
            return crew_list
        except PyMongoError as e:
            print(f"Error fetching crew for movie {tmdb_id} from MongoDB: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error fetching crew for movie {tmdb_id}: {e}")
            return []

    def get_director_for_movie(self, tmdb_id):
        """Fetches the director for a specific movie from MongoDB."""
        crew_collection = self._get_crew_collection()
        if crew_collection is None:
            print("MongoDB connection not available for Crew collection.")
            return None

        try:
            director_doc = crew_collection.find_one({"tmdbID": tmdb_id, "job": "Director"})
            if director_doc:
                director_doc.pop('_id', None)
            return director_doc
        except PyMongoError as e:
            print(f"Error fetching director for movie {tmdb_id} from MongoDB: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error fetching director for movie {tmdb_id}: {e}")
            return None
        
    def add_cast_member(self, tmdb_id, name, character):
        """Inserts a new cast member into MongoDB."""
        cast_collection = self._get_cast_collection()
        if cast_collection is None:
            print("MongoDB connection not available for Cast collection.")
            return False

        try:
            existing_cast = cast_collection.find_one({"tmdbID": tmdb_id, "name": name})
            if existing_cast:
                print(f"DEBUG: Cast member (name: '{name}') already exists for tmdbID {tmdb_id}. Updating character from '{existing_cast.get('character', '')}' to '{character}'.")
                result = cast_collection.update_one(
                    {"tmdbID": tmdb_id, "name": name},
                    {"$set": {"character": character}}
                )
                return result.modified_count > 0
            
            result = cast_collection.insert_one({
                "tmdbID": tmdb_id, "name": name, "character": character
            })
            return result.inserted_id is not None
        except PyMongoError as e:
            print(f"Error adding/updating cast member: {e}")
            return False

    def add_crew_member(self, tmdb_id, name, job, department):
        """Inserts a new crew member into MongoDB."""
        crew_collection = self._get_crew_collection()
        if crew_collection is None:
            print("MongoDB connection not available for Crew collection.")
            return False

        try:
            existing_crew = crew_collection.find_one({"tmdbID": tmdb_id, "name": name, "job": job})
            if existing_crew:
                print(f"DEBUG: Crew member (name: '{name}', job: '{job}') already exists for tmdbID {tmdb_id}. Updating department from '{existing_crew.get('department', '')}' to '{department}'.")
                result = crew_collection.update_one(
                    {"tmdbID": tmdb_id, "name": name, "job": job},
                    {"$set": {"department": department}}
                )
                return result.modified_count > 0

            result = crew_collection.insert_one({
                "tmdbID": tmdb_id, "name": name, "job": job, "department": department
            })
            return result.inserted_id is not None
        except PyMongoError as e:
            print(f"Error adding/updating crew member: {e}")
            return False

    def update_cast_member(self, tmdb_id, name, new_character):
        """Updates the character for an existing cast member identified by name."""
        cast_collection = self._get_cast_collection()
        if cast_collection is None:
            print("MongoDB connection not available for Cast collection.")
            return False

        try:
            result = cast_collection.update_one(
                {"tmdbID": tmdb_id, "name": name},
                {"$set": {"character": new_character}}
            )
            return result.modified_count == 1
        except PyMongoError as e:
            print(f"Error updating cast member: {e}")
            return False

    def update_crew_member(self, tmdb_id, name, old_job, new_department, new_job=None):
        """Updates the department (and optionally the job) for an existing crew member."""
        crew_collection = self._get_crew_collection()
        if crew_collection is None:
            print("MongoDB connection not available for Crew collection.")
            return False

        try:
            update_doc = {"$set": {"department": new_department}}
            if new_job is not None:
                update_doc["$set"]["job"] = new_job

            result = crew_collection.update_one(
                {"tmdbID": tmdb_id, "name": name, "job": old_job},
                update_doc
            )
            return result.modified_count == 1
        except PyMongoError as e:
            print(f"Error updating crew member: {e}")
            return False

    def delete_cast_member(self, tmdb_id, name):
        """Deletes a cast member for a specific movie identified by name."""
        cast_collection = self._get_cast_collection()
        if cast_collection is None:
            print("MongoDB connection not available for Cast collection.")
            return False

        try:
            result = cast_collection.delete_one({"tmdbID": tmdb_id, "name": name})
            return result.deleted_count == 1
        except PyMongoError as e:
            print(f"Error deleting cast member: {e}")
            return False

    def delete_crew_member(self, tmdb_id, name, job):
        """Deletes a crew member for a specific movie based on name and job."""
        crew_collection = self._get_crew_collection()
        if crew_collection is None:
            print("MongoDB connection not available for Crew collection.")
            return False

        try:
            result = crew_collection.delete_one({"tmdbID": tmdb_id, "name": name, "job": job})
            return result.deleted_count == 1
        except PyMongoError as e:
            print(f"Error deleting crew member: {e}")
            return False

    def get_all_cast_for_movie(self, tmdb_id):
        """Alias for get_cast_for_movie, kept for consistency if needed."""
        return self.get_cast_for_movie(tmdb_id)

    def get_all_crew_for_movie(self, tmdb_id):
        """Alias for get_crew_for_movie, kept for consistency if needed."""
        return self.get_crew_for_movie(tmdb_id)
    
    def delete_all_cast_for_movie(self, tmdb_id):
        """Deletes all cast members for a specific movie from MongoDB."""
        cast_collection = self._get_cast_collection()
        if cast_collection is None:
            print("MongoDB connection not available for Cast collection.")
            return False

        try:
            result = cast_collection.delete_many({"tmdbID": tmdb_id})
            deleted_count = result.deleted_count
            print(f"DEBUG: Deleted {deleted_count} cast member(s) for tmdbID {tmdb_id} from MongoDB.")
            return deleted_count >= 0
        except PyMongoError as e:
            print(f"Error deleting all cast for movie {tmdb_id} from MongoDB: {e}")
            return False

    def delete_all_crew_for_movie(self, tmdb_id):
        """Deletes all crew members for a specific movie from MongoDB."""
        crew_collection = self._get_crew_collection()
        if crew_collection is None:
            print("MongoDB connection not available for Crew collection.")
            return False

        try:
            result = crew_collection.delete_many({"tmdbID": tmdb_id})
            deleted_count = result.deleted_count
            print(f"DEBUG: Deleted {deleted_count} crew member(s) for tmdbID {tmdb_id} from MongoDB.")
            return deleted_count >= 0
        except PyMongoError as e:
            print(f"Error deleting all crew for movie {tmdb_id} from MongoDB: {e}")
            return False
