# database/services/cast_crew_service.py
from database.repositories.cast_crew_repository import CastCrewRepository
import threading

class CastCrewService:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(CastCrewService, cls).__new__(cls)
                    cls._instance.cast_crew_repo = CastCrewRepository()
        return cls._instance

    def get_full_cast_and_crew(self, tmdb_id):
        """Retrieves both cast and crew for a specific movie."""
        cast = self.cast_crew_repo.get_cast_for_movie(tmdb_id)
        crew = self.cast_crew_repo.get_crew_for_movie(tmdb_id)
        return {
            "success": True,
            "cast": cast,
            "crew": crew
        }

    def get_cast_for_movie(self, tmdb_id):
        """Retrieves the cast for a specific movie."""
        cast = self.cast_crew_repo.get_cast_for_movie(tmdb_id)
        return {
            "success": True,
            "cast": cast
        }

    def get_crew_for_movie(self, tmdb_id):
        """Retrieves the crew for a specific movie."""
        crew = self.cast_crew_repo.get_crew_for_movie(tmdb_id)
        return {
            "success": True,
            "crew": crew
        }

    def get_director_for_movie(self, tmdb_id):
        """Retrieves the director for a specific movie."""
        director = self.cast_crew_repo.get_director_for_movie(tmdb_id)
        return {
            "success": True,
            "director": director
        }

    def find_tmdbids_by_cast(self, cast_name):
        return self.cast_crew_repo.find_tmdbids_by_cast(cast_name)

    def find_tmdbids_by_crew(self, crew_name, job=None):
        return self.cast_crew_repo.find_tmdbids_by_crew(crew_name)

    # Optional: Helper method to get a formatted list of actors and their roles
    def get_formatted_cast_list(self, tmdb_id):
        """Returns a list of strings like 'Name as Character' for the cast."""
        cast = self.cast_crew_repo.get_cast_for_movie(tmdb_id)
        formatted = [f"{person['name']} as {person['character']}" for person in cast]
        return {
            "success": True,
            "cast_list": formatted
        }

    # Optional: Helper method to get a formatted list of crew members by department/job
    def get_formatted_crew_list(self, tmdb_id):
        """Returns a dictionary grouping crew by department or job."""
        crew = self.cast_crew_repo.get_crew_for_movie(tmdb_id)
        formatted_crew = {}
        for person in crew:
            # Group by department first, then by job within department if needed
            dept = person.get('department', 'Other')
            job = person.get('job', 'N/A')
            name = person['name']

            if dept not in formatted_crew:
                formatted_crew[dept] = {}
            if job not in formatted_crew[dept]:
                formatted_crew[dept][job] = []
            formatted_crew[dept][job].append(name)
        
        return {
            "success": True,
            "crew_by_department": formatted_crew
        }

    def add_cast_member(self, tmdb_id, name, character):
        """Adds a cast member via the repository using name for collision."""
        if not all([tmdb_id, name, character]):
            return {"success": False, "message": "All fields (tmdbID, name, character) are required."}
        try:
            success = self.cast_crew_repo.add_cast_member(tmdb_id, name, character) # Removed actor_id from call
            if success:
                return {"success": True, "message": "Cast member added/updated successfully."}
            else:
                return {"success": False, "message": "Failed to add/update cast member (DB error)."}
        except Exception as e:
            print(f"Error in CastCrewService.add_cast_member: {e}")
            return {"success": False, "message": f"An error occurred: {e}"}

    def add_crew_member(self, tmdb_id, name, job, department):
        """Adds a crew member via the repository using name and job for collision."""
        # Basic validation - removed person_id check
        if not all([tmdb_id, name, job, department]):
            return {"success": False, "message": "All fields (tmdbID, name, job, department) are required."}
        try:
            success = self.cast_crew_repo.add_crew_member(tmdb_id, name, job, department) # Removed person_id from call
            if success:
                return {"success": True, "message": "Crew member added/updated successfully."}
            else:
                return {"success": False, "message": "Failed to add/update crew member (DB error)."}
        except Exception as e:
            print(f"Error in CastCrewService.add_crew_member: {e}")
            return {"success": False, "message": f"An error occurred: {e}"}

    def update_cast_member(self, tmdb_id, name, new_character):
        """Updates a cast member via the repository using name."""
        # Basic validation - removed actor_id check
        if not all([tmdb_id, name, new_character]):
            return {"success": False, "message": "tmdbID, name, and new_character are required."}
        try:
            success = self.cast_crew_repo.update_cast_member(tmdb_id, name, new_character) # Removed actor_id from call
            if success:
                return {"success": True, "message": "Cast member updated successfully."}
            else:
                return {"success": False, "message": "Failed to update cast member (not found or DB error)."}
        except Exception as e:
            print(f"Error in CastCrewService.update_cast_member: {e}")
            return {"success": False, "message": f"An error occurred: {e}"}

    def update_crew_member(self, tmdb_id, name, old_job, new_department, new_job=None):
        """Updates a crew member via the repository using name and old job."""
        # Basic validation - removed person_id check
        if not all([tmdb_id, name, old_job, new_department]):
            return {"success": False, "message": "tmdbID, name, old_job, and new_department are required."}
        try:
            success = self.cast_crew_repo.update_crew_member(tmdb_id, name, old_job, new_department, new_job) # Removed person_id from call
            if success:
                return {"success": True, "message": "Crew member updated successfully."}
            else:
                return {"success": False, "message": "Failed to update crew member (not found or DB error)."}
        except Exception as e:
            print(f"Error in CastCrewService.update_crew_member: {e}")
            return {"success": False, "message": f"An error occurred: {e}"}

    def delete_cast_member(self, tmdb_id, name):
        """Deletes a cast member via the repository using name."""
        # Basic validation - removed actor_id check
        if not all([tmdb_id, name]):
            return {"success": False, "message": "tmdbID and name are required."}
        try:
            success = self.cast_crew_repo.delete_cast_member(tmdb_id, name) # Removed actor_id from call
            if success:
                return {"success": True, "message": "Cast member deleted successfully."}
            else:
                return {"success": False, "message": "Failed to delete cast member (not found or DB error)."}
        except Exception as e:
            print(f"Error in CastCrewService.delete_cast_member: {e}")
            return {"success": False, "message": f"An error occurred: {e}"}

    def delete_crew_member(self, tmdb_id, name, job):
        """Deletes a crew member via the repository using name and job."""
        # Basic validation - removed person_id check
        if not all([tmdb_id, name, job]):
            return {"success": False, "message": "tmdbID, name, and job are required."}
        try:
            success = self.cast_crew_repo.delete_crew_member(tmdb_id, name, job) # Removed person_id from call
            if success:
                return {"success": True, "message": "Crew member deleted successfully."}
            else:
                return {"success": False, "message": "Failed to delete crew member (not found or DB error)."}
        except Exception as e:
            print(f"Error in CastCrewService.delete_crew_member: {e}")
            return {"success": False, "message": f"An error occurred: {e}"}
        
    def delete_all_cast_for_movie(self, tmdb_id):
        """
        Deletes all cast members for a specific movie via the repository.
        """
        try:
            success = self.cast_crew_repo.delete_all_cast_for_movie(tmdb_id)
            if success:
                print(f"DEBUG: Service: Successfully deleted all cast for tmdbID {tmdb_id}.")
                return {"success": True, "message": f"Deleted all cast for movie {tmdb_id}."}
            else:
                print(f"DEBUG: Service: Failed to delete all cast for tmdbID {tmdb_id}.")
                return {"success": False, "message": f"Failed to delete all cast for movie {tmdb_id} (DB error or connection issue)."}
        except Exception as e:
            print(f"Error in CastCrewService.delete_all_cast_for_movie: {e}")
            return {"success": False, "message": f"An error occurred: {e}"}

    def delete_all_crew_for_movie(self, tmdb_id):
        """
        Deletes all crew members for a specific movie via the repository.
        """
        try:
            success = self.cast_crew_repo.delete_all_crew_for_movie(tmdb_id)
            if success:
                print(f"DEBUG: Service: Successfully deleted all crew for tmdbID {tmdb_id}.")
                return {"success": True, "message": f"Deleted all crew for movie {tmdb_id}."}
            else:
                print(f"DEBUG: Service: Failed to delete all crew for tmdbID {tmdb_id}.")
                return {"success": False, "message": f"Failed to delete all crew for movie {tmdb_id} (DB error or connection issue)."}
        except Exception as e:
            print(f"Error in CastCrewService.delete_all_crew_for_movie: {e}")
            return {"success": False, "message": f"An error occurred: {e}"}