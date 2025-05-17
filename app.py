import os
import zipfile
from flask import Flask, session, request, redirect, url_for, render_template, flash
import threading
import time
import secrets
import hashlib
import requests
import sqlite3
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# Initialize Flask
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads/websites'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Set initial secret key
app.secret_key = secrets.token_hex(175)

# In-memory search index
search_index = []

def build_search_index():
    global search_index
    search_index.clear()
    for root, _, files in os.walk(UPLOAD_FOLDER):
        for file in files:
            filepath = os.path.join(root, file)
            if file.endswith(('.txt', '.md', '.html', '.htm')):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
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

# Run indexing on startup and after uploads
build_search_index()
