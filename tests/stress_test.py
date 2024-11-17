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
from colorama import init, Fore, Style

# Initialize colorama
init()

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
        self.print_interval = 2  # Print stats every 2 seconds (changed from 5)
        self.window_size = 10
        self.start_time = time.time()

    def signal_handler(self, signum, frame):
        print("\nGracefully shutting down...")
        self.running = False

    def gcd(self, a: int, b: int) -> int:
        """Calculate the Greatest Common Divisor of a and b"""
        while b:
            a, b = b, a % b
        return a

    def is_valid_input(self, input_values: Dict) -> bool:
        """Check if the input values are valid for the water jug problem"""
        x_capacity = input_values["x_capacity"]
        y_capacity = input_values["y_capacity"]
        z_amount = input_values["z_amount_wanted"]
        
        # Basic validation rules
        if x_capacity <= 0 or y_capacity <= 0 or z_amount <= 0:
            return False
        
        # Target amount should be less than or equal to the larger jug
        if z_amount > max(x_capacity, y_capacity):
            return False
        
        # Check if the target is achievable using GCD
        gcd_value = self.gcd(x_capacity, y_capacity)
        if z_amount % gcd_value != 0:
            return False
        
        return True

    def generate_random_input(self) -> Dict:
        """Generate random valid input values for the water jug problem"""
        while True:
            # Keep capacities within reasonable bounds
            x_capacity = random.randint(1, 50)
            y_capacity = random.randint(1, 50)
            
            # Calculate GCD
            gcd_value = self.gcd(x_capacity, y_capacity)
            
            # Generate a target that's guaranteed to be achievable
            # by making it a multiple of GCD and less than the larger jug
            max_target = min(max(x_capacity, y_capacity), 50)
            possible_multiples = range(gcd_value, max_target + 1, gcd_value)
            
            if not possible_multiples:
                continue
            
            z_amount = random.choice(list(possible_multiples))
            
            input_values = {
                "x_capacity": x_capacity,
                "y_capacity": y_capacity,
                "z_amount_wanted": z_amount
            }
            
            if self.is_valid_input(input_values):
                return input_values

    async def make_request(self, session: aiohttp.ClientSession) -> RequestStats:
        """Make a single request to the API"""
        input_values = self.generate_random_input()
        
        # Skip invalid inputs
        if not self.is_valid_input(input_values):
            return None
        
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
        # Filter out None results (invalid inputs) and add timestamps
        valid_results = [result for result in results if result is not None]
        for result in valid_results:
            result.timestamp = time.time()
        return valid_results

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
        """Print detailed statistics about the stress test with colors"""
        response_times = [stat.response_time for stat in self.stats]
        successful_requests = [stat for stat in self.stats if stat.success]
        failed_requests = [stat for stat in self.stats if not stat.success]

        # Get stats from last 10 seconds for recent performance
        current_time = time.time()
        recent_stats = [
            stat.response_time 
            for stat in self.stats 
            if current_time - stat.timestamp <= self.window_size
        ]
        
        slowest_recent = max(recent_stats) if recent_stats else 0
        
        # Calculate requests per second
        time_window = time.time() - min(stat.timestamp for stat in self.stats) if self.stats else 0
        requests_per_second = len(self.stats) / time_window if time_window > 0 else 0
        
        # Calculate success rate percentage
        success_rate = (len(successful_requests) / len(self.stats) * 100) if self.stats else 0
        
        # Calculate throughput (requests/minute)
        total_time = time.time() - self.start_time
        throughput = len(self.stats) / (total_time / 60) if total_time > 0 else 0

        # Calculate test duration
        duration = time.time() - self.start_time
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)
        duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        # Pretty printing with colors
        print("\033[2J\033[H")  # Clear screen and move cursor to top
        print(f"{Fore.CYAN}╔══════════════════════════════════════════════════════════╗{Style.RESET_ALL}")
        print(f"{Fore.CYAN}║                     API STRESS TEST                      ║{Style.RESET_ALL}")
        print(f"{Fore.CYAN}╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Test Duration: {duration_str}{Style.RESET_ALL}")
        
        print(f"\n{Fore.MAGENTA}Performance Metrics:{Style.RESET_ALL}")
        print(f"  • Requests/sec: {Fore.GREEN}{requests_per_second:.2f}{Style.RESET_ALL}")
        print(f"  • Throughput: {Fore.GREEN}{throughput:.1f}{Style.RESET_ALL} req/min")
        print(f"  • Success Rate: {self._get_colored_percentage(success_rate)}")
        
        print(f"\n{Fore.BLUE}Response Times:{Style.RESET_ALL}")
        if response_times:
            print(f"  • Fastest: {Fore.GREEN}{min(response_times):.3f}s{Style.RESET_ALL}")
            print(f"  • Average: {Fore.YELLOW}{statistics.mean(response_times):.3f}s{Style.RESET_ALL}")
            print(f"  • Slowest (10s window): {Fore.RED}{slowest_recent:.3f}s{Style.RESET_ALL}")
        
        print(f"\n{Fore.LIGHTCYAN_EX}Traffic Stats:{Style.RESET_ALL}")
        print(f"  • Total Requests: {Fore.GREEN}{len(self.stats)}{Style.RESET_ALL}")
        print(f"  • Successful: {Fore.GREEN}{len(successful_requests)}{Style.RESET_ALL}")
        print(f"  • Failed: {Fore.RED}{len(failed_requests)}{Style.RESET_ALL}")

        if failed_requests:
            print(f"\n{Fore.RED}Latest Failures:{Style.RESET_ALL}")
            for stat in failed_requests[-3:]:  # Show last 3 failed requests
                print(f"  • Status {stat.status_code}: {stat.input_values}")

    def _get_colored_percentage(self, percentage: float) -> str:
        """Return colored percentage based on value"""
        if percentage >= 90:
            color = Fore.GREEN
        elif percentage >= 75:
            color = Fore.YELLOW
        else:
            color = Fore.RED
        return f"{color}{percentage:.1f}%{Style.RESET_ALL}"

async def main():
    # Configuration
    BASE_URL = "http://localhost:8000"
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