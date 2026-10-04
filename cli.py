import sys
import os
import shutil
from datetime import datetime

from indexer.db import get_connection, DB_PATH

def show_stats():
    conn = get_connection()
    cursor = conn.cursor()
    
    total_pages = cursor.execute("SELECT COUNT(*) FROM pages").fetchone()[0]
    avg_score = cursor.execute("SELECT AVG(ad_score) FROM pages").fetchone()[0] or 0.0
    domains = cursor.execute("SELECT domain, COUNT(*) as c FROM pages GROUP BY domain ORDER BY c DESC LIMIT 10").fetchall()
    
    print("\n=== COGNICORE INDEX STATS ===")
    print(f"Total Pages Indexed : {total_pages}")
    print(f"Average Ad/Bloat Score : {avg_score:.4f}")
    print("\nTop Domains in Index:")
    for d in domains:
        print(f" - {d['domain']}: {d['c']} page(s)")
    print("=============================\n")
    conn.close()

def backup_db():
    if not os.path.exists("backups"):
        os.makedirs("backups")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = f"backups/cognicore_{timestamp}.db"
    shutil.copy2(DB_PATH, dest)
    print(f"[BACKUP SUCCESS] Saved to {dest}")

def purge_domain(domain):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM pages WHERE domain LIKE ?", (f"%{domain}%",))
    conn.commit()
    print(f"[PURGED] Deleted {cursor.rowcount} row(s) matching domain: {domain}")
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python cli.py stats")
        print("  python cli.py backup")
        print("  python cli.py purge <domain>")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == "stats":
        show_stats()
    elif cmd == "backup":
        backup_db()
    elif cmd == "purge" and len(sys.argv) > 2:
        purge_domain(sys.argv[2])
    else:
        print("Unknown command.")
