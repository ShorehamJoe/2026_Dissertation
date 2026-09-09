
import json
import os
import time

from uk_housing_dashboard.utils.cache import _fetch
from uk_housing_dashboard.data.datasets import REGIONAL, HPI, HPI_TREND, HPI_YEARS

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".map_cache")
TTL_DAYS  = 30
TTL_SECS  = TTL_DAYS * 86400

# ONS region code mapping (E12 codes -> our region names)
ONS_REGION_CODES = {
    "E12000001": "North East",
    "E12000002": "North West",
    "E12000003": "Yorkshire and The Humber",
    "E12000004": "East Midlands",
    "E12000005": "West Midlands",
    "E12000006": "East of England",
    "E12000007": "London",
    "E12000008": "South East",
    "E12000009": "South West",
    "W92000004": "Wales",
    "S92000003": "Scotland",
    "N92000002": "Northern Ireland",
}

# HM Land Registry region names -> our names
LR_REGION_MAP = {
    "North East":               "North East",
    "North West":               "North West",
    "Yorkshire and The Humber": "Yorkshire and The Humber",
    "East Midlands":            "East Midlands",
    "West Midlands":            "West Midlands",
    "East of England":          "East of England",
    "London":                   "London",
    "South East":               "South East",
    "South West":               "South West",
    "Wales":                    "Wales",
    "Scotland":                 "Scotland",
    "Northern Ireland":         "Northern Ireland",
}


def _cache_path(name):
    return os.path.join(CACHE_DIR, name)


def _is_fresh(path):

    if not os.path.exists(path):
        return False
    return (time.time() - os.path.getmtime(path)) < TTL_SECS


def _load_json_cache(name):
    path = _cache_path(name)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return None


def _save_json_cache(name, data):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(_cache_path(name), "w", encoding="utf-8") as f:
        json.dump(data, f)


# ---------------------------------------------------------------------------
# INCOME DATA - ONS Regional GDHI
# ---------------------------------------------------------------------------

def fetch_regional_income():

    cache_name = "live_regional_income.json"
    if _is_fresh(_cache_path(cache_name)):
        cached = _load_json_cache(cache_name)
        if cached:
            print("  [live] Regional income: loaded from cache (< 30 days old)")
            return cached

    print("  [live] Fetching regional income from ONS API...")
    try:
        url = ("https://api.beta.ons.gov.uk/v1/datasets/regional-gdhi-by-component/"
               "editions/time-series/versions/1/observations"
               "?geography=E92000001,E12000001,E12000002,E12000003,E12000004,"
               "E12000005,E12000006,E12000007,E12000008,E12000009"
               "&aggregate=torva&time=*")
        raw  = _fetch(url, timeout=15)
        data = json.loads(raw)

        # Extract most recent year per region
        region_income = {}
        observations  = data.get("observations", [])
        by_region     = {}
        for obs in observations:
            code  = obs.get("geography", {}).get("id", "")
            name  = ONS_REGION_CODES.get(code)
            if not name:
                continue
            year  = int(obs.get("time", {}).get("id", "0"))
            value = obs.get("observation")
            if value and (name not in by_region or year > by_region[name][0]):
                by_region[name] = (year, float(value) * 1000)  # convert GBPk to GBP

        region_income = {k: round(v[1]) for k, v in by_region.items()}
        if len(region_income) >= 8:
            _save_json_cache(cache_name, region_income)
            print(f"  [live] Regional income: {len(region_income)} regions fetched")
            return region_income

    except Exception as e:
        print(f"  [live] Regional income API unavailable ({e}) - using embedded data")

    return None


# ---------------------------------------------------------------------------
# HOUSE PRICE DATA - HM Land Registry HPI API
# ---------------------------------------------------------------------------

