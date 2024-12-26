import os
import time
import random
import webbrowser
import re
from googlesearch import search
from concurrent.futures import ThreadPoolExecutor
from queue import Queue

# Configuration
DORK_FILE = 'dorks.txt'
SAVE_FILE = 'results.json'
RETRY_LIMIT = 3
BACKOFF_FACTOR = 2
RATE_LIMIT_SLEEP = 180  # 3 minutes
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 10; SM-G970F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.210 Mobile Safari/537.36",
]

HEADERS = {'User-Agent': random.choice(USER_AGENTS)}
rate_limited = False

# Utility Functions
def load_dorks(filename=DORK_FILE):
    try:
        if not os.path.exists(filename):
            print(f"[-] {filename} not found. Please create the file and add your dorks.")
            return []
        with open(filename, 'r') as file:
            return [line.strip() for line in file if line.strip()]
    except Exception as e:
        print(f"Error loading dorks file: {e}")
        return []

# Dork Searching
def google_dork_search(dork, pages_to_view, result_queue):
    global rate_limited
    try:
        for page_num in range(pages_to_view):
            if rate_limited:
                print("Rate limited, pausing dorking...")
                time.sleep(RATE_LIMIT_SLEEP)
                continue

            for attempt in range(RETRY_LIMIT):
                try:
                    user_agent = random.choice(USER_AGENTS)
                    search_results = search(
                        dork, num_results=10, start=page_num * 10, user_agent=user_agent
                    )
                    for url in search_results:
                        match = re.search(r'https?://(\d{1,3}\.(?:\d{1,3}\.){2}\d{1,3})', url)
                        if match:
                            result_queue.put(match.group(0))
                    time.sleep(10)  # Delay between requests
                    break
                except Exception as e:
                    print(f"Error on dork {dork}, page {page_num + 1}: {e}")
                    time.sleep(BACKOFF_FACTOR ** attempt)
    except Exception as e:
        print(f"Critical error in dork search: {e}")

# Result Management
def save_results(results, filename=SAVE_FILE):
    try:
        with open(filename, "w") as file:
            for dork, urls in results.items():
                file.write(f"Dork: {dork}\n")
                for url in urls:
                    file.write(f"{url}\n")
                file.write("\n")
        print(f"[+] Results saved to {filename}")
    except Exception as e:
        print(f"Error saving results: {e}")

def display_results(results, result_queue):
    page_size = 20
    current_page = 0
    results_set = set()

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

# Main Function
def main():
    print("[+] Loading dorks...")
    dorks = load_dorks()
    if not dorks:
        print("[-] No dorks loaded. Exiting...")
        return

    result_queue = Queue()
    results = {}

    print("[+] Starting dork search...")
    with ThreadPoolExecutor() as executor:
        for dork in dorks:
            executor.submit(google_dork_search, dork, 2, result_queue)

    display_results(results, result_queue)

if __name__ == "__main__":
    main()
