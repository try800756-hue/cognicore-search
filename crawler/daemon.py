import time
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from crawler.queue_runner import run_queue
from indexer.db import get_connection

def get_page_count():
    conn = get_connection()
    count = conn.cursor().execute("SELECT COUNT(*) FROM pages").fetchone()[0]
    conn.close()
    return count

def run_daemon(target_pages=100, delay_seconds=2):
    print(f"=== Cognicore Daemon Started ===")
    print(f"Target Index Size: {target_pages} pages")
    
    while True:
        current_count = get_page_count()
        if current_count >= target_pages:
            print(f"\n[DAEMON DONE] Reached target index count of {target_pages} pages!")
            break
            
        print(f"\n[DAEMON PASS] Current pages: {current_count}/{target_pages}")
        # Allow run_queue to fill up all remaining slots up to target_pages
        newly_added = run_queue(max_pages=target_pages)

        if newly_added == 0:
            print("\n[DAEMON IDLE] Queue is empty and no new links could be harvested. Exiting.")
            break

        time.sleep(delay_seconds)

if __name__ == "__main__":
    run_daemon(target_pages=100, delay_seconds=2)
