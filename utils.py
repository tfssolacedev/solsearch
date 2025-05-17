import os
import hashlib

SOURCE_DIR = "."
KNOWN_HASHES = {
    "app.py": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0",
    "LICENSE": "f9d7b8d4e2a1c5f90d4a7b1c3e6a5d8b7c0f2e1d0a9d5c4b8e7f3a2d1c0b9a8e"
}

def load_theme():
    return {"theme": "default", "version": "1.0"}

def calculate_file_hash(filepath):
    with open(filepath, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def verify_source_integrity():
    tampered_files = []
    for filename, expected_hash in KNOWN_HASHES.items():
        if not os.path.exists(filename):
            continue
        actual_hash = calculate_file_hash(filename)
        if actual_hash != expected_hash:
            tampered_files.append(filename)
    if tampered_files:
        raise PermissionError(f"Tampering detected in files: {', '.join(tampered_files)}.")

verify_source_integrity()
