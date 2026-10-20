"""Short-lived overview data; never used to authorize edits or decisions."""

from collections import OrderedDict
from pathlib import Path
from threading import Condition
from time import monotonic

TTL = 5
_LIMIT = 128
_entries = OrderedDict()
_running = set()
_condition = Condition()


def cached(root, subject, read):
    key = (str(Path(root).resolve()), subject)
    with _condition:
        while key in _running:
            _condition.wait()
        entry = _entries.get(key)
        if entry and monotonic() - entry[0] < TTL:
            _entries.move_to_end(key)
            return entry[1]
        marker = object()
        _entries[key] = (0, marker)
        _running.add(key)
    try:
        value = read()
        with _condition:
            # A write during the read must not repopulate an invalidated entry.
            if _entries.get(key) == (0, marker):
                _entries[key] = (monotonic(), value)
                while len(_entries) > _LIMIT:
                    _entries.popitem(last=False)
        return value
    finally:
        with _condition:
            if _entries.get(key) == (0, marker):
                del _entries[key]
            _running.remove(key)
            _condition.notify_all()


def invalidate(root):
    workspace = str(Path(root).resolve())
    with _condition:
        for key in list(_entries):
            if key[0] == workspace:
                del _entries[key]
