import requests
from bs4 import BeautifulSoup
import re
import os
import webbrowser
import json
import time
from queue import Queue
from threading import Thread
import random
import subprocess

# Configuration
DORK_FILE = 'dorks.txt'
SAVE_FILE = 'results.json'
RETRY_LIMIT = 3
BACKOFF_FACTOR = 2
RATE_LIMIT_SLEEP = 180  # 3 minutes

# User-Agent rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 10; SM-G970F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.210 Mobile Safari/537.36",
]

HEADERS = {'User-Agent': random.choice(USER_AGENTS)}

# Shared state for rate limiting status
rate_limited = False

# Load dorks from file
def load_dorks():
    try:
        with open(DORK_FILE, 'r') as file:
            return [line.strip() for line in file if line.strip()]
    except Exception as e:
        print(f"Error loading dorks file: {e}")
        return []


# Perform Google dorking
def google_dork_search(dork, pages_to_view, result_queue, verbose_proc):
    global rate_limited  # Access shared variable for rate limit status

    search_url_base = "https://www.google.com/search?q="
    for page_num in range(pages_to_view):
        search_url = f"{search_url_base}{dork}&start={page_num * 10}"  # Google paginates with 'start'

        for attempt in range(RETRY_LIMIT):
            try:
                if rate_limited:
                    verbose_proc.stdin.write("Rate limited, pausing dorking...\n")
                    verbose_proc.stdin.flush()
                    time.sleep(RATE_LIMIT_SLEEP)
                    continue

                response = requests.get(search_url, headers=HEADERS)

                if response.status_code == 429:  # Rate limited
                    rate_limited = True  # Update rate limit status
                    verbose_proc.stdin.write("Rate limited! Sleeping for 3 minutes...\n")
                    verbose_proc.stdin.flush()
                    time.sleep(RATE_LIMIT_SLEEP)
                    continue

                if response.status_code != 200:
                    verbose_proc.stdin.write(f"HTTP error {response.status_code} for {search_url}\n")
                    verbose_proc.stdin.flush()
                    time.sleep(BACKOFF_FACTOR ** attempt)  # Exponential backoff
                    continue

                soup = BeautifulSoup(response.text, 'html.parser')

                # Extract URLs from search results
                for link in soup.find_all('a', href=True):
                    url = link['href']
                    match = re.search(r'https?://(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', url)  # Strict IP regex
                    if match:
                        result_queue.put(match.group(0))  # Add the valid IP URL to results

                verbose_proc.stdin.write(f"Successfully processed page {page_num + 1} of dork: {dork}\n")
                verbose_proc.stdin.flush()

                time.sleep(10)  # Delay between page requests
                break
            except Exception as e:
                verbose_proc.stdin.write(f"Error during Google dork search for {search_url}: {e}\n")
                verbose_proc.stdin.flush()
                time.sleep(BACKOFF_FACTOR ** attempt)


# Run background tasks for Google dorking
def run_background_tasks(result_queue, dorks, pages_to_view, verbose_proc):
    with ThreadPoolExecutor() as executor:
        # Submit tasks for Google dorking concurrently
        future_dorks = [executor.submit(google_dork_search, dork, pages_to_view, result_queue, verbose_proc) for dork in dorks]

        # Wait for all futures to complete
        for future in future_dorks:
            future.result()  # Wait for all dorking tasks to finish


