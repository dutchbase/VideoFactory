"""SHA-256 of a file, cached until its stat signature changes."""

from __future__ import annotations

import hashlib
import threading
from collections import OrderedDict
from pathlib import Path

# Bootstrap plus one character detail touch ~8k files; entries are ~200 bytes.
_LIMIT = 65536
_CACHE: OrderedDict[tuple[str, int, int, int, int, int], str] = OrderedDict()
_LOCK = threading.Lock()


def file_sha256(path: str | Path) -> str:
    path = Path(path)
    stat = path.stat()
    key = (str(path), stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
    with _LOCK:
        if key in _CACHE:
            _CACHE.move_to_end(key)
            return _CACHE[key]
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    value = digest.hexdigest()
    with _LOCK:
        _CACHE[key] = value
        while len(_CACHE) > _LIMIT:
            _CACHE.popitem(last=False)
    return value
