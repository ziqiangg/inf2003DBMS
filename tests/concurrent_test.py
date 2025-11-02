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
                ['browse', 'search', 'view_detail', 'rate', 'review'],
                weights=[40, 25, 20, 10, 5]  # Weighted probability
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
                        reviews = ["Great!", "Good movie", "Not bad", "Amazing", "Decent"]
                        result = rating_service.review_service.add_review(
                            logged_user_id, movie['tmdbID'], random.choice(reviews)
                        )
                        success = result and result.get('success')
                
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


if __name__ == "__main__":
    # Configuration
    NUM_USERS = 10  # Number of concurrent users
    DURATION = 60   # Test duration in seconds
    
    simulator = ConcurrentUserSimulator(num_users=NUM_USERS, duration_seconds=DURATION)
    simulator.run_test()
