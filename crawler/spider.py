import os
import sys
import urllib.request
import urllib.parse
import re
from bs4 import BeautifulSoup

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from indexer.db import get_connection

TRUSTED_DOMAINS = {
    'archlinux.org', 'kernel.org', 'pypi.org', 
    'docs.python.org', 'wikipedia.org', 'news.ycombinator.com', 'lobste.rs'
}

# Ignore administrative, auth, and search paths
BLOCKED_PATTERNS = [
    r'/login', r'/register', r'/signup', r'/auth', 
    r'/search', r'/account', r'/cart', r'/checkout'
]

def is_blocked_url(url):
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.lower()
    return any(re.search(pattern, path) for pattern in BLOCKED_PATTERNS)

def calculate_ad_score(soup, html, domain):
    total_len = max(len(html), 1)
    is_trusted = any(trusted in domain for trusted in TRUSTED_DOMAINS)
    
    scripts = len(soup.find_all('script'))
    iframes = len(soup.find_all('iframe'))
    ads_tags = len(soup.find_all(class_=re.compile(r'ad|banner|sponsor|popup|affiliate', re.I)))
    
    for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
        element.decompose()
        
    text = ' '.join(soup.stripped_strings)
    word_count = len(text.split())
    
    if word_count < 15 and not is_trusted:
        return 1.0, text, word_count
        
    penalty = (scripts * 120 + iframes * 250 + ads_tags * 350) / total_len
    
    if is_trusted:
        penalty *= 0.1
        
    return min(penalty, 1.0), text, word_count

def crawl_url(url):
    if is_blocked_url(url):
        print(f"[SKIPPED] Utility/Auth path: {url}")
        return False

    domain = urllib.parse.urlparse(url).netloc
    
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'CognicoreBot/1.0 (+https://cognicore.local)'}
        )
        with urllib.request.urlopen(req, timeout=6) as response:
            if 'text/html' not in response.headers.get('Content-Type', ''):
                return False
            html = response.read().decode('utf-8', errors='ignore')

        soup = BeautifulSoup(html, 'html.parser')
        title = soup.title.string.strip() if soup.title and soup.title.string else url
        
        ad_score, clean_text, word_count = calculate_ad_score(soup, html, domain)
        
        if ad_score > 0.35:
            print(f"[REJECTED] High bloat score ({ad_score:.2f}): {url}")
            return False

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT OR REPLACE INTO pages (url, domain, title, content, word_count, ad_score) 
               VALUES (?, ?, ?, ?, ?, ?)''',
            (url, domain, title, clean_text, word_count, ad_score)
        )
        conn.commit()
        conn.close()
        print(f"[INDEXED] Score: {ad_score:.2f} | Words: {word_count} | {url}")
        return True

    except Exception as e:
        print(f"[ERROR] Failed {url}: {e}")
        return False

if __name__ == "__main__":
    test_urls = [
        "https://news.ycombinator.com/",
        "https://pypi.org/account/login/"
    ]
    for target in test_urls:
        crawl_url(target)
