import os
import sys
import time
import json
import requests
from flask import Flask, request, render_template_string, Response, send_from_directory

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

app = Flask(__name__, static_folder='static')

CACHE = {}
CACHE_TTL = 300

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ query if query else 'Cognicore Search • The Ugandan Web Engine' }}</title>
    
    <!-- PWA & OpenSearch Meta -->
    <link rel="manifest" href="/manifest.json">
    <link rel="search" type="application/opensearchdescription+xml" title="Cognicore Search" href="/opensearch.xml">
    <meta name="theme-color" content="#0f1013">
    <meta name="description" content="Independent, high-speed Ugandan web search platform built for privacy and performance.">

    <style>
        :root {
            --bg: #0f1013;
            --header-bg: #16181d;
            --card-bg: #1a1c23;
            --card-hover: #22252e;
            --border: #2a2e38;
            --text-main: #f3f4f6;
            --text-sub: #9ca3af;
            --text-muted: #6b7280;
            
            --ug-yellow: #facc15;
            --ug-red: #ef4444;
            --link: #60a5fa;
            --link-hover: #93c5fd;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            position: relative;
        }

        /* Watermark Signature */
        body::before {
            content: "COGNICORE • BUILT IN UGANDA";
            position: fixed;
            bottom: 30px;
            right: -20px;
            font-size: 80px;
            font-weight: 900;
            color: rgba(255, 255, 255, 0.012);
            letter-spacing: 4px;
            pointer-events: none;
            white-space: nowrap;
            transform: rotate(-5deg);
            z-index: 0;
        }

        /* Home Layout Grid */
        .home-wrapper {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            flex-grow: 1;
            padding: 40px 20px;
            z-index: 1;
            width: 100%;
            max-width: 1280px;
            margin: 0 auto;
        }

        .home-grid {
            display: grid;
            grid-template-columns: 280px 1fr 280px;
            gap: 24px;
            width: 100%;
            align-items: center;
        }

        @media (max-width: 960px) {
            .home-grid {
                grid-template-columns: 1fr;
            }
            .home-side-card { display: none; }
        }

        .home-center {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
        }

        .brand-heading {
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 12px;
        }
        .home-logo-img {
            width: 64px;
            height: 64px;
            object-fit: contain;
        }
        .home-logo {
            font-size: 52px;
            font-weight: 900;
            letter-spacing: -1.5px;
            background: linear-gradient(90deg, var(--ug-yellow) 0%, var(--ug-red) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .home-tagline {
            color: var(--text-sub);
            font-size: 14px;
            margin-bottom: 28px;
        }
        .home-search-box {
            width: 100%;
            max-width: 600px;
            display: flex;
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 28px;
            padding: 8px 18px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            transition: all 0.2s ease;
        }
        .home-search-box:focus-within {
            border-color: var(--ug-yellow);
            box-shadow: 0 0 20px rgba(250, 204, 21, 0.2);
        }

        /* Home Sidebar Cards */
        .home-side-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 20px;
            text-align: left;
        }
        .card-title {
            font-size: 15px;
            font-weight: 700;
            color: var(--ug-yellow);
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .card-desc {
            font-size: 13px;
            color: var(--text-sub);
            line-height: 1.5;
            margin-bottom: 14px;
        }
        .action-btn {
            display: inline-block;
            background: rgba(250, 204, 21, 0.15);
            color: var(--ug-yellow);
            border: 1px solid rgba(250, 204, 21, 0.3);
            padding: 8px 14px;
            border-radius: 8px;
            text-decoration: none;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .action-btn:hover {
            background: var(--ug-yellow);
            color: #000;
        }

        /* Header Bar */
        .sticky-header {
            position: sticky;
            top: 0;
            z-index: 100;
            background: var(--header-bg);
            border-bottom: 1px solid var(--border);
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }
        .header-top {
            display: flex;
            align-items: center;
            gap: 20px;
            padding: 14px 40px;
        }
        .logo-link {
            display: flex;
            align-items: center;
            gap: 12px;
            text-decoration: none;
        }
        .header-logo-img {
            width: 32px;
            height: 32px;
            object-fit: contain;
        }
        .logo-text {
            font-size: 20px;
            font-weight: 900;
            color: var(--ug-yellow);
            letter-spacing: -0.5px;
        }
        .search-box {
            display: flex;
            flex-grow: 1;
            max-width: 650px;
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 24px;
            padding: 8px 18px;
            align-items: center;
        }
        .search-box:focus-within { border-color: var(--ug-yellow); }
        .search-input {
            width: 100%;
            background: transparent;
            border: none;
            color: #fff;
            font-size: 15px;
            outline: none;
        }
        .search-btn {
            background: none;
            border: none;
            color: var(--ug-yellow);
            cursor: pointer;
            font-weight: 600;
            font-size: 14px;
        }

        /* Tabs Navigation */
        .tabs {
            display: flex;
            gap: 32px;
            padding: 0 40px;
            margin-left: 150px;
        }
        .tab-item {
            color: var(--text-sub);
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
            padding: 12px 0;
            border-bottom: 2px solid transparent;
            transition: all 0.2s;
        }
        .tab-item:hover { color: var(--text-main); }
        .tab-item.active {
            color: var(--ug-yellow);
            border-bottom-color: var(--ug-yellow);
        }

        /* Results Layout Grid */
        .results-wrapper {
            display: flex;
            gap: 32px;
            padding: 24px 40px;
            margin-left: 150px;
            max-width: 1280px;
            z-index: 1;
        }
        .main-content {
            flex: 1;
            max-width: 680px;
        }
        .main-content.images-view {
            max-width: 100%;
            margin-left: 0;
        }

        .sidebar-widget {
            width: 300px;
            flex-shrink: 0;
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 20px;
            height: fit-content;
            align-self: flex-start;
        }

        .stats {
            font-size: 13px;
            color: var(--text-muted);
            margin-bottom: 24px;
        }

        /* Result Cards */
        .result-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 16px;
            transition: background 0.15s ease, border-color 0.15s ease;
        }
        .result-card:hover {
            border-color: #3f4452;
            background: var(--card-hover);
        }
        .result-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 6px;
        }
        .favicon {
            width: 16px;
            height: 16px;
            border-radius: 4px;
        }
        .result-domain {
            color: var(--text-sub);
            font-size: 13px;
            font-weight: 500;
        }
        .result-title {
            font-size: 18px;
            font-weight: 600;
            color: var(--link);
            text-decoration: none;
            display: inline-block;
            margin-bottom: 6px;
            line-height: 1.35;
        }
        .result-title:hover { text-decoration: underline; color: var(--link-hover); }
        .result-snippet {
            font-size: 14px;
            line-height: 1.6;
            color: var(--text-sub);
        }

        /* Footer */
        .uganda-badge {
            margin-top: auto;
            padding: 16px 40px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-top: 1px solid var(--border);
            background: var(--header-bg);
            font-size: 13px;
            color: var(--text-sub);
            z-index: 10;
        }
        .flag-strip {
            display: inline-flex;
            gap: 3px;
            align-items: center;
            margin-left: 6px;
        }
        .stripe {
            width: 12px;
            height: 8px;
            border-radius: 1px;
        }
        .stripe.black { background: #000; border: 1px solid #333; }
        .stripe.yellow { background: var(--ug-yellow); }
        .stripe.red { background: var(--ug-red); }
    </style>
</head>
<body>

    {% if query %}
    <div class="sticky-header">
        <div class="header-top">
            <a href="/" class="logo-link">
                <img src="/static/logo.png" class="header-logo-img" alt="Logo" onerror="this.style.display='none'">
                <span class="logo-text">COGNICORE</span>
            </a>
            <form action="/search" method="get" class="search-box">
                <input type="text" name="q" class="search-input" value="{{ query }}" placeholder="Search global web..." required>
                <input type="hidden" name="type" value="{{ search_type }}">
                <button type="submit" class="search-btn">Search</button>
            </form>
        </div>

        <div class="tabs">
            <a href="/search?q={{ query }}&type=all" class="tab-item {{ 'active' if search_type == 'all' else '' }}">All</a>
            <a href="/search?q={{ query }}&type=images" class="tab-item {{ 'active' if search_type == 'images' else '' }}">Images</a>
            <a href="/search?q={{ query }}&type=videos" class="tab-item {{ 'active' if search_type == 'videos' else '' }}">Videos</a>
            <a href="/search?q={{ query }}&type=blogs" class="tab-item {{ 'active' if search_type == 'blogs' else '' }}">Blogs & News</a>
        </div>
    </div>

    <div class="results-wrapper">
        <div class="main-content">
            <div class="stats">Showing {{ search_type }} results for "{{ query }}" — Page {{ page }}</div>

            {% for r in results %}
                <div class="result-card">
                    <div class="result-header">
                        <img class="favicon" src="https://www.google.com/s2/favicons?domain={{ r.domain }}&sz=32" alt="" onerror="this.style.display='none'">
                        <span class="result-domain">{{ r.domain }}</span>
                    </div>
                    <a href="{{ r.url }}" target="_blank" class="result-title">{{ r.title }}</a>
                    <div class="result-snippet">{{ r.snippet | safe }}</div>
                </div>
            {% else %}
                <div style="margin-top: 40px; color: var(--text-main);">
                    <h3>No results found for "{{ query }}".</h3>
                </div>
            {% endfor %}
        </div>

        <div class="sidebar-widget">
            <div class="card-title">Cognicore Engine</div>
            <div class="card-desc">Designed & Engineered in Uganda 🇺🇬. Focused on high-speed, unbiased search without user tracking.</div>
            <button onclick="installPWA()" class="action-btn" style="width:100%; text-align:center;">📲 Install Web App</button>
        </div>
    </div>

    {% else %}
    <!-- Home Screen with Left and Right Sections -->
    <div class="home-wrapper">
        <div class="home-grid">
            
            <!-- Left Info Card -->
            <div class="home-side-card">
                <div class="card-title">🚀 About Cognicore</div>
                <div class="card-desc">
                    An independent, privacy-focused search technology built locally in Uganda to deliver fast, unfiltered access to the global web.
                </div>
                <button onclick="addSearchEngine()" class="action-btn">🔍 Set as Default Search</button>
            </div>

            <!-- Center Brand Section -->
            <div class="home-center">
                <div class="brand-heading">
                    <img src="/static/logo.png" class="home-logo-img" alt="Cognicore Logo" onerror="this.style.display='none'">
                    <div class="home-logo">COGNICORE</div>
                </div>
                <div class="home-tagline">Fast • Secure • Independent Web Engine</div>
                <form action="/search" method="get" class="home-search-box">
                    <input type="text" name="q" class="search-input" style="font-size: 16px;" placeholder="Search global web..." required autofocus>
                    <input type="hidden" name="type" value="all">
                    <button type="submit" class="search-btn">Search</button>
                </form>
            </div>

            <!-- Right Support / Install Card -->
            <div class="home-side-card">
                <div class="card-title">🇺🇬 Support Our Hardware Fund</div>
                <div class="card-desc">
                    We are young Ugandan developers building independent cloud infrastructure. Support server upgrades & hardware growth:
                </div>
                <div style="font-size: 12px; color: var(--ug-yellow); font-weight: bold; margin-bottom: 8px;">
                    MoMo/Airtel: +256 700 000 000
                </div>
                <button onclick="installPWA()" class="action-btn" style="width: 100%; text-align: center;">📲 Install Mobile & PC App</button>
            </div>

        </div>
    </div>
    {% endif %}

    <div class="uganda-badge">
        <span>© Cognicore Search • Built in Uganda 🇺🇬</span>
        <span class="flag-strip">
            <span class="stripe black"></span>
            <span class="stripe yellow"></span>
            <span class="stripe red"></span>
        </span>
    </div>

    <script>
        let deferredPrompt;
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
        });

        function installPWA() {
            if (deferredPrompt) {
                deferredPrompt.prompt();
                deferredPrompt.userChoice.then((choiceResult) => {
                    if (choiceResult.outcome === 'accepted') {
                        console.log('User accepted the install prompt');
                    }
                    deferredPrompt = null;
                });
            } else {
                alert("To install: Open browser menu (⋮) and tap 'Add to Home screen' or 'Install App'.");
            }
        }

        function addSearchEngine() {
            if (window.external && ('AddSearchProvider' in window.external)) {
                window.external.AddSearchProvider('/opensearch.xml');
            } else {
                alert("To add Cognicore to Chrome/Brave: Open Settings -> Search Engine -> Manage Search Engines -> Add Cognicore.");
            }
        }
    </script>