# Display results menu
def display_results(results, result_queue, thread, verbose_proc):
    global rate_limited  # Access shared variable for rate limit status
    page_size = 20
    current_page = 0

    while True:
        # Check for new results in the queue
        while not result_queue.empty():
            results.append(result_queue.get())
        results = list(set(results))  # Deduplicate results
        total_pages = (len(results) + page_size - 1) // page_size  # Update total pages dynamically

        # Clear the console for a clean display
        os.system('cls' if os.name == 'nt' else 'clear')

        # Dynamic rate limiting message
        if rate_limited:
            print("\033[91mRate limited! Sleeping for 3 minutes...\033[0m")
        else:
            print("\033[92mReady to go! No rate limit.\033[0m")

        print("\033[92mResults containing IP addresses:\033[0m")
        if results:
            start = current_page * page_size
            end = start + page_size

            for i, result in enumerate(results[start:end], start=1):
                print(f"\033[92m[{start + i}] {result}\033[0m")

            print(f"\nPage {current_page + 1}/{total_pages}")
        else:
            print("No results found yet. Waiting for new results...")

        print("n - Next Page | p - Previous Page | r - Refresh Results | c - Continue Dorking | q - Quit | Select a number to open URL")

        choice = input("Enter choice: ").strip().lower()

        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(results):
                webbrowser.open(results[index])
        elif choice == 'n' and current_page < total_pages - 1:
            current_page += 1
        elif choice == 'p' and current_page > 0:
            current_page -= 1
        elif choice == 'r':
            print("Refreshing results...")
        elif choice == 'c':
            if not thread.is_alive():
                print("Fetching has completed. No new results.")
            else:
                print("Fetching in progress. Waiting for new results...")
        elif choice == 'q':
            break
        else:
            print("Invalid choice. Please try again.")
        time.sleep(1)


# Dynamic Rate Limiting Check
def check_rate_limiting(verbose_proc):
    global rate_limited  # Access shared variable for rate limit status
    test_url = "https://www.google.com/search?q=intitle:D-Link Internet Camera&start=0"
    headers = {'User-Agent': random.choice(USER_AGENTS)}

    while True:
        try:
            response = requests.get(test_url, headers=headers)

            if response.status_code == 429:  # Rate limit detected
                rate_limited = True
                verbose_proc.stdin.write("Rate limited! Sleeping for 3 minutes...\n".encode())  # Encode to bytes
                verbose_proc.stdin.flush()
                time.sleep(RATE_LIMIT_SLEEP)
            else:
                if rate_limited:
                    rate_limited = False  # Reset rate-limited flag
                    verbose_proc.stdin.write("No longer rate limited. Let's go!\n".encode())  # Encode to bytes
                    verbose_proc.stdin.flush()
                time.sleep(10)  # Check every 10 seconds
        except Exception as e:
            verbose_proc.stdin.write(f"Error during rate limiting check: {e}\n".encode())  # Encode to bytes
            verbose_proc.stdin.flush()
            time.sleep(10)


# Start verbose mode
def start_verbose_mode():
    verbose_proc = subprocess.Popen(['bash'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    verbose_proc.stdin.write("Verbose mode started. Monitoring actions...\n".encode())  # Encoding the string as bytes
    verbose_proc.stdin.flush()
    return verbose_proc

# Main execution
def main():
    use_saved = input("Use saved results? (y/n): ").strip().lower()
    if use_saved == 'y':
        all_results = load_saved_results()
    else:
        try:
            pages_to_view = int(input("How many pages to view per dork search? (e.g., 50): ").strip())
            if pages_to_view <= 0:
                print("Invalid number of pages. Defaulting to 50.")
                pages_to_view = 50
        except ValueError:
            print("Invalid input. Defaulting to 50.")
            pages_to_view = 50

        result_queue = Queue()  # Thread-safe queue for results
        dorks = load_dorks()

        if not dorks:
            print("No dorks found in the dorks file. Exiting.")
            return

        print("Starting background tasks...")

        # Start the verbose mode
        verbose_proc = start_verbose_mode()

        # Start the rate-limiting check in a separate thread
        rate_limit_thread = Thread(target=check_rate_limiting, args=(verbose_proc,))
        rate_limit_thread.daemon = True  # Allow the program to exit even if the thread is still running
        rate_limit_thread.start()

        # Start background tasks for Google dorking
        thread = Thread(target=run_background_tasks, args=(result_queue, dorks, pages_to_view, verbose_proc))
        thread.daemon = True  # Allow the program to exit even if the thread is still running
        thread.start()

        # Initialize results
        all_results = []
        display_results(all_results, result_queue, thread, verbose_proc)

        # Save results after dorking
        save_results(all_results)
        print(f"Results saved to {SAVE_FILE}. Total {len(all_results)} unique IP addresses found.")


if __name__ == '__main__':
    main()
