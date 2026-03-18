"""
Utilities for the monitoring module.
"""
from typing import Any


def sanitize_for_json(obj: Any) -> Any:
    """
    Recursively ensure obj is JSON-serializable.

    Converts non-serializable types (exceptions, custom objects, etc.)
    to strings. Used for SSE streams and database storage.

    Args:
        obj: Value to sanitize (dict, list, or scalar)

    Returns:
        Sanitized value safe for json.dumps()
    """
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize_for_json(v) for v in obj]
    return str(obj)