</body>
</html>
"""

SEARXNG_URL = "http://127.0.0.1:8080/search"

def fetch_searxng(query, category="general", page=1):
    cache_key = f"{query}:{category}:{page}"
    now = time.time()

    if cache_key in CACHE:
        cached_time, cached_results = CACHE[cache_key]
        if now - cached_time < CACHE_TTL:
            return cached_results

    results = []
    params = {'q': query, 'format': 'json', 'categories': category, 'pageno': page}
    
    try:
        resp = requests.get(SEARXNG_URL, params=params, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            for r in data.get('results', []):
                domain = r.get('parsed_url', ['', ''])[1].replace('www.', '') if r.get('parsed_url') else 'web'
                results.append({
                    'url': r.get('url', '#'),
                    'title': r.get('title', ''),
                    'domain': domain,
                    'snippet': r.get('content', '')
                })
    except Exception as e:
        print(f"[FETCH ERROR]: {e}")

    CACHE[cache_key] = (now, results)
    return results

@app.route('/manifest.json')
def manifest():
    data = {
        "short_name": "Cognicore",
        "name": "Cognicore Web Search",
        "icons": [
            {"src": "/static/logo.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/static/logo.png", "sizes": "512x512", "type": "image/png"}
        ],
        "start_url": "/",
        "background_color": "#0f1013",
        "theme_color": "#0f1013",
        "display": "standalone"
    }
    return Response(json.dumps(data), mimetype='application/json')

@app.route('/opensearch.xml')
def opensearch():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
    <ShortName>Cognicore</ShortName>
    <Description>Search the global web using Cognicore</Description>
    <InputEncoding>UTF-8</InputEncoding>
    <Url type="text/html" template="https://cognicoretech.com/search?q={searchTerms}"/>
</OpenSearchDescription>"""
    return Response(xml, mimetype='application/opensearchdescription+xml')

@app.route('/')
@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all').lower()
    
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1

    category_map = {'all': 'general', 'images': 'images', 'videos': 'videos', 'blogs': 'news'}
    category = category_map.get(search_type, 'general')

    results = []
    if query:
        results = fetch_searxng(query, category, page)

    return render_template_string(HTML_TEMPLATE, query=query, search_type=search_type, results=results, page=page)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
