"""
postcode.py
===========
Postcode-to-LAD/region lookup using the postcodes.io public API.
Free, no API key required, Open Government Licence data.
"""
import json
import logging
import urllib.request

from uk_housing_dashboard.config import POSTCODES_IO_URL

log = logging.getLogger(__name__)


def lookup(postcode: str) -> dict | None:
    """
    Look up a UK postcode and return location metadata.

    Returns dict with keys: postcode, lat, lng, region, district, lad_name
    or None if the postcode is invalid or the API is unavailable.

    >>> result = lookup("SW1A 1AA")
    >>> result is not None
    True
    """
    clean = postcode.strip().upper().replace(" ", "")
    url   = POSTCODES_IO_URL.format(postcode=clean)
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            data = json.loads(r.read())
        if data.get("status") != 200:
            return None
        res = data["result"]
        # Map ONS region names to our 12-region set
        from uk_housing_dashboard.data.land_registry import POSTCODE_TO_REGION
        prefix = clean[:2]
        region = POSTCODE_TO_REGION.get(prefix) or POSTCODE_TO_REGION.get(prefix[:1], "")
        return {
            "postcode": res.get("postcode"),
            "lat":      res.get("latitude"),
            "lng":      res.get("longitude"),
            "region":   region,
            "district": res.get("admin_district", ""),
            "lad_name": res.get("admin_district", ""),
        }
    except Exception as exc:
        log.debug("Postcode lookup failed for %s: %s", postcode, exc)
        return None
