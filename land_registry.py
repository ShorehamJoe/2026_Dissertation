

import os
import io
import logging
import urllib.request
import json

import numpy  as np
import pandas as pd

from uk_housing_dashboard.config import (
    LR_MONTHLY_URL, LR_COLUMNS, LR_PROPERTY_MAP,
    LR_MIN_YEAR, LR_PRICE_LOW, LR_PRICE_HIGH,
    CACHE_DIR, LR_DATA_PATH, LR_CSV_PATH,
    CACHE_TTL_DAYS,
)
from uk_housing_dashboard.data.datasets import REGIONAL

log = logging.getLogger(__name__)

# ONS postcode-district to region lookup (built from ONS NSPL, abbreviated)
# Full lookup at: https://geoportal.statistics.gov.uk/datasets/national-statistics-postcode-lookup
POSTCODE_TO_REGION = {
    # London
    "EC": "London", "WC": "London", "E":  "London", "N":  "London",
    "NW": "London", "SE": "London", "SW": "London", "W":  "London",
    "BR": "London", "CR": "London", "DA": "London", "EN": "London",
    "HA": "London", "IG": "London", "KT": "London", "RM": "London",
    "SM": "London", "TW": "London", "UB": "London", "WD": "London",
    # South East
    "RH": "South East", "GU": "South East", "KY": "South East",
    "BN": "South East", "PO": "South East", "SO": "South East",
    "RG": "South East", "SL": "South East", "HP": "South East",
    "LU": "South East", "AL": "South East", "SG": "South East",
    "CM": "South East", "SS": "South East", "CO": "South East",
    "IP": "East of England", "NR": "East of England", "PE": "East of England",
    "CB": "East of England", "MK": "East of England",
    # South West
    "BS": "South West", "BA": "South West", "GL": "South West",
    "SN": "South West", "SP": "South West", "DT": "South West",
    "BH": "South West", "EX": "South West", "TQ": "South West",
    "PL": "South West", "TR": "South West", "TA": "South West",
    # West Midlands
    "B":  "West Midlands", "CV": "West Midlands", "WS": "West Midlands",
    "WV": "West Midlands", "DY": "West Midlands", "ST": "West Midlands",
    "TF": "West Midlands", "WR": "West Midlands", "HR": "West Midlands",
    # East Midlands
    "DE": "East Midlands", "NG": "East Midlands", "LE": "East Midlands",
    "NN": "East Midlands", "LN": "East Midlands",
    # Yorkshire
    "LS": "Yorkshire and The Humber", "BD": "Yorkshire and The Humber",
    "HX": "Yorkshire and The Humber", "WF": "Yorkshire and The Humber",
    "HD": "Yorkshire and The Humber", "HG": "Yorkshire and The Humber",
    "YO": "Yorkshire and The Humber", "HU": "Yorkshire and The Humber",
    "DN": "Yorkshire and The Humber", "S":  "Yorkshire and The Humber",
    # North West
    "M":  "North West", "SK": "North West", "OL": "North West",
    "BL": "North West", "WN": "North West", "PR": "North West",
    "FY": "North West", "BB": "North West", "LA": "North West",
    "CH": "North West", "WA": "North West", "CW": "North West",
    "L":  "North West",
    # North East
    "NE": "North East", "SR": "North East", "DH": "North East",
    "DL": "North East", "TS": "North East",
    # Wales
    "CF": "Wales", "SA": "Wales", "NP": "Wales", "LD": "Wales",
    "SY": "Wales", "LL": "Wales",
    # Scotland
    "EH": "Scotland", "G":  "Scotland", "ML": "Scotland", "KA": "Scotland",
    "PA": "Scotland", "KY": "Scotland", "DD": "Scotland", "AB": "Scotland",
    "IV": "Scotland", "PH": "Scotland",
    # Northern Ireland
    "BT": "Northern Ireland",
}


