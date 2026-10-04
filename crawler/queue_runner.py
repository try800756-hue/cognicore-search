import os
import sys
import time
import urllib.parse
from bs4 import BeautifulSoup
import urllib.request

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from crawler.spider import crawl_url
from indexer.db import get_connection

SEEDS_FILE = os.path.join(os.path.dirname(__file__), '../data/seeds.txt')
QUEUE_FILE = os.path.join(os.path.dirname(__file__), '../data/queue.txt')

def get_visited_urls():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT url FROM pages")
    visited = {row['url'] for row in cursor.fetchall()}
    conn.close()
    return visited

def extract_links(url, max_links=15):
    links = []
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'CognicoreBot/1.0 (+https://cognicore.local)'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            if 'text/html' not in response.headers.get('Content-Type', ''):
                return []
            html = response.read().decode('utf-8', errors='ignore')
            
        soup = BeautifulSoup(html, 'html.parser')
        for a in soup.find_all('a', href=True):
            full_url = urllib.parse.urljoin(url, a['href'])
            parsed = urllib.parse.urlparse(full_url)
            if parsed.scheme in ['http', 'https']:
                clean_link = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, parsed.query, ''))
                links.append(clean_link)
                if len(links) >= max_links:
                    break
    except Exception:
        pass
    return links

def seed_queue_from_indexed_pages(visited):
    """If queue is empty, grab URLs from SQLite and extract outbound links."""
    print("[HARVESTER] Re-scanning indexed pages for new outbound links...")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT url FROM pages ORDER BY RANDOM() LIMIT 10")
    sample_urls = [row['url'] for row in cursor.fetchall()]
    conn.close()

    discovered = []
    for url in sample_urls:
        links = extract_links(url, max_links=10)
        for link in links:
            if link not in visited and link not in discovered:
                discovered.append(link)
    
    return discovered

def load_queue(visited):
    queue = []

    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, 'r') as f:
            queue = [line.strip() for line in f if line.strip() and line.strip() not in visited]

    if not queue and os.path.exists(SEEDS_FILE):
        with open(SEEDS_FILE, 'r') as f:
            queue = [line.strip() for line in f if line.strip() and line.strip() not in visited]

    # If seeds are exhausted, harvest links from DB pages
    if not queue:
        queue = seed_queue_from_indexed_pages(visited)

    seen = set()
    deduped = []
    for url in queue:
        if url not in seen:
            seen.add(url)
            deduped.append(url)

    return deduped

def save_queue(queue):
    with open(QUEUE_FILE, 'w') as f:
        for url in queue:
            f.write(f"{url}\n")

def run_queue(max_pages=50):
    visited = get_visited_urls()
    queue = load_queue(visited)

    print(f"=== Starting Cognicore Queue Runner ===")
    print(f"Queue Size: {len(queue)} | Currently Indexed: {len(visited)}")

    if not queue:
        print("No new URLs found to crawl.")
        return 0

    indexed_count = 0
    while queue and (len(visited) + indexed_count) < max_pages:
        target_url = queue.pop(0)
        
        if target_url in visited:
            continue
            
        success = crawl_url(target_url)
        visited.add(target_url)
        
        if success:
            indexed_count += 1
            new_links = extract_links(target_url)
            for link in new_links:
                if link not in visited and link not in queue:
                    queue.append(link)
                    
        time.sleep(1)

    save_queue(queue)
    print(f"=== Queue Run Finished. Newly Indexed: {indexed_count} | Remaining in Queue: {len(queue)} ===")
    return indexed_count

if __name__ == "__main__":
    run_queue(max_pages=30)
