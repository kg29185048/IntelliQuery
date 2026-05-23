import time
import threading
from functools import wraps

def ttl_cache(ttl_seconds: int = 300):
    """
    A simple in-memory TTL cache decorator.
    Stores results for `ttl_seconds`.
    Thread-safe implementation using threading.Lock.
    """
    def decorator(func):
        cache = {}
        lock = threading.Lock()
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create a string representation of args/kwargs as the cache key.
            # This works well for our DB objects (MongoClient and SQLAlchemy Engine)
            # because their string representations naturally include the connection details.
            key = str(args) + str(kwargs)
            
            with lock:
                if key in cache:
                    result, timestamp = cache[key]
                    if time.time() - timestamp < ttl_seconds:
                        return result
                    
                # Cache miss or expired — call the function
                result = func(*args, **kwargs)
                cache[key] = (result, time.time())
                return result
                
        return wrapper
    return decorator