def fetch_hpi_by_region():

    cache_name = "live_hpi_regional.json"
    if _is_fresh(_cache_path(cache_name)):
        cached = _load_json_cache(cache_name)
        if cached:
            print("  [live] HPI prices: loaded from cache (< 30 days old)")
            return cached

    print("  [live] Fetching HPI data from Land Registry API...")
    try:
        # HM Land Registry Linked Data API - average prices by region
        url = ("https://landregistry.data.gov.uk/data/ukhpi/region.json"
               "?_pageSize=200&_sort=-ukhpi%3ArefPeriodStart")
        raw  = _fetch(url, timeout=15)
        data = json.loads(raw)

        result_raw = data.get("result", {}).get("items", [])
        if not result_raw:
            raise ValueError("Empty response")

        # Group by region, take most recent entry per region per property type
        from collections import defaultdict
        by_region = defaultdict(dict)

        type_map = {
            "detachedAverage":      "Detached",
            "semiDetachedAverage":  "Semi-Detached",
            "terracedAverage":      "Terraced",
            "flatMaisonetteAverage":"Flat",
            "averagePrice":         "All",
            "firstTimeBuyerAveragePrice": "FTB",
        }

        for item in result_raw:
            region_uri = item.get("regionName", "")
            region_name = LR_REGION_MAP.get(region_uri, "")
            if not region_name:
                continue
            for api_key, our_key in type_map.items():
                val = item.get(f"ukhpi:{api_key}") or item.get(api_key)
                if val and our_key not in by_region[region_name]:
                    by_region[region_name][our_key] = round(float(val))

        hpi_data = dict(by_region)
        if len(hpi_data) >= 8:
            _save_json_cache(cache_name, hpi_data)
            print(f"  [live] HPI prices: {len(hpi_data)} regions fetched")
            return hpi_data

    except Exception as e:
        print(f"  [live] HPI API unavailable ({e}) - using embedded data")

    return None


# ---------------------------------------------------------------------------
# HPI TREND - annual index series
# ---------------------------------------------------------------------------

def fetch_hpi_trend():

    cache_name = "live_hpi_trend.json"
    if _is_fresh(_cache_path(cache_name)):
        cached = _load_json_cache(cache_name)
        if cached:
            print("  [live] HPI trend: loaded from cache (< 30 days old)")
            return cached

    print("  [live] Fetching HPI trend series...")
    try:
        url = ("https://landregistry.data.gov.uk/data/ukhpi/region.json"
               "?_pageSize=500&_sort=ukhpi%3ArefPeriodStart"
               "&ukhpi%3ArefPeriodStart-min=2015-01-01")
        raw  = _fetch(url, timeout=20)
        data = json.loads(raw)
        items = data.get("result", {}).get("items", [])
        if not items:
            raise ValueError("Empty trend response")

        from collections import defaultdict
        by_region = defaultdict(list)
        for item in items:
            region_name = LR_REGION_MAP.get(item.get("regionName", ""), "")
            if not region_name:
                continue
            idx = item.get("ukhpi:housePriceIndex") or item.get("housePriceIndex")
            if idx:
                by_region[region_name].append(float(idx))

        # Normalise to 2015=100 and sample to 10 annual points
        trend_data = {}
        for region, values in by_region.items():
            if len(values) < 10:
                continue
            # Sample evenly to 10 points
            step = len(values) / 10
            sampled = [values[round(i * step)] for i in range(10)]
            base = sampled[0] if sampled[0] else 100
            trend_data[region] = [round((v / base) * 100) for v in sampled]

        if len(trend_data) >= 8:
            _save_json_cache(cache_name, trend_data)
            print(f"  [live] HPI trend: {len(trend_data)} regions fetched")
            return trend_data

    except Exception as e:
        print(f"  [live] HPI trend API unavailable ({e}) - using embedded data")

    return None


# ---------------------------------------------------------------------------
# MAIN LOADER - merges live + embedded, always returns complete dataset
# ---------------------------------------------------------------------------

def load_live_data():

    print("[data] Loading datasets...")
    notes = {}

    # Start from embedded baselines
    regional  = {k: dict(v) for k, v in REGIONAL.items()}
    hpi       = {k: dict(v) for k, v in HPI.items()}
    hpi_trend = {k: list(v) for k, v in HPI_TREND.items()}
    hpi_years = list(HPI_YEARS)

    # Try live income
    live_income = fetch_regional_income()
    if live_income:
        for region, income in live_income.items():
            if region in regional:
                regional[region]["income"] = income
        notes["income"] = "ONS API (live)"
    else:
        notes["income"] = "ONS GDHI 2023 (embedded)"

    # Try live HPI
    live_hpi = fetch_hpi_by_region()
    if live_hpi:
        for region, prices in live_hpi.items():
            if region in hpi:
                hpi[region].update(prices)
        notes["hpi"] = "HM Land Registry API (live)"
    else:
        notes["hpi"] = "HM Land Registry HPI Q4 2024 (embedded)"

    # Try live trend
    live_trend = fetch_hpi_trend()
    if live_trend:
        for region, trend in live_trend.items():
            if region in hpi_trend:
                hpi_trend[region] = trend
        notes["trend"] = "HM Land Registry API (live)"
    else:
        notes["trend"] = "HM Land Registry 2015-2024 (embedded)"

    print(f"  [data] Income: {notes['income']}")
    print(f"  [data] Prices: {notes['hpi']}")
    print(f"  [data] Trend:  {notes['trend']}")

    return regional, hpi, hpi_trend, hpi_years, notes
