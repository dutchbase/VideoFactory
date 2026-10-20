"""A process lease shared by every production entry point.

Pass ``lease_fds()`` to child processes. A child then holds the lease even if
its controller dies. Recovery never removes or replaces the lock inode.
"""
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import threading
import time


class ProductionBusy(ValueError):
    pass


_guard = threading.Lock()
_leases = {}


def lease_fds():
    return tuple(value['fd'] for value in _leases.values()
                 if value['thread'] == threading.get_ident())


def child_environment(root):
    lease = _leases.get(str(Path(root).resolve()))
    if lease is None or lease['thread'] != threading.get_ident(): return {}
    return {'VF_PRODUCTION_ROOT': str(Path(root).resolve()), 'VF_PRODUCTION_FD': str(lease['fd'])}


@contextmanager
def production_lock(root, owner=None):
    key = str(Path(root).resolve())
    thread = threading.get_ident()
    with _guard:
        existing = _leases.get(key)
        if existing:
            if existing['thread'] != thread:
                raise ProductionBusy('Another production worker is active.')
            existing['depth'] += 1
            lease = existing
        else:
            path = Path(key) / '.studio' / 'production.lock'
            path.parent.mkdir(parents=True, exist_ok=True)
            fd = None
            if os.environ.get('VF_PRODUCTION_ROOT') == key:
                try:
                    inherited = int(os.environ.get('VF_PRODUCTION_FD', ''))
                    stat = os.fstat(inherited)
                    actual = path.stat()
                    if (stat.st_dev, stat.st_ino) == (actual.st_dev, actual.st_ino):
                        fd = os.dup(inherited)
                except (ValueError, OSError): pass
            if fd is None: fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                os.close(fd)
                raise ProductionBusy('Another production worker or its child is active.') from None
            lease = dict(fd=fd, thread=thread, depth=1, pid=os.getpid(),
                         owner=owner or 'production', started_at=time.time())
            os.ftruncate(fd, 0)
            os.write(fd, json.dumps({k:v for k,v in lease.items() if k not in ('fd','thread','depth')}).encode())
            os.fsync(fd)
            _leases[key] = lease
    try:
        yield {k:v for k,v in lease.items() if k not in ('fd','thread','depth')}
    finally:
        with _guard:
            lease['depth'] -= 1
            if not lease['depth']:
                # Closing, rather than LOCK_UN, keeps inherited child leases alive.
                os.close(lease['fd'])
                del _leases[key]
