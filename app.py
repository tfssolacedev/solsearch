from flask import Flask, session, request, redirect, url_for, render_template, flash, send_from_directory
import os
import threading
import time
import secrets
import hashlib
import requests
import sqlite3
from dotenv import load_dotenv
import pymongo
import zipfile
import re

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# Initialize Flask app
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads/websites'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Set initial secret key
app.secret_key = secrets.token_hex(175)

# === IP BANNING SYSTEM ===
def load_banned_ips():
    if not os.path.exists("banned_ips.txt"):
        open("banned_ips.txt", 'w').close()
    with open("banned_ips.txt", 'r') as f:
        return set(line.strip() for line in f)

def ban_ip(ip):
    if ip not in load_banned_ips():
        with open("banned_ips.txt", 'a') as f:
            f.write(f"{ip}\n")
    conn = sqlite3.connect("banned_ips.db")
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO banned_ips(ip) VALUES(?)", (ip,))
    conn.commit()

@app.before_request
def check_banned_ip():
    client_ip = request.remote_addr
    if client_ip in load_banned_ips():
        return render_template("banned.html")
    query = request.args.get("q", "").lower()
    restricted_terms = ["child porn", "cp videos", "illegal content"]
    for term in restricted_terms:
        if term in query:
            ban_ip(client_ip)
            return render_template("banned.html")

# === SEARCH ENGINE ===
search_index = []

def build_search_index():
    global search_index
    search_index.clear()
    for root, _, files in os.walk(UPLOAD_FOLDER):
        for file in files:
            filepath = os.path.join(root, file)
            if file.endswith(('.txt', '.md', '.html', '.htm')):
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        words = re.findall(r'\w+', content.lower())
                        title = file
                        url = f"/file/{file}"
                        search_index.append({
                            "title": title,
                            "url": url,
                            "content": content[:200] + "...",
                            "words": set(words),
                            "filepath": filepath
                        })
                except Exception as e:
                    print(f"[INDEX] Error reading {file}: {e}")

build_search_index()  # Initial index build

def perform_search(query):
    words = set(re.findall(r'\w+', query.lower()))
    matched = []
    for item in search_index:
        score = len(words & item["words"])
        if score > 0:
            matched.append({
                "title": item["title"],
                "url": item["url"],
                "summary": item["content"]
            })
    return sorted(matched, key=lambda x: len(x["summary"]), reverse=True)[:10]

# === SEARCH ROUTE ===
@app.route('/search')
def search():
    client_ip = request.remote_addr
    raw_query = request.args.get("q", "").strip()

    # AI Search Mode
    if raw_query.startswith("searchai@"):
        try:
            num_searches = int(raw_query.split("@")[1])
            recent_queries = get_last_n_searches(client_ip, num_searches)
            combined_results = []
            for q in recent_queries:
                results = perform_search(q)
                combined_results.append({"query": q, "results": results})
            log_search(client_ip, raw_query)
            return render_template("search_results.html", results=combined_results, ai_mode=True)
        except:
            return "Invalid AI search format. Use: searchai@N", 400

    # Regular Search
    results = perform_search(raw_query)
    log_search(client_ip, raw_query)
    return render_template("search_results.html", results=[{"query": raw_query, "results": results}], ai_mode=False)

# === FILE VIEWER ===
@app.route('/file/<path:filename>')
def view_file(filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(filepath):
        return "File not found", 404

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    return f"<pre>{content}</pre>"

# === APPLY WEBSITE FORM ===
@app.route('/apply:website', methods=['GET', 'POST'])
def apply_website():
    if request.method == 'POST':
        file = request.files.get('zip_file')
        if not file or file.filename == '':
            return redirect(request.url)
        if file.filename.endswith('.zip'):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            flash('Application submitted successfully!')

            # Extract zip
            extract_path = os.path.join(UPLOAD_FOLDER, filename.replace(".zip", ""))
            os.makedirs(extract_path, exist_ok=True)
            try:
                with zipfile.ZipFile(file, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)
            except Exception as e:
                flash("Error extracting ZIP file.")
                return redirect(url_for('apply_website'))

            # Rebuild index
            build_search_index()

            # Forward to Discord
            try:
                payload = {"content": f"📦 New domain application received: `{filename}`"}
                requests.post(DISCORD_WEBHOOK_URL, json=payload)
            except:
                pass

            return redirect(url_for('apply_website'))
    return render_template('apply_website.html')

# === STATIC PAGES ===
@app.route('/solace:extensions')
def extensions():
    return render_template('extensions.html')

@app.route('/solace:tos')
def tos():
    return render_template('tos.html')

@app.route('/solace:privacy')
def privacy():
    return render_template('privacy.html')

# === SECRET KEY ROTATION ===
def rotate_secret_key():
    while True:
        time.sleep(60)
        app.secret_key = secrets.token_hex(175)

@app.before_request
def validate_session_integrity():
    if 'user' in session:
        session.clear()

# === SEARCH HISTORY DB ===
def init_search_db():
    conn = sqlite3.connect("search_history.db")
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS search_history(ip TEXT, query TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
    conn.commit()

def log_search(ip, query):
    conn = sqlite3.connect("search_history.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO search_history(ip, query) VALUES(?, ?)", (ip, query))
    conn.commit()

def get_last_n_searches(ip, n=5):
    conn = sqlite3.connect("search_history.db")
    cur = conn.cursor()
    cur.execute("SELECT query FROM search_history WHERE ip=? ORDER BY timestamp DESC LIMIT ?", (ip, n))
    return [row[0] for row in cur.fetchall()]

# === STARTUP ===
if __name__ == '__main__':
    init_search_db()

    # Start background tasks
    threading.Thread(target=rotate_secret_key, daemon=True).start()
    import system_health_checker
    system_health_checker.start_system_health_checker()

    # Connect to MongoDB
    client = pymongo.MongoClient(MONGO_URI)
    db = client.solace
    applications = db.applications

    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)
