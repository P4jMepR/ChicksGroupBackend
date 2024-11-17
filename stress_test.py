import asyncio
import aiohttp
import random
import time
import statistics
from datetime import datetime
from typing import List, Dict
from dataclasses import dataclass
import signal
import sys

@dataclass
class RequestStats:
    response_time: float
    status_code: int
    success: bool
    input_values: Dict
    timestamp: float = None

class APIStressTester:
    def __init__(self, base_url: str, concurrent_requests: int):
        self.base_url = base_url
        self.concurrent_requests = concurrent_requests
        self.stats: List[RequestStats] = []
        self.running = True
        self.last_print_time = time.time()
        self.print_interval = 5  # Print stats every 5 seconds
        self.window_size = 10  # Look at last 10 seconds for slowest time

    def signal_handler(self, signum, frame):
        print("\nGracefully shutting down...")
        self.running = False

    def generate_random_input(self) -> Dict:
        """Generate random valid input values for the water jug problem"""
        # Keep capacities and target within reasonable bounds
        x_capacity = random.randint(1, 50)
        y_capacity = random.randint(1, 50)
        # Make sure target is achievable (less than max capacity)
        z_amount = random.randint(1, max(x_capacity, y_capacity))
        
        return {
            "x_capacity": x_capacity,
            "y_capacity": y_capacity,
            "z_amount_wanted": z_amount
        }

    async def make_request(self, session: aiohttp.ClientSession) -> RequestStats:
        """Make a single request to the API"""
        input_values = self.generate_random_input()
        
        start_time = time.time()
        try:
            async with session.post(f"{self.base_url}/api/solve", json=input_values) as response:
                await response.json()  # Ensure we read the response
                end_time = time.time()
                
                return RequestStats(
                    response_time=end_time - start_time,
                    status_code=response.status,
                    success=response.status == 200,
                    input_values=input_values
                )
        except Exception as e:
            end_time = time.time()
            print(f"Request failed: {str(e)}")
            return RequestStats(
                response_time=end_time - start_time,
                status_code=500,
                success=False,
                input_values=input_values
            )

    async def run_batch(self, session: aiohttp.ClientSession):
        """Run a batch of concurrent requests"""
        tasks = [self.make_request(session) for _ in range(self.concurrent_requests)]
        results = await asyncio.gather(*tasks)
        for result in results:
            result.timestamp = time.time()
        return results

    async def run_stress_test(self):
        """Run the stress test indefinitely until interrupted"""
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        async with aiohttp.ClientSession() as session:
            while self.running:
                batch_results = await self.run_batch(session)
                self.stats.extend(batch_results)
                
                # Keep only the last hour of stats to prevent memory issues
                current_time = time.time()
                self.stats = [stat for stat in self.stats 
                            if current_time - stat.timestamp < 3600]
                
                # Print real-time stats periodically
                if current_time - self.last_print_time >= self.print_interval:
                    self.print_results()
                    self.last_print_time = current_time

    def print_results(self):
        """Print detailed statistics about the stress test"""
        response_times = [stat.response_time for stat in self.stats]
        successful_requests = [stat for stat in self.stats if stat.success]
        failed_requests = [stat for stat in self.stats if not stat.success]

        # Get stats only from last 10 seconds for slowest time
        current_time = time.time()
        recent_stats = [
            stat.response_time 
            for stat in self.stats 
            if current_time - stat.timestamp <= self.window_size
        ]
        
        slowest_recent = max(recent_stats) if recent_stats else 0

        # Calculate requests per second
        if self.stats:
            time_window = time.time() - min(stat.timestamp for stat in self.stats)
            requests_per_second = len(self.stats) / time_window if time_window > 0 else 0
        else:
            requests_per_second = 0

        # Clear screen (works on most terminals)
        print("\033[H\033[J")  
        
        print(f"=== Stress Test Results at {datetime.now().strftime('%H:%M:%S')} ===")
        print(f"Requests in last hour: {len(self.stats)}")
        print(f"Requests/second: {requests_per_second:.2f}")
        print(f"Successful Requests: {len(successful_requests)}")
        print(f"Failed Requests: {len(failed_requests)}")
        
        if response_times:
            print(f"\nResponse Times (seconds):")
            print(f"Fastest: {min(response_times):.3f}")
            print(f"Slowest (10s window): {slowest_recent:.3f}")
            print(f"Average: {statistics.mean(response_times):.3f}")
            print(f"Median: {statistics.median(response_times):.3f}")
            if len(response_times) > 1:
                print(f"Std Dev: {statistics.stdev(response_times):.3f}")

        if failed_requests:
            print("\nRecent Failed Requests:")
            for stat in failed_requests[-5:]:  # Show last 5 failed requests
                print(f"Status: {stat.status_code}, Input: {stat.input_values}")

async def main():
    # Configuration
    BASE_URL = "http://localhost:8000"  # Adjust if your API is hosted elsewhere
    CONCURRENT_REQUESTS = 50  # Number of concurrent requests
    
    print(f"Starting infinite stress test at {datetime.now()}")
    print(f"Concurrent requests: {CONCURRENT_REQUESTS}")
    print("Press Ctrl+C to stop the test")
    
    tester = APIStressTester(BASE_URL, CONCURRENT_REQUESTS)
    await tester.run_stress_test()
    
    # Print final results after stopping
    print("\n=== Final Results ===")
    tester.print_results()

if __name__ == "__main__":
    asyncio.run(main()) 