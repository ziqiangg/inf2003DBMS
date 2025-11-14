"""
Concurrent User Test - Direct Database Operations
Run with: python concurrent_test.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.services.user_service import UserService
from database.services.movie_service import MovieService
from database.services.rating_service import RatingService
from database.db_connection import MySQLConnectionManager
from database.db_mongo_connection import MongoConnectionManager
import threading
import time
import random
from collections import defaultdict
import statistics
import matplotlib.pyplot as plt
import numpy as np


class ConcurrentUserSimulator:
    def __init__(self, num_users=10, duration_seconds=60):
        self.num_users = num_users
        self.duration_seconds = duration_seconds
        self.results = defaultdict(list)
        self.errors = defaultdict(int)
        self.lock = threading.Lock()
        
        # Initialize connection managers
        self.mysql_manager = MySQLConnectionManager()
        self.mongo_manager = MongoConnectionManager()
        self.mysql_manager.initialize_pool(pool_size=20)
        self.mongo_manager.initialize_connection()
    
    def simulate_user(self, user_id):
        """Simulate a single user's behavior"""
        # Initialize services for this thread
        user_service = UserService()
        movie_service = MovieService()
        rating_service = RatingService()
        
        # Register and login
        test_email = f"concurrent_test_{user_id}_{random.randint(1000, 9999)}@test.com"
        register_result = user_service.register_user(test_email, "TestPass123")
        
        if not register_result['success']:
            print(f"✗ User {user_id}: Registration failed")
            return
        
        login_result = user_service.login_user(test_email, "TestPass123")
        if not login_result['success']:
            print(f"✗ User {user_id}: Login failed")
            return
        
        logged_user_id = login_result['user_id']
        print(f"✓ User {user_id}: Logged in as {test_email}")
        
        start_time = time.time()
        operations_count = 0
        
        while (time.time() - start_time) < self.duration_seconds:
            # Randomly choose an operation
            operation = random.choices(
                ['browse', 'search', 'view_detail', 'rate', 'review', 'profile', 'get_cast', 'get_reviews', 'check_rating', 'update_rating', 'delete_rating', 'advanced_search', 'paginate_search', 'cast_crew_search'],
                weights=[15, 12, 10, 8, 4, 4, 6, 5, 4, 3, 2, 8, 6, 5]  # Weighted probability - advanced operations moderately frequent
            )[0]
            
            op_start = time.time()
            success = False
            
            try:
                if operation == 'browse':
                    result = movie_service.get_movies_for_homepage(
                        page_number=random.randint(1, 5),
                        movies_per_page=20
                    )
                    success = result and len(result.get('movies', [])) > 0
                
                elif operation == 'search':
                    search_terms = ["action", "comedy", "the", "love", "star"]
                    result = movie_service.search_movies_by_title(
                        search_term=random.choice(search_terms),
                        page_number=1
                    )
                    success = result and 'movies' in result
                
                elif operation == 'view_detail':
                    browse = movie_service.get_movies_for_homepage(page_number=1, movies_per_page=20)
                    if browse and browse['movies']:
                        movie = random.choice(browse['movies'])
                        result = movie_service.get_movie_detail(movie['tmdbID'])
                        success = result and result.get('success')
                
                elif operation == 'rate':
                    browse = movie_service.get_movies_for_homepage(page_number=1, movies_per_page=20)
                    if browse and browse['movies']:
                        movie = random.choice(browse['movies'])
                        rating_value = random.choice([1.0, 2.0, 3.0, 4.0, 5.0])
                        result = rating_service.add_rating(logged_user_id, movie['tmdbID'], rating_value)
                        success = result and result.get('success')
                
                elif operation == 'review':
                    browse = movie_service.get_movies_for_homepage(page_number=1, movies_per_page=20)
                    if browse and browse['movies']:
                        movie = random.choice(browse['movies'])
                        reviews = ["Great!", "Good movie", "Not bad", "Amazing", "Decent", "Excellent!", "Poor", "Masterpiece"]
                        result = rating_service.review_service.add_review(
                            logged_user_id, movie['tmdbID'], random.choice(reviews)
                        )
                        success = result and result.get('success')
                
                elif operation == 'profile':
                    # View user's own profile (ratings and reviews)
                    result = rating_service.get_user_ratings_and_reviews_for_profile(logged_user_id)
                    success = result and result.get('success')
                
                elif operation == 'get_cast':
                    # Get cast information for a movie (common when viewing details)
                    browse = movie_service.get_movies_for_homepage(page_number=1, movies_per_page=20)
                    if browse and browse['movies']:
                        movie = random.choice(browse['movies'])
                        from database.services.cast_crew_service import CastCrewService
                        cast_service = CastCrewService()
                        result = cast_service.get_formatted_cast_list(movie['tmdbID'])
                        success = result and result.get('success')
                
                elif operation == 'get_reviews':
                    # Get all reviews for a movie (when viewing movie details)
                    browse = movie_service.get_movies_for_homepage(page_number=1, movies_per_page=20)
                    if browse and browse['movies']:
                        movie = random.choice(browse['movies'])
                        result = rating_service.review_service.get_reviews_for_movie(movie['tmdbID'])
                        success = result and result.get('success')
                
                elif operation == 'check_rating':
                    # Check if user has already rated a movie (when viewing movie details)
                    browse = movie_service.get_movies_for_homepage(page_number=1, movies_per_page=20)
                    if browse and browse['movies']:
                        movie = random.choice(browse['movies'])
                        result = rating_service.get_user_rating_for_movie(logged_user_id, movie['tmdbID'])
                        success = result and result.get('success')
                
                elif operation == 'update_rating':
                    # Update an existing rating (user changes their mind)
                    browse = movie_service.get_movies_for_homepage(page_number=1, movies_per_page=20)
                    if browse and browse['movies']:
                        movie = random.choice(browse['movies'])
                        # First check if rating exists
                        existing = rating_service.get_user_rating_for_movie(logged_user_id, movie['tmdbID'])
                        if existing and existing.get('rating'):
                            new_rating = random.choice([1.0, 2.0, 3.0, 4.0, 5.0])
                            result = rating_service.update_rating(logged_user_id, movie['tmdbID'], new_rating)
                            success = result and result.get('success')
                        else:
                            # No existing rating, just add one
                            rating_value = random.choice([1.0, 2.0, 3.0, 4.0, 5.0])
                            result = rating_service.add_rating(logged_user_id, movie['tmdbID'], rating_value)
                            success = result and result.get('success')
                
                elif operation == 'delete_rating':
                    # Delete a rating (user removes their rating)
                    browse = movie_service.get_movies_for_homepage(page_number=1, movies_per_page=20)
                    if browse and browse['movies']:
                        movie = random.choice(browse['movies'])
                        # Check if rating exists before trying to delete
                        existing = rating_service.get_user_rating_for_movie(logged_user_id, movie['tmdbID'])
                        if existing and existing.get('rating'):
                            result = rating_service.delete_rating(logged_user_id, movie['tmdbID'])
                            success = result and result.get('success')
                        else:
                            success = True  # No rating to delete is also success
                
                elif operation == 'advanced_search':
                    # Advanced search with genre, year, and rating filters
                    genres = ["Action", "Comedy", "Drama", "Horror", "Romance", "Sci-Fi", "Thriller"]
                    years = [2020, 2015, 2010, 2000, 1990]
                    min_ratings = [3.0, 4.0, 4.5]
                    
                    result = movie_service.search_movies_by_title(
                        search_term=random.choice(["the", "a", "of", "and", "to"]),
                        genres=random.choice(genres),
                        year=random.choice(years),
                        min_avg_rating=random.choice(min_ratings),
                        page_number=1,
                        movies_per_page=20
                    )
                    success = result and 'movies' in result
                
                elif operation == 'paginate_search':
                    # Paginate through search results (simulate user browsing multiple pages)
                    search_terms = ["action", "comedy", "love", "star", "movie"]
                    result = movie_service.search_movies_by_title(
                        search_term=random.choice(search_terms),
                        page_number=random.randint(1, 3),  # Browse different pages
                        movies_per_page=20
                    )
                    success = result and 'movies' in result
                
                elif operation == 'cast_crew_search':
                    # Search by cast/crew names
                    cast_names = ["John", "Mary", "David", "Sarah", "Michael", "Jennifer"]
                    crew_names = ["Steven", "Martin", "Christopher", "James", "William"]
                    
                    # Randomly choose between cast or crew search
                    if random.choice([True, False]):
                        # Cast search
                        result = movie_service.search_movies_by_title(
                            cast=random.choice(cast_names),
                            page_number=1,
                            movies_per_page=20
                        )
                    else:
                        # Crew search
                        result = movie_service.search_movies_by_title(
                            crew=random.choice(crew_names),
                            page_number=1,
                            movies_per_page=20
                        )
                    success = result and 'movies' in result
                
                op_time = (time.time() - op_start) * 1000  # Convert to ms
                
                with self.lock:
                    self.results[operation].append(op_time)
                    if not success:
                        self.errors[operation] += 1
                
                operations_count += 1
                
                # Small delay to simulate user think time
                time.sleep(random.uniform(0.5, 2.0))
                
            except Exception as e:
                with self.lock:
                    self.errors[operation] += 1
                print(f"✗ User {user_id}: {operation} error - {e}")
        
        print(f"✓ User {user_id}: Completed {operations_count} operations")
    
    def run_test(self):
        """Run the concurrent user simulation"""
        print(f"\n{'='*60}")
        print(f"Starting Concurrent User Test")
        print(f"Users: {self.num_users} | Duration: {self.duration_seconds}s")
        print(f"{'='*60}\n")
        
        threads = []
        start_time = time.time()
        
        # Spawn user threads
        for i in range(self.num_users):
            thread = threading.Thread(target=self.simulate_user, args=(i,))
            thread.start()
            threads.append(thread)
            time.sleep(0.1)  # Stagger thread starts
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Print results
        self.print_results(total_time)
    
    def print_results(self, total_time):
        """Print test results and statistics"""
        print(f"\n{'='*60}")
        print(f"Test Completed in {total_time:.2f}s")
        print(f"{'='*60}\n")
        
        total_operations = sum(len(times) for times in self.results.values())
        total_errors = sum(self.errors.values())
        
        print(f"Total Operations: {total_operations}")
        print(f"Total Errors: {total_errors}")
        print(f"Success Rate: {((total_operations - total_errors) / total_operations * 100):.2f}%")
        print(f"Throughput: {total_operations / total_time:.2f} ops/sec\n")
        
        print(f"{'Operation':<15} {'Count':<8} {'Errors':<8} {'Min(ms)':<10} {'Avg(ms)':<10} {'Max(ms)':<10} {'p95(ms)':<10}")
        print(f"{'-'*80}")
        
        for operation, times in sorted(self.results.items()):
            if times:
                count = len(times)
                errors = self.errors[operation]
                min_time = min(times)
                avg_time = statistics.mean(times)
                max_time = max(times)
                p95_time = statistics.quantiles(times, n=20)[18] if len(times) > 1 else avg_time
                
                print(f"{operation:<15} {count:<8} {errors:<8} {min_time:<10.2f} {avg_time:<10.2f} {max_time:<10.2f} {p95_time:<10.2f}")
        
        print(f"\n{'='*60}\n")
        
        # Generate visualizations
        self.generate_visualizations(total_time)
    
    def generate_visualizations(self, total_time):
        """Generate performance visualizations"""
        try:
            # Set up the plotting style
            plt.style.use('default')
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle(f'Concurrent User Test Results ({self.num_users} users, {self.duration_seconds}s)', fontsize=16, fontweight='bold')
            
            # 1. Operation Distribution Pie Chart
            operations = list(self.results.keys())
            counts = [len(self.results[op]) for op in operations]
            ax1.pie(counts, labels=operations, autopct='%1.1f%%', startangle=90)
            ax1.set_title('Operation Distribution')
            ax1.axis('equal')
            
            # 2. Response Time Box Plot
            if self.results:
                data = [self.results[op] for op in operations if self.results[op]]
                ax2.boxplot(data, labels=operations)
                ax2.set_title('Response Time Distribution (ms)')
                ax2.set_ylabel('Response Time (ms)')
                ax2.grid(True, alpha=0.3)
            
            # 3. Average Response Times Bar Chart
            if self.results:
                avg_times = []
                for op in operations:
                    if self.results[op]:
                        avg_times.append(statistics.mean(self.results[op]))
                    else:
                        avg_times.append(0)
                
                bars = ax3.bar(operations, avg_times, color='skyblue', edgecolor='navy', alpha=0.7)
                ax3.set_title('Average Response Times by Operation')
                ax3.set_ylabel('Average Time (ms)')
                ax3.set_xlabel('Operation')
                ax3.grid(True, alpha=0.3)
                
                # Add value labels on bars
                for bar, time in zip(bars, avg_times):
                    height = bar.get_height()
                    ax3.text(bar.get_x() + bar.get_width()/2., height + 5,
                            f'{time:.1f}ms', ha='center', va='bottom', fontweight='bold')
            
            # 4. Throughput Timeline (simulated)
            total_ops = sum(len(self.results[op]) for op in operations)
            throughput_over_time = []
            time_points = []
            
            # Simulate throughput over time (assuming uniform distribution)
            for i in range(0, int(total_time) + 1, 5):
                time_points.append(i)
                # Calculate operations completed by this time point
                ops_by_time = int((i / total_time) * total_ops)
                throughput_over_time.append(ops_by_time / max(i, 1))  # ops per second
            
            ax4.plot(time_points, throughput_over_time, 'g-', linewidth=2, marker='o')
            ax4.set_title('Throughput Over Time')
            ax4.set_xlabel('Time (seconds)')
            ax4.set_ylabel('Operations per Second')
            ax4.grid(True, alpha=0.3)
            ax4.set_xlim(0, max(time_points))
            
            plt.tight_layout()
            plt.savefig('concurrency_test_results.png', dpi=300, bbox_inches='tight')
            print("Performance visualizations saved as 'concurrency_test_results.png'")
            
            # Show throughput summary
            print(f"\nThroughput Analysis:")
            print(f"- Peak Throughput: {max(throughput_over_time):.2f} ops/sec")
            print(f"- Average Throughput: {total_ops / total_time:.2f} ops/sec")
            print(f"- Total Operations: {total_ops}")
            
            # Response time analysis
            all_times = []
            for times in self.results.values():
                all_times.extend(times)
            
            if all_times:
                print(f"\nResponse Time Analysis:")
                print(f"- Overall Average: {statistics.mean(all_times):.2f}ms")
                print(f"- 95th Percentile: {statistics.quantiles(all_times, n=20)[18]:.2f}ms")
                print(f"- Max Response Time: {max(all_times):.2f}ms")
                print(f"- Min Response Time: {min(all_times):.2f}ms")
            
        except ImportError:
            print("Matplotlib not available for visualization. Install with: pip install matplotlib")
        except Exception as e:
            print(f"Error generating visualizations: {e}")


if __name__ == "__main__":
    # Configuration
    NUM_USERS = 8  # Reduced for quicker test
    DURATION = 30   # Reduced duration for quicker test
    
    simulator = ConcurrentUserSimulator(num_users=NUM_USERS, duration_seconds=DURATION)
    simulator.run_test()
