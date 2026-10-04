import os
import sys
import zipfile
import urllib.request

# Ensure project root is in sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from indexer.db import get_connection

TRANCO_URL = "https://tranco-list.eu/top-1m.csv.zip"
ZIP_PATH = "data/tranco-top-1m.csv.zip"
CSV_PATH = "data/top-1m.csv"

def seed_database(limit=10000):
    print("[1/3] Downloading Tranco Top 1M domain list...")
    os.makedirs("data", exist_ok=True)
    urllib.request.urlretrieve(TRANCO_URL, ZIP_PATH)

    print("[2/3] Extracting dataset...")
    with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
        zip_ref.extractall("data")

    print(f"[3/3] Seeding top {limit} international domains into pages table...")
    conn = get_connection()
    cursor = conn.cursor()

    added = 0
    with open(CSV_PATH, 'r') as f:
        for line in f:
            if added >= limit:
                break
            parts = line.strip().split(',')
            if len(parts) == 2:
                rank, domain = parts
                url = f"https://{domain}"
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO pages (url, domain, title, content, ad_score, pagerank)
                        VALUES (?, ?, ?, ?, 0.0, 1.0)
                    ''', (url, domain, domain, ''))
                    added += 1
                except Exception as e:
                    pass

    conn.commit()
    conn.close()
    print(f"[SUCCESS] Seeded {added} international seed domains into data/cognicore.db")

if __name__ == '__main__':
    seed_database(limit=10000)
