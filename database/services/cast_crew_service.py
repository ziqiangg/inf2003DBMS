# database/services/cast_crew_service.py
from database.repositories.cast_crew_repository import CastCrewRepository

class CastCrewService:
    def __init__(self):
        self.cast_crew_repo = CastCrewRepository()

    def get_full_cast_and_crew(self, tmdb_id):
        """Retrieves both cast and crew for a specific movie."""
        cast = self.cast_crew_repo.get_cast_for_movie(tmdb_id)
        crew = self.cast_crew_repo.get_crew_for_movie(tmdb_id)
        return {
            "cast": cast,
            "crew": crew
        }

    def get_cast_for_movie(self, tmdb_id):
        """Retrieves the cast for a specific movie."""
        return self.cast_crew_repo.get_cast_for_movie(tmdb_id)

    def get_crew_for_movie(self, tmdb_id):
        """Retrieves the crew for a specific movie."""
        return self.cast_crew_repo.get_crew_for_movie(tmdb_id)

    def get_director_for_movie(self, tmdb_id):
        """Retrieves the director for a specific movie."""
        return self.cast_crew_repo.get_director_for_movie(tmdb_id)

    # Optional: Helper method to get a formatted list of actors and their roles
    def get_formatted_cast_list(self, tmdb_id):
        """Returns a list of strings like 'Name as Character' for the cast."""
        cast = self.get_cast_for_movie(tmdb_id)
        return [f"{person['name']} as {person['character']}" for person in cast]

    # Optional: Helper method to get a formatted list of crew members by department/job
    def get_formatted_crew_list(self, tmdb_id):
        """Returns a dictionary grouping crew by department or job."""
        crew = self.get_crew_for_movie(tmdb_id)
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
        return formatted_crew
