import os
import sys
import asyncio
import aiohttp
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from indexer.db import get_connection, save_page
from indexer.cleaner import clean_html_content, is_utility_or_auth_url

HEADERS = {
    'User-Agent': 'CognicoreBot/2.0 (+https://cognicoretech.com/bot; search-engine-crawler)'
}

async def fetch_and_index(session, url):
    if is_utility_or_auth_url(url):
        return

    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=8), headers=HEADERS) as resp:
            if resp.status == 200 and 'text/html' in resp.headers.get('Content-Type', '').lower():
                html = await resp.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                title = soup.title.string.strip() if (soup.title and soup.title.string) else url
                content = clean_html_content(html)
                domain = urlparse(url).netloc.replace('www.', '')

                # Extract first prominent image URL
                image_url = ""
                img_tag = soup.find('img', src=True)
                if img_tag:
                    image_url = urljoin(url, img_tag['src'])

                # Detect video links/embeds
                is_video = 1 if ('youtube.com' in url or 'vimeo.com' in url or soup.find('video') or soup.find('iframe')) else 0

                if content:
                    save_page(url, title, content, domain, image_url=image_url, is_video=is_video)
                    print(f"[CRAWLED] {url} — {len(content)} chars (Media: {'Video' if is_video else 'Image' if image_url else 'None'})")
    except Exception:
        pass

async def crawl_batch(batch_size=25):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT url FROM pages WHERE content = '' OR content IS NULL LIMIT ?", (batch_size,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return 0

    urls = [row['url'] for row in rows]
    connector = aiohttp.TCPConnector(limit=25, ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch_and_index(session, url) for url in urls]
        await asyncio.gather(*tasks)

    return len(urls)

async def main_loop():
    print("[COGNICORE DAEMON] Active continuous media & text indexer running...")
    while True:
        processed = await crawl_batch(batch_size=25)
        if processed == 0:
            await asyncio.sleep(10)
        else:
            await asyncio.sleep(1)

if __name__ == '__main__':
    asyncio.run(main_loop())