def _postcode_to_region(postcode: str) -> str:

    if not postcode or not isinstance(postcode, str):
        return ""
    p = postcode.strip().upper()
    # Try 2-char prefix first, then 1-char
    for length in (2, 1):
        region = POSTCODE_TO_REGION.get(p[:length], "")
        if region:
            return region
    return ""


def _cache_stale() -> bool:

    import time
    if not os.path.exists(LR_DATA_PATH):
        return True
    age_days = (time.time() - os.path.getmtime(LR_DATA_PATH)) / 86400
    return age_days > CACHE_TTL_DAYS


def download_and_clean(use_complete: bool = False) -> pd.DataFrame | None:

    url = (
        "http://prod.publicdata.landregistry.gov.uk.s3-website-eu-west-1.amazonaws.com"
        "/pp-complete.csv" if use_complete else
        "http://prod.publicdata.landregistry.gov.uk.s3-website-eu-west-1.amazonaws.com"
        "/pp-monthly-update-new-version.csv"
    )
    log.info("Downloading Land Registry data from: %s", url)
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "uk-housing-dashboard/3.0 (academic research)"}
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
        log.info("Downloaded %s MB", f"{len(raw)/1e6:.1f}")
    except Exception as exc:
        log.warning("Land Registry download failed: %s", exc)
        return None

    try:
        df = pd.read_csv(
            io.BytesIO(raw),
            header=None,
            names=LR_COLUMNS,
            low_memory=False,
        )
    except Exception as exc:
        log.warning("Land Registry CSV parse failed: %s", exc)
        return None

    return _clean(df)



    log.info("Cleaning %d raw rows...", len(df))

    # Price: numeric, positive
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df[df["price"] > 0].copy()

    # Year from date_of_transfer
    df["year"] = pd.to_datetime(df["date_of_transfer"], errors="coerce").dt.year
    df = df.dropna(subset=["year"])
    df["year"] = df["year"].astype(int)
    df = df[df["year"] >= LR_MIN_YEAR]

    # Property type
    df["property_type"] = df["property_type"].map(LR_PROPERTY_MAP)
    df = df[df["property_type"].notna()]

    # Region from postcode
    df["region"] = df["postcode"].apply(_postcode_to_region)
    df = df[df["region"] != ""]

    # Remove outliers per region/type
    clean_parts = []
    for (region, ptype), grp in df.groupby(["region", "property_type"]):
        lo = grp["price"].quantile(LR_PRICE_LOW)
        hi = grp["price"].quantile(LR_PRICE_HIGH)
        clean_parts.append(grp[(grp["price"] >= lo) & (grp["price"] <= hi)])
    df = pd.concat(clean_parts, ignore_index=True)

    result = df[["price", "year", "region", "property_type"]].copy()
    log.info("Clean dataset: %d rows", len(result))
    return result


def load_real_data() -> pd.DataFrame | None:

    os.makedirs(CACHE_DIR, exist_ok=True)

    # Return cached Parquet if fresh
    if not _cache_stale():
        try:
            df = pd.read_parquet(LR_DATA_PATH)
            log.info("Loaded %d rows from cache: %s", len(df), LR_DATA_PATH)
            return df
        except Exception as exc:
            log.warning("Parquet cache unreadable: %s", exc)

    # Download monthly update
    df = download_and_clean(use_complete=False)
    if df is None or len(df) < 100:
        log.warning("Real data unavailable - falling back to synthetic dataset")
        return None

    # Cache as Parquet for fast future loads
    try:
        df.to_parquet(LR_DATA_PATH, index=False)
        log.info("Cached %d rows to %s", len(df), LR_DATA_PATH)
    except Exception as exc:
        log.warning("Could not write Parquet cache: %s", exc)

    return df

def _clean(df):
    from uk_housing_dashboard.config import LR_MIN_YEAR, LR_PRICE_LOW, LR_PRICE_HIGH, LR_PROPERTY_MAP
    df = df.copy()
    df = df[df["price"].between(LR_PRICE_LOW, LR_PRICE_HIGH)]
    df["property_type"] = df["property_type"].map(LR_PROPERTY_MAP).fillna("Other")
    return df