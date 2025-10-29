# database/repositories/cast_crew_repository.py
from database.db_mongo_connection import get_mongo_connection
from pymongo.errors import PyMongoError

class CastCrewRepository:
    def __init__(self):
        self.db = get_mongo_connection()
        if self.db is not None:
            self.cast_collection = self.db['MovieCastLink']
            self.crew_collection = self.db['MovieCrewLink']
        else:
            self.cast_collection = None
            self.crew_collection = None
            print("Warning: Could not connect to MongoDB. Cast/Crew repository will not function.")

    def get_cast_for_movie(self, tmdb_id):
        """Fetches the cast for a specific movie from MongoDB."""
        if self.cast_collection is None:
            print("MongoDB connection not available for Cast collection.")
            return []

        try:
            # Query the MovieCastLink collection for the given tmdbID
            cursor = self.cast_collection.find({"tmdbID": tmdb_id})
            cast_list = list(cursor)
            # Remove MongoDB's internal _id field from results for cleaner output if desired
            for person in cast_list:
                person.pop('_id', None) # Remove _id if present
            return cast_list
        except PyMongoError as e:
            print(f"Error fetching cast for movie {tmdb_id} from MongoDB: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error fetching cast for movie {tmdb_id}: {e}")
            return []

    def get_crew_for_movie(self, tmdb_id):
        """Fetches the crew for a specific movie from MongoDB."""
        if self.crew_collection is None:
            print("MongoDB connection not available for Crew collection.")
            return []

        try:
            # Query the MovieCrewLink collection for the given tmdbID
            cursor = self.crew_collection.find({"tmdbID": tmdb_id})
            crew_list = list(cursor)
            # Remove MongoDB's internal _id field from results for cleaner output if desired
            for person in crew_list:
                person.pop('_id', None) # Remove _id if present
            return crew_list
        except PyMongoError as e:
            print(f"Error fetching crew for movie {tmdb_id} from MongoDB: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error fetching crew for movie {tmdb_id}: {e}")
            return []

    def get_director_for_movie(self, tmdb_id):
        """Fetches the director for a specific movie from MongoDB."""
        if self.crew_collection is None:
            print("MongoDB connection not available for Crew collection.")
            return None

        try:
            # Query the MovieCrewLink collection for the given tmdbID where job is 'Director'
            director_doc = self.crew_collection.find_one({"tmdbID": tmdb_id, "job": "Director"})
            if director_doc:
                 director_doc.pop('_id', None) # Remove _id if present
            return director_doc
        except PyMongoError as e:
            print(f"Error fetching director for movie {tmdb_id} from MongoDB: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error fetching director for movie {tmdb_id}: {e}")
            return None
        
    def add_cast_member(self, tmdb_id, name, character):
        """
        Inserts a new cast member into MongoDB.
        If an entry with the same tmdbID and name already exists, it updates the character.
        Otherwise, it creates a new entry.
        Uses tmdbID and name for collision check.
        """
        if self.cast_collection is None:
            print("MongoDB connection not available for Cast collection.")
            return False

        try:
            # Check if the cast member already exists for this movie using name (collision check)
            existing_cast = self.cast_collection.find_one({"tmdbID": tmdb_id, "name": name})
            if existing_cast:
                 print(f"DEBUG: Cast member (name: '{name}') already exists for tmdbID {tmdb_id}. Updating character from '{existing_cast.get('character', '')}' to '{character}'.")
                 # Update the existing entry's character
                 result = self.cast_collection.update_one(
                     {"tmdbID": tmdb_id, "name": name},
                     {"$set": {"character": character}} # Update character, name stays the same
                 )
                 # Return True if the update was successful (modified_count > 0)
                 return result.modified_count > 0
            result = self.cast_collection.insert_one({
                "tmdbID": tmdb_id, "name": name, "character": character
                # "actor_id": actor_id # Removed from collision logic and assumed handled elsewhere if needed for storage
            })
            return result.inserted_id is not None
        except PyMongoError as e:
            print(f"Error adding/updating cast member: {e}")
            return False

    def add_crew_member(self, tmdb_id, name, job, department):
        """
        Inserts a new crew member into MongoDB.
        If an entry with the same tmdbID, name, and job already exists, it updates the department.
        Otherwise, it creates a new entry.
        Uses tmdbID, name, and job for collision check.
        """
        if self.crew_collection is None:
            print("MongoDB connection not available for Crew collection.")
            return False

        try:
            # Check if the crew member already exists for this movie using name and job (collision check)
            existing_crew = self.crew_collection.find_one({"tmdbID": tmdb_id, "name": name, "job": job})
            if existing_crew:
                 print(f"DEBUG: Crew member (name: '{name}', job: '{job}') already exists for tmdbID {tmdb_id}. Updating department from '{existing_crew.get('department', '')}' to '{department}'.")
                 # Update the existing entry's department
                 result = self.crew_collection.update_one(
                     {"tmdbID": tmdb_id, "name": name, "job": job},
                     {"$set": {"department": department}} # Update department, name and job stay the same
                 )
                 # Return True if the update was successful (modified_count > 0)
                 return result.modified_count > 0

            # If no collision, insert the new crew member
            result = self.crew_collection.insert_one({
                "tmdbID": tmdb_id, "name": name, "job": job, "department": department
                # "person_id": person_id # Removed from collision logic and assumed handled elsewhere if needed for storage
            })
            return result.inserted_id is not None
        except PyMongoError as e:
            print(f"Error adding/updating crew member: {e}")
            return False

    def update_cast_member(self, tmdb_id, name, new_character):
        """Updates the character for an existing cast member identified by name."""
        if self.cast_collection is None:
            print("MongoDB connection not available for Cast collection.")
            return False

        try:
            # Find and update the specific cast entry by name
            result = self.cast_collection.update_one(
                {"tmdbID": tmdb_id, "name": name}, # Changed from actor_id to name
                {"$set": {"character": new_character}}
            )
            # Success if exactly one document was modified
            return result.modified_count == 1
        except PyMongoError as e:
            print(f"Error updating cast member: {e}")
            return False

    def update_crew_member(self, tmdb_id, name, old_job, new_department, new_job=None):
        """Updates the department (and optionally the job) for an existing crew member identified by name and old job."""
        if self.crew_collection is None:
            print("MongoDB connection not available for Crew collection.")
            return False

        try:
            # Prepare the update document
            update_doc = {"$set": {"department": new_department}}
            if new_job is not None:
                update_doc["$set"]["job"] = new_job

            # Find and update the specific crew entry by name and old job
            result = self.crew_collection.update_one(
                {"tmdbID": tmdb_id, "name": name, "job": old_job}, # Match on name and old job
                update_doc
            )
            # Success if exactly one document was modified
            return result.modified_count == 1
        except PyMongoError as e:
            print(f"Error updating crew member: {e}")
            return False

    def delete_cast_member(self, tmdb_id, name):
        """Deletes a cast member for a specific movie identified by name."""
        if self.cast_collection is None:
            print("MongoDB connection not available for Cast collection.")
            return False

        try:
            result = self.cast_collection.delete_one({"tmdbID": tmdb_id, "name": name}) # Changed from actor_id to name
            return result.deleted_count == 1
        except PyMongoError as e:
            print(f"Error deleting cast member: {e}")
            return False

    def delete_crew_member(self, tmdb_id, name, job):
        """Deletes a crew member for a specific movie based on name and job."""
        if self.crew_collection is None:
            print("MongoDB connection not available for Crew collection.")
            return False

        try:
            result = self.crew_collection.delete_one({"tmdbID": tmdb_id, "name": name, "job": job}) # Changed from person_id to name
            return result.deleted_count == 1
        except PyMongoError as e:
            print(f"Error deleting crew member: {e}")
            return False


    def get_all_cast_for_movie(self, tmdb_id):
        """Alias for get_cast_for_movie, kept for consistency if needed."""
        return self.get_cast_for_movie(tmdb_id)

    def get_all_crew_for_movie(self, tmdb_id):
        """alias for get_crew_for_movie, kept for consistency if needed."""
        return self.get_crew_for_movie(tmdb_id)
    
    def delete_all_cast_for_movie(self, tmdb_id):
        """
        Deletes all cast members for a specific movie from MongoDB.
        Uses tmdbID for the deletion query.
        """
        if self.cast_collection is None:
            print("MongoDB connection not available for Cast collection.")
            return False

        try:
            result = self.cast_collection.delete_many({"tmdbID": tmdb_id})
            deleted_count = result.deleted_count
            print(f"DEBUG: Deleted {deleted_count} cast member(s) for tmdbID {tmdb_id} from MongoDB.")
            return deleted_count >= 0  # Success if the operation ran without error, even if count was 0
        except PyMongoError as e:
            print(f"Error deleting all cast for movie {tmdb_id} from MongoDB: {e}")
            return False

    def delete_all_crew_for_movie(self, tmdb_id):
        """
        Deletes all crew members for a specific movie from MongoDB.
        Uses tmdbID for the deletion query.
        """
        if self.crew_collection is None:
            print("MongoDB connection not available for Crew collection.")
            return False

        try:
            result = self.crew_collection.delete_many({"tmdbID": tmdb_id})
            deleted_count = result.deleted_count
            print(f"DEBUG: Deleted {deleted_count} crew member(s) for tmdbID {tmdb_id} from MongoDB.")
            return deleted_count >= 0  # Success if the operation ran without error, even if count was 0
        except PyMongoError as e:
            print(f"Error deleting all crew for movie {tmdb_id} from MongoDB: {e}")
            return False

    # Optional: Methods for adding/updating cast/crew if needed by admin functionality
    # def add_cast_member(self, tmdb_id, actor_id, name, character):
    #     if self.cast_collection is None: # Also corrected here
    #         return False
    #     try:
    #         result = self.cast_collection.insert_one({
    #             "tmdbID": tmdb_id, "actor_id": actor_id, "name": name, "character": character
    #         })
    #         return result.inserted_id is not None
    #     except PyMongoError as e:
    #         print(f"Error adding cast member: {e}")
    #         return False
    #
    # def add_crew_member(self, tmdb_id, person_id, name, job, department):
    #     if self.crew_collection is None: # Also corrected here
    #         return False
    #     try:
    #         result = self.crew_collection.insert_one({
    #             "tmdbID": tmdb_id, "person_id": person_id, "name": name, "job": job, "department": department
    #         })
    #         return result.inserted_id is not None
    #     except PyMongoError as e:
    #         print(f"Error adding crew member: {e}")
    #         return False
