"""cache.py - Network fetch with TTL-based local cache."""
import os, time, logging
from uk_housing_dashboard.config import CACHE_DIR, CACHE_TTL_DAYS

log  = logging.getLogger(__name__)
_TTL = CACHE_TTL_DAYS * 86400
os.makedirs(CACHE_DIR, exist_ok=True)

try:
    import requests as _req; _HAS_REQ = True
except ImportError:
    import urllib.request as _url; _HAS_REQ = False


def _fetch(url, timeout=30):
    if _HAS_REQ:
        r = _req.get(url, timeout=timeout, headers={"User-Agent":"uk-housing-dashboard/4.0"})
        r.raise_for_status(); return r.content
    with _url.urlopen(_url.Request(url, headers={"User-Agent":"uk-housing-dashboard/4.0"}), timeout=timeout) as r:
        return r.read()


def _load(filename, url, desc=""):
    path = os.path.join(CACHE_DIR, filename)
    if os.path.exists(path):
        age = time.time() - os.path.getmtime(path)
        if age < _TTL:
            log.info("[cache] %s (%.0fd old)", desc or filename, age/86400)
            return open(path, "rb").read()
    log.info("[download] %s ...", desc or url)
    data = _fetch(url)
    open(path, "wb").write(data)
    return data
