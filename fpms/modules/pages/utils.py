import time
from functools import wraps


def ttl_cache(seconds):
    """
    Memoize a method's return value for `seconds`.

    For expensive calls (shell-outs) whose result changes slowly. `self` is
    excluded from the cache key so the cache is shared across instances of
    classes that are re-created frequently (e.g. HomePage).
    """

    def decorator(func):
        cache: dict = {}

        @wraps(func)
        def wrapper(*args, **kwargs):
            key = (args[1:], tuple(sorted(kwargs.items())))
            now = time.monotonic()
            cached = cache.get(key)
            if cached is not None and now - cached[0] < seconds:
                return cached[1]
            value = func(*args, **kwargs)
            cache[key] = (now, value)
            return value

        return wrapper

    return decorator


class StringFormatter:
    def __init__(self):
        pass

    def justify(self, text, width=21):
        """
        Inserts spaces between ':' and the remaining of the text to make
        sure 'text' is 'width' characters in length.
        """

        if len(text) < width:
            index = text.find(":") + 1
            if index > 0:
                return text[:index] + (" " * (width - len(text))) + text[index:]

        return text

    def split(self, lines, length=21):
        """
        Split lines that are longer than the given length
        """
        new_lines = []
        for line in lines:
            new_lines.extend(
                [line[i : i + length] for i in range(0, len(line), length)]
            )
        return new_lines
