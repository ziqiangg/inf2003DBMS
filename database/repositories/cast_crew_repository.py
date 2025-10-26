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
        # --- CORRECTED: Compare with None ---
        if self.cast_collection is None:
        # --- END CORRECTED ---
            print("MongoDB connection not available for Cast collection.")
            return []

        try:
            # Query the MovieCastLink collection for the given tmdbid
            cursor = self.cast_collection.find({"tmdbid": tmdb_id})
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
        # --- CORRECTED: Compare with None ---
        if self.crew_collection is None:
        # --- END CORRECTED ---
            print("MongoDB connection not available for Crew collection.")
            return []

        try:
            # Query the MovieCrewLink collection for the given tmdbid
            cursor = self.crew_collection.find({"tmdbid": tmdb_id})
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
        # --- CORRECTED: Compare with None ---
        if self.crew_collection is None:
        # --- END CORRECTED ---
            print("MongoDB connection not available for Crew collection.")
            return None

        try:
            # Query the MovieCrewLink collection for the given tmdbid where job is 'Director'
            director_doc = self.crew_collection.find_one({"tmdbid": tmdb_id, "job": "Director"})
            if director_doc:
                 director_doc.pop('_id', None) # Remove _id if present
            return director_doc
        except PyMongoError as e:
            print(f"Error fetching director for movie {tmdb_id} from MongoDB: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error fetching director for movie {tmdb_id}: {e}")
            return None

    # Optional: Methods for adding/updating cast/crew if needed by admin functionality
    # def add_cast_member(self, tmdb_id, actor_id, name, character):
    #     if self.cast_collection is None: # Also corrected here
    #         return False
    #     try:
    #         result = self.cast_collection.insert_one({
    #             "tmdbid": tmdb_id, "actor_id": actor_id, "name": name, "character": character
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
    #             "tmdbid": tmdb_id, "person_id": person_id, "name": name, "job": job, "department": department
    #         })
    #         return result.inserted_id is not None
    #     except PyMongoError as e:
    #         print(f"Error adding crew member: {e}")
    #         return False
