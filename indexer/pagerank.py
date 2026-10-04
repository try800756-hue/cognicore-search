import os
import sys
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from indexer.db import get_connection, init_db

def ensure_pagerank_column():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(pages)")
    columns = [col['name'] for col in cursor.fetchall()]
    if 'pagerank' not in columns:
        cursor.execute("ALTER TABLE pages ADD COLUMN pagerank REAL DEFAULT 1.0")
        conn.commit()
    conn.close()

def calculate_pagerank(iterations=20, d=0.85):
    ensure_pagerank_column()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, url FROM pages")
    pages = cursor.fetchall()
    if not pages:
        conn.close()
        return

    page_map = {row['url']: row['id'] for row in pages}
    num_pages = len(pages)
    id_to_idx = {row['id']: i for i, row in enumerate(pages)}
    idx_to_id = {i: row['id'] for i, row in enumerate(pages)}

    # Initialize transition matrix
    M = np.zeros((num_pages, num_pages))

    # Calculate inbound links
    for row in pages:
        p_id = row['id']
        p_url = row['url']
        # Simplified internal link calculation using domain matching
        cursor.execute("SELECT COUNT(*) FROM pages WHERE content LIKE ?", (f"%{p_url}%",))
        link_count = cursor.fetchone()[0]
        if link_count > 0:
            for other_row in pages:
                if other_row['id'] != p_id:
                    M[id_to_idx[p_id], id_to_idx[other_row['id']]] = 1.0 / num_pages

    ranks = np.ones(num_pages) / num_pages
    for _ in range(iterations):
        ranks = (1 - d) / num_pages + d * M.dot(ranks)

    # Normalize and write back to database
    max_rank = np.max(ranks) if np.max(ranks) > 0 else 1.0
    for idx, rank in enumerate(ranks):
        page_id = idx_to_id[idx]
        norm_score = float(rank / max_rank)
        cursor.execute("UPDATE pages SET pagerank = ? WHERE id = ?", (norm_score, page_id))

    conn.commit()
    conn.close()
    print(f"[PAGERANK] Updated PageRank scores across {num_pages} indexed pages.")

if __name__ == "__main__":
    calculate_pagerank()
