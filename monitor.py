import inspect
import hashlib

FUNCTIONS_TO_CHECK = ["rotate_secret_key", "validate_session_integrity"]

def hash_function_source(func):
    source = inspect.getsource(func)
    return hashlib.sha256(source.encode()).hexdigest()

def check_runtime_integrity():
    from app import rotate_secret_key, validate_session_integrity
    known_hashes = {
        "rotate_secret_key": "d1c4f6e8a3b7d5c0e2a1f9d4c8b3e7a6f1e5d4c0b9a8f7e6d2c1a0",
        "validate_session_integrity": "e2a3d5f1c8b4e6d7a9f0e1c2d3b8a7f6e5d4c0b9a8f7e6d2c1a0"
    }
    for func_name in FUNCTIONS_TO_CHECK:
        func = eval(func_name)
        current_hash = hash_function_source(func)
        if current_hash != known_hashes.get(func_name):
            raise PermissionError(f"Function '{func_name}' has been altered.")

class PerformanceMonitor:
    def __init__(self):
        self.start_time = time.time()

    def log_performance(self):
        elapsed = time.time() - self.start_time
        print(f"[PERF] Uptime: {elapsed:.2f} seconds")

def start_background_monitor():
    def run():
        while True:
            time.sleep(10)
            try:
                check_runtime_integrity()
            except Exception as e:
                print(f"[MONITOR] Tamper detected: {e}")
    threading.Thread(target=run, daemon=True).start()
