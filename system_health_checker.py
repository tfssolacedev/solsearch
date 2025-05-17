import os
import hashlib
import time
import threading
import sqlite3

BANNED_IPS_FILE = "banned_ips.txt"
DATABASE = "banned_ips.db"

def get_file_hash(filepath):
    if not os.path.exists(filepath):
        return ""
    with open(filepath, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

class SystemHealthChecker:
    def __init__(self):
        self.file_hashes = {}
        self.init_db()

    def init_db(self):
        self.conn = sqlite3.connect(DATABASE, check_same_thread=False)
        cur = self.conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS banned_ips(ip TEXT PRIMARY KEY)")
        self.conn.commit()

    def log_ip_to_db(self, ip):
        cur = self.conn.cursor()
        cur.execute("INSERT OR IGNORE INTO banned_ips(ip) VALUES(?)", (ip,))
        self.conn.commit()

    def sync_banned_ips(self):
        if os.path.exists(BANNED_IPS_FILE):
            with open(BANNED_IPS_FILE, 'r') as f:
                ips = set(line.strip() for line in f.readlines())
                cur = self.conn.cursor()
                cur.execute("SELECT ip FROM banned_ips")
                db_ips = set(row[0] for row in cur.fetchall())
                missing_in_db = ips - db_ips
                for ip in missing_in_db:
                    self.log_ip_to_db(ip)
                missing_in_file = db_ips - ips
                with open(BANNED_IPS_FILE, 'a') as f:
                    for ip in missing_in_file:
                        f.write(f"{ip}\n")

    def verify_integrity(self):
        files_to_check = ["app.py", "banned_ips.txt"]
        for filename in files_to_check:
            if not os.path.exists(filename):
                raise PermissionError(f"Critical file '{filename}' missing.")
            current_hash = get_file_hash(filename)
            if filename in self.file_hashes:
                if current_hash != self.file_hashes[filename]:
                    raise PermissionError(f"File '{filename}' has been modified.")
            self.file_hashes[filename] = current_hash

    def run(self):
        while True:
            time.sleep(30)
            try:
                self.verify_integrity()
                self.sync_banned_ips()
            except Exception as e:
                print(f"[ANTITAMPER] Security violation: {e}")

def start_system_health_checker():
    checker = SystemHealthChecker()
    thread = threading.Thread(target=checker.run, daemon=True)
    thread.start()
