import os
from googlesearch import search
import time
import random
import webbrowser
import queue
from threading import Thread

# Constants for rate-limiting
RATE_LIMIT_SLEEP = 180  # 3 minutes
TOO_MANY_REQUESTS_SLEEP = 60  # 1 minute

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.54",
    "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36",
]

class RateLimiter:
    def __init__(self):
        self.rate_limited = False

    def check_limit(self):
        if self.rate_limited:
            print("\033[91mRate limited! Pausing for 3 minutes...\033[0m")
            time.sleep(RATE_LIMIT_SLEEP)
            self.rate_limited = False

    def set_limit(self, too_many_requests=False):
        if too_many_requests:
            print("\033[91mToo many requests! Pausing for 1 minute...\033[0m")
            time.sleep(TOO_MANY_REQUESTS_SLEEP)
        else:
            self.rate_limited = True

def banner():
    print("""hey sexy camera""")

def load_dorks(filename="dorks.txt"):
    if not os.path.exists(filename):
        print(f"[-] Dorks file '{filename}' not found. Please provide a valid file.")
        return []
    with open(filename, "r") as file:
        dorks = [line.strip() for line in file if line.strip()]
    print(f"[+] Loaded {len(dorks)} dorks from '{filename}'")
    return dorks

def perform_dorking(dorks, stop_results, result_queue=None, rate_limiter=None, results_file="coupon_dorks_results.txt"):
    results_set = set()
    if os.path.exists(results_file):
        with open(results_file, "r") as file:
            results_set.update([line.strip() for line in file if line.strip()])

    for dork in dorks:
        retry_count = 0  # Keep track of retries for the current dork
        while retry_count < 10:  # Auto-retry up to 10 times
            print(f"\n[+] Searching for: {dork} (Attempt {retry_count + 1}/10)")
            try:
                if rate_limiter:
                    rate_limiter.check_limit()

                user_agent = random.choice(USER_AGENTS)
                for result in search(dork, stop=stop_results, lang="en", user_agent=user_agent):
                    if result not in results_set:
                        print(f" - {result}")
                        results_set.add(result)
                        with open(results_file, "a") as file:
                            file.write(f"{result}\n")
                        if result_queue:
                            result_queue.put(result)
                    time.sleep(8)  # Add a delay of 8 seconds between queries
                break  # Exit the retry loop if successful

            except Exception as e:
                retry_count += 1
                if "429" in str(e):  # Too Many Requests
                    print(f"Rate limit encountered for dork: {dork}. Pausing before retry...")
                    if rate_limiter:
                        rate_limiter.set_limit(too_many_requests=True)
                else:
                    print(f"Error searching with dork: {dork}. Error: {e}")
                    if rate_limiter:
                        rate_limiter.set_limit()

        # If the dork still fails after 10 retries, prompt the user for further action
        if retry_count == 10:
            while True:
                action = input(f"Max retries reached for '{dork}'. Retry another 10 times (r) or Skip (s): ").strip().lower()
                if action == "s":
                    print(f"Skipping dork: {dork}")
                    break  # Exit the retry loop and move to the next dork
                elif action == "r":
                    print(f"Retrying dork: {dork} for another 10 attempts...")
                    retry_count = 0  # Reset retry counter and retry
                    continue
                else:
                    print("Invalid choice. Please enter 'r' to retry or 's' to skip.")

    print("\n[+] Dorking process completed.")

def display_results(result_queue, results_file="coupon_dorks_results.txt"):
    page_size = 20
    current_page = 0
    results_set = set()

    if os.path.exists(results_file):
        with open(results_file, "r") as file:
            results_set.update([line.strip() for line in file if line.strip()])

    while True:
        while not result_queue.empty():
            results_set.add(result_queue.get())
        results = list(results_set)
        total_pages = (len(results) + page_size - 1) // page_size

        os.system('cls' if os.name == 'nt' else 'clear')
        print("\033[92mResults containing IP addresses:\033[0m")
        if results:
            start = current_page * page_size
            end = start + page_size
            for i, result in enumerate(results[start:end], start=1):
                print(f"[{start + i}] {result}")
            print(f"\nPage {current_page + 1}/{total_pages}")
        else:
            print("No results yet. Waiting...")

        choice = input("n - Next | p - Prev | q - Quit | Enter number to open: ").strip()
        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(results):
                webbrowser.open(results[index])
        elif choice == 'n' and current_page < total_pages - 1:
            current_page += 1
        elif choice == 'p' and current_page > 0:
            current_page -= 1
        elif choice == 'q':
            break
        else:
            print("Invalid choice. Try again.")

def main():
    banner()
    dorks_file = input("Enter the dorks filename (default: dorks.txt): ").strip() or "dorks.txt"
    dorks = load_dorks(dorks_file)
    if not dorks:
        return

    stop_results = int(input("Enter the number of results to retrieve per dork: "))
    result_queue = queue.Queue()
    rate_limiter = RateLimiter()

    # Start the dorking in a separate thread
    dorking_thread = Thread(target=perform_dorking, args=(dorks, stop_results, result_queue, rate_limiter))
    dorking_thread.start()

    # Display results dynamically
    display_results(result_queue)

    dorking_thread.join()

if __name__ == "__main__":
    main()
