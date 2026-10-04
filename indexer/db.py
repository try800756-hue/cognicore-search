import os
import sqlite3

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'cognicore.db')

def get_connection():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE,
        title TEXT,
        content TEXT,
        domain TEXT,
        image_url TEXT DEFAULT '',
        is_video INTEGER DEFAULT 0,
        ad_score REAL DEFAULT 0.0,
        pagerank REAL DEFAULT 1.0
    )
    ''')
    
    cursor.execute('''
    CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(
        title,
        content
    )
    ''')
    
    conn.commit()
    conn.close()

def save_page(url, title, content, domain, image_url='', is_video=0, ad_score=0.0, pagerank=1.0):
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Ensure new columns exist if database was previously initialized without them
        try:
            cursor.execute("ALTER TABLE pages ADD COLUMN image_url TEXT DEFAULT ''")
            cursor.execute("ALTER TABLE pages ADD COLUMN is_video INTEGER DEFAULT 0")
        except Exception:
            pass

        cursor.execute('''
            INSERT INTO pages (url, title, content, domain, image_url, is_video, ad_score, pagerank)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                title=excluded.title,
                content=excluded.content,
                domain=excluded.domain,
                image_url=excluded.image_url,
                is_video=excluded.is_video,
                ad_score=excluded.ad_score;
        ''', (url, title, content, domain, image_url, is_video, ad_score, pagerank))
        
        cursor.execute('SELECT id FROM pages WHERE url = ?', (url,))
        row = cursor.fetchone()
        if row:
            page_id = row['id']
            cursor.execute('DELETE FROM search_index WHERE rowid = ?', (page_id,))
            cursor.execute('INSERT INTO search_index (rowid, title, content) VALUES (?, ?, ?)', (page_id, title, content))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    init_db()
