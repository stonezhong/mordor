from functools import wraps

def cached(cache_id):
    def do_cached(f):
        @wraps(f)
        def wrapper(self, *argc, **kwargs):
            if cache_id not in self._cache:
                self._cache[cache_id] = f(self, *argc, **kwargs)
            return self._cache[cache_id]
        return wrapper
    return do_cached
