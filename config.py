
import os

# Cache
CACHE_TTL_DAYS       = 30
MODEL_CACHE_TTL_DAYS = 7

# Affordability
DEFAULT_DEPOSIT_PCT  = 0.10
MORTGAGE_RATE        = 0.045
INCOME_GROWTH_RATE   = 0.025
PRICE_GROWTH_PRIOR   = 0.035   # long-run UK equilibrium
SAVINGS_YEARS_GAP    = 5

# Stamp Duty (England 2024)
SDLT_STANDARD_BANDS = [
    (0,        250_000,    0.00),
    (250_000,  925_000,    0.05),
    (925_000,  1_500_000,  0.10),
    (1_500_000, 99_999_999, 0.12),
]
SDLT_FTB_BANDS = [(0, 425_000, 0.00), (425_000, 625_000, 0.05)]
SDLT_FTB_CAP   = 625_000

# ML
FORECAST_YEARS   = [2025, 2026, 2027, 2028, 2029]   # 5-year forecast
ML_N_ESTIMATORS  = 200
ML_LEARNING_RATE = 0.07
ML_MAX_DEPTH     = 5
ML_SUBSAMPLE     = 0.85
ML_RANDOM_STATE  = 42
CV_FOLDS         = 5
SYNTH_PER_CELL   = 80

# Paths
_ROOT       = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR   = os.path.join(_ROOT, ".map_cache")
OUTPUTS_DIR = os.path.join(_ROOT, "outputs")
EVAL_DIR    = os.path.join(_ROOT, "evaluation_data")
