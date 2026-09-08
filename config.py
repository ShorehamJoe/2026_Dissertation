
import os


CACHE_TTL_DAYS       = 30
MODEL_CACHE_TTL_DAYS = 7

# Affordability
DEFAULT_DEPOSIT_PCT  = 0.10
MORTGAGE_RATE        = 0.045
INCOME_GROWTH_RATE   = 0.025
PRICE_GROWTH_PRIOR   = 0.035   
SAVINGS_YEARS_GAP    = 5


SDLT_STANDARD_BANDS = [
    (0,        250_000,    0.00),
    (250_000,  925_000,    0.05),
    (925_000,  1_500_000,  0.10),
    (1_500_000, 99_999_999, 0.12),
]
SDLT_FTB_BANDS = [(0, 425_000, 0.00), (425_000, 625_000, 0.05)]
SDLT_FTB_CAP   = 625_000


FORECAST_YEARS   = [2025, 2026, 2027, 2028, 2029]   
ML_N_ESTIMATORS  = 200
ML_LEARNING_RATE = 0.07
ML_MAX_DEPTH     = 5
ML_SUBSAMPLE     = 0.85
ML_RANDOM_STATE  = 42
CV_FOLDS         = 5
SYNTH_PER_CELL   = 80


_ROOT       = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR   = os.path.join(_ROOT, ".map_cache")
OUTPUTS_DIR = os.path.join(_ROOT, "outputs")
EVAL_DIR    = os.path.join(_ROOT, "evaluation_data")

# ── Land Registry live data ───────────────────────────────────────────────
LR_MONTHLY_URL  = "https://prod.publicdata.landregistry.gov.uk.s3-website-eu-west-1.amazonaws.com/pp-monthly-update-new-version.csv"
LR_COLUMNS      = ["transaction_id", "price", "date", "postcode", "property_type",
                   "old_new", "duration", "paon", "saon", "street", "locality",
                   "town", "district", "county", "ppd_type", "record_status"]
LR_PROPERTY_MAP = {"D": "Detached", "S": "Semi-Detached", "T": "Terraced", "F": "Flat"}
LR_MIN_YEAR     = 2015
LR_PRICE_LOW    = 10_000
LR_PRICE_HIGH   = 5_000_000
LR_DATA_PATH    = "evaluation_data"
LR_CSV_PATH     = "evaluation_data/land_registry.csv"

# ── Cache ─────────────────────────────────────────────────────────────────
CACHE_DIR       = ".cache"
CACHE_TTL_DAYS  = 30

# ── ML model ─────────────────────────────────────────────────────────────
ML_TEST_SIZE    = 0.2
