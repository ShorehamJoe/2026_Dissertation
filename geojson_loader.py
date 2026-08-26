"""geojson_loader.py - Downloads and caches LAD boundary GeoJSON."""
import json, logging
from uk_housing_dashboard.utils.cache import _load

log = logging.getLogger(__name__)

_SOURCES = [
    ("lad_ons.geojson",
     "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
     "Local_Authority_Districts_May_2023_UK_BGC/FeatureServer/0/query"
     "?where=1%3D1&outFields=LAD23NM,RGN23NM&outSR=4326&f=geojson&geometryPrecision=4",
     "ONS LAD boundaries"),
    ("lad_fallback.json",
     "https://raw.githubusercontent.com/martinjc/UK-GeoJSON/master/json/administrative/eng/lad.json",
     "LAD fallback"),
]


def load_geojson():
    log.info("[geo] Loading LAD boundaries...")
    for filename, url, desc in _SOURCES:
        try:
            raw  = _load(filename, url, desc)
            data = json.loads(raw)
            slim = [
                {"type":"Feature",
                 "properties":{
                     "name":   next((f["properties"].get(k,"") for k in ("LAD23NM","lad23nm","name") if f["properties"].get(k)),""),
                     "region": next((f["properties"].get(k,"") for k in ("RGN23NM","rgn23nm","region") if f["properties"].get(k)),""),
                 },
                 "geometry":f["geometry"]}
                for f in data.get("features",[])
            ]
            log.info("[geo] %d features loaded", len(slim))
            return json.dumps({"type":"FeatureCollection","features":slim})
        except Exception as e:
            log.warning("[geo] Failed (%s), trying next...", e)
    log.warning("[geo] All sources failed - city-only mode")
    return "null"
