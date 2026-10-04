import re
from urllib.parse import urlparse

def is_utility_or_auth_url(url: str) -> bool:
    """Filter out login, signup, cart, and utility pages."""
    keywords = ['login', 'signup', 'signin', 'auth', 'cart', 'checkout', 'account', 'register', 'password']
    parsed = urlparse(url.lower())
    path = parsed.path
    return any(kw in path for kw in keywords)

def calculate_bloat_score(html: str) -> float:
    """Calculate a basic bloat score based on script/style density relative to content length."""
    if not html:
        return 0.0
    scripts = len(re.findall(r'<script.*?>.*?</script>', html, re.DOTALL | re.IGNORECASE))
    styles = len(re.findall(r'<style.*?>.*?</style>', html, re.DOTALL | re.IGNORECASE))
    total_len = len(html)
    if total_len == 0:
        return 0.0
    return min(1.0, (scripts * 200 + styles * 300) / total_len)

def clean_html_content(html: str) -> str:
    """Strip scripts, styles, HTML tags, and return cleaned text."""
    if not html:
        return ""
    # Strip script and style tags
    clean = re.sub(r'<script.*?>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r'<style.*?>.*?</style>', '', clean, flags=re.DOTALL | re.IGNORECASE)
    # Strip remaining HTML tags
    clean = re.sub(r'<[^>]+>', ' ', clean)
    # Collapse whitespace
    return ' '.join(clean.split())
