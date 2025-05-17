import os
import hashlib

LICENSE_PATH = "LICENSE"
EXPECTED_HASH = "f9d7b8d4e2a1c5f90d4a7b1c3e6a5d8b7c0f2e1d0a9d5c4b8e7f3a2d1c0b9a8e"

def load_config():
    return {
        "UPLOAD_FOLDER": "uploads/websites",
        "MAX_CONTENT_LENGTH": 100 * 1024 * 1024,
        "MEILISEARCH_URL": "http://localhost:7700",
        "DISCORD_WEBHOOK": None
    }

def verify_license_integrity():
    if not os.path.exists(LICENSE_PATH):
        raise RuntimeError("Missing LICENSE file.")
    with open(LICENSE_PATH, 'rb') as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    if file_hash != EXPECTED_HASH:
        raise PermissionError("License file has been modified.")

verify_license_integrity()
