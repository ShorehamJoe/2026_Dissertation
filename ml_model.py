

import json
import logging
import os
import time

import numpy  as np
import pandas as pd

from uk_housing_dashboard.config import (
    FORECAST_YEARS, ML_RANDOM_STATE, ML_TEST_SIZE,
    CV_FOLDS, BOOTSTRAP_SAMPLES, SYNTH_PER_CELL, SYNTH_LOGNORMAL_SIGMA,
    ML_N_ESTIMATORS, ML_LEARNING_RATE, ML_MAX_DEPTH, ML_SUBSAMPLE,
    INCOME_GROWTH_RATE, PRICE_GROWTH_PRIOR,
    CACHE_DIR, OUTPUTS_DIR, MODEL_CACHE_TTL_DAYS,
)
from uk_housing_dashboard.data.datasets import REGIONAL, HPI, HPI_TREND

log = logging.getLogger(__name__)

MODEL_CACHE = os.path.join(CACHE_DIR, "ml_predictions.json")
PROP_TYPES  = ["Detached", "Semi-Detached", "Terraced", "Flat"]
FEATURES    = ["region_enc", "property_type_enc", "year",
               "affordability_ratio", "median_income", "ons_ratio"]


# ---------------------------------------------------------------------------
# DATASET BUILDER
# ---------------------------------------------------------------------------

def _build_synthetic(regional: dict, hpi: dict, hpi_trend: dict) -> pd.DataFrame:

    rng      = np.random.default_rng(ML_RANDOM_STATE)
    type_enc = {t: i for i, t in enumerate(PROP_TYPES)}
    reg_enc  = {r: i for i, r in enumerate(sorted(regional.keys()))}
    rows     = []

    for region, rd in regional.items():
        if region not in hpi:
            continue
        trend  = hpi_trend.get(region, [100] * 10)
        income = rd["income"]
        ratio  = rd["ratio"]

        for prop_type in PROP_TYPES:
            base = hpi[region].get(prop_type)
            if not base:
                continue
            for yr_idx, year in enumerate(range(2015, 2025)):
                adj   = base * (trend[yr_idx] / trend[-1])
                mu    = np.log(adj) - 0.5 * SYNTH_LOGNORMAL_SIGMA**2
                prices = rng.lognormal(mu, SYNTH_LOGNORMAL_SIGMA, SYNTH_PER_CELL)
                for p in prices:
                    rows.append({
                        "price":              p,
                        "region_enc":         reg_enc[region],
                        "property_type_enc":  type_enc[prop_type],
                        "year":               year,
                        "affordability_ratio": p / income,
                        "median_income":      income,
                        "ons_ratio":          ratio,
                        "region":             region,
                        "property_type":      prop_type,
                    })

    df = pd.DataFrame(rows)
    log.info("Synthetic dataset: %d rows", len(df))
    return df, reg_enc, type_enc


def _build_real(lr_df: pd.DataFrame, regional: dict) -> pd.DataFrame:

    type_enc = {t: i for i, t in enumerate(PROP_TYPES)}
    reg_enc  = {r: i for i, r in enumerate(sorted(regional.keys()))}

    # Filter to property types we model
    lr_df = lr_df[lr_df["property_type"].isin(PROP_TYPES)].copy()

    # Map region income
    income_map = {r: d["income"] for r, d in regional.items()}
    ratio_map  = {r: d["ratio"]  for r, d in regional.items()}
    lr_df["median_income"]      = lr_df["region"].map(income_map)
    lr_df["ons_ratio"]          = lr_df["region"].map(ratio_map)
    lr_df["affordability_ratio"] = lr_df["price"] / lr_df["median_income"]
    lr_df["region_enc"]         = lr_df["region"].map(reg_enc)
    lr_df["property_type_enc"]  = lr_df["property_type"].map(type_enc)
    lr_df = lr_df.dropna(subset=FEATURES + ["price"])

    log.info("Real dataset: %d rows after feature engineering", len(lr_df))
    return lr_df, reg_enc, type_enc


# ---------------------------------------------------------------------------
# CROSS-VALIDATION
# ---------------------------------------------------------------------------

def _cross_validate(model_cls, params: dict, X: np.ndarray, y: np.ndarray) -> dict:

    from sklearn.model_selection import KFold
    from sklearn.metrics import mean_absolute_error, r2_score

    kf       = KFold(n_splits=CV_FOLDS, shuffle=True, random_state=ML_RANDOM_STATE)
    mae_list, r2_list, rmse_list = [], [], []

    for fold, (tr, te) in enumerate(kf.split(X), 1):
        m = model_cls(**params, random_state=ML_RANDOM_STATE)
        m.fit(X[tr], y[tr])
        preds   = np.expm1(m.predict(X[te]))
        actuals = np.expm1(y[te])
        mae_list.append(mean_absolute_error(actuals, preds))
        r2_list.append(r2_score(actuals, preds))
        rmse_list.append(float(np.sqrt(np.mean((actuals - preds)**2))))
        log.debug("  Fold %d: R2=%.4f MAE=%.0f", fold, r2_list[-1], mae_list[-1])

    return {
        "mae_mean":  round(float(np.mean(mae_list))),
        "mae_std":   round(float(np.std(mae_list))),
        "r2_mean":   round(float(np.mean(r2_list)),  4),
        "r2_std":    round(float(np.std(r2_list)),   4),
        "rmse_mean": round(float(np.mean(rmse_list))),
        "rmse_std":  round(float(np.std(rmse_list))),
    }


# ---------------------------------------------------------------------------
# HYPERPARAMETER TUNING
# ---------------------------------------------------------------------------

def _tune_gb(X: np.ndarray, y: np.ndarray) -> dict:

    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.model_selection import GridSearchCV

    grid = {
        "n_estimators":  [100, 200],
        "learning_rate": [0.05, 0.10],
        "max_depth":     [4, 5, 6],
        "subsample":     [0.8],
    }
    base = GradientBoostingRegressor(random_state=ML_RANDOM_STATE)
    gs   = GridSearchCV(base, grid, cv=3, scoring="r2",
                        n_jobs=-1, verbose=0)
    gs.fit(X, y)
    log.info("Best GB params: %s (CV R2=%.4f)", gs.best_params_, gs.best_score_)
    return gs.best_params_


# ---------------------------------------------------------------------------
# MODEL COMPARISON
# ---------------------------------------------------------------------------

def _compare_models(X: np.ndarray, y: np.ndarray) -> dict:

    from sklearn.tree     import DecisionTreeRegressor
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics  import mean_absolute_error, r2_score

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=ML_TEST_SIZE, random_state=ML_RANDOM_STATE
    )

    models = {
        "Decision Tree":    DecisionTreeRegressor(max_depth=10, random_state=ML_RANDOM_STATE),
        "Random Forest":    RandomForestRegressor(n_estimators=100, random_state=ML_RANDOM_STATE, n_jobs=-1),
        "Gradient Boosting": GradientBoostingRegressor(
            n_estimators=ML_N_ESTIMATORS, learning_rate=ML_LEARNING_RATE,
            max_depth=ML_MAX_DEPTH, subsample=ML_SUBSAMPLE, random_state=ML_RANDOM_STATE
        ),
    }

    comparison = {}
    best_model, best_r2 = None, -np.inf

    for name, m in models.items():
        t0 = time.time()
        m.fit(X_tr, y_tr)
        elapsed = time.time() - t0
        preds   = np.expm1(m.predict(X_te))
        actuals = np.expm1(y_te)
        mae     = float(mean_absolute_error(actuals, preds))
        r2      = float(r2_score(actuals, preds))
        rmse    = float(np.sqrt(np.mean((actuals - preds)**2)))
        comparison[name] = {
            "mae": round(mae), "r2": round(r2, 4),
            "rmse": round(rmse), "train_time_s": round(elapsed, 2),
        }
        log.info("  %-22s  R2=%.4f  MAE=GBP%8,.0f  RMSE=GBP%8,.0f  t=%.1fs",
                 name, r2, mae, rmse, elapsed)
        if r2 > best_r2:
            best_r2, best_model = r2, m

    return comparison, best_model


# ---------------------------------------------------------------------------
# BOOTSTRAP CONFIDENCE INTERVALS
# ---------------------------------------------------------------------------

def _bootstrap_ci(X_train: np.ndarray, y_train: np.ndarray,
                  X_pred: np.ndarray, n: int = BOOTSTRAP_SAMPLES) -> tuple:

    from sklearn.ensemble import GradientBoostingRegressor

    preds = []
    rng   = np.random.default_rng(ML_RANDOM_STATE)
    for _ in range(n):
        idx = rng.integers(0, len(X_train), size=len(X_train))
        m   = GradientBoostingRegressor(
            n_estimators=50, learning_rate=ML_LEARNING_RATE,
            max_depth=ML_MAX_DEPTH, random_state=ML_RANDOM_STATE
        )
        m.fit(X_train[idx], y_train[idx])
        preds.append(float(np.expm1(m.predict(X_pred)[0])))

    return (round(np.percentile(preds,  5)),
            round(np.percentile(preds, 95)))


# ---------------------------------------------------------------------------
# FEATURE IMPORTANCE
# ---------------------------------------------------------------------------

def _extract_importance(model, feature_names: list) -> dict:

    if not hasattr(model, "feature_importances_"):
        return {}
    labels = {
        "region_enc":         "Region",
        "property_type_enc":  "Property type",
        "year":               "Transaction year",
        "affordability_ratio": "Affordability ratio",
        "median_income":      "Regional income",
        "ons_ratio":          "ONS ratio",
    }
    return {
        labels.get(f, f): round(float(v), 4)
        for f, v in zip(feature_names, model.feature_importances_)
    }


# ---------------------------------------------------------------------------
# FORECASTING
# ---------------------------------------------------------------------------

def _forecast(model, reg_enc: dict, type_enc: dict,
              X_train: np.ndarray, y_train: np.ndarray,
              regional: dict, hpi: dict) -> dict:

    forecasts = {}

    for region, rd in regional.items():
        if region not in reg_enc:
            continue
        income = rd["income"]
        ratio  = rd["ratio"]
        forecasts[region] = {}

        for prop_type in PROP_TYPES:
            base = hpi.get(region, {}).get(prop_type)
            if not base:
                continue
            forecasts[region][prop_type] = {}

            for year in FORECAST_YEARS:
                yrs_ahead  = year - 2024
                proj_inc   = income  * (1 + INCOME_GROWTH_RATE)  ** yrs_ahead
                proj_price = base    * (1 + PRICE_GROWTH_PRIOR)  ** yrs_ahead
                proj_ratio = proj_price / proj_inc

                X_p = np.array([[
                    reg_enc[region],
                    type_enc.get(prop_type, 0),
                    year, proj_ratio, proj_inc, ratio,
                ]])

                pred = round(float(np.expm1(model.predict(X_p)[0])))
                low, high = _bootstrap_ci(X_train, y_train, X_p,
                                          n=BOOTSTRAP_SAMPLES)
                forecasts[region][prop_type][str(year)] = {
                    "pred": pred, "low": low, "high": high,
                }

    return forecasts


# ---------------------------------------------------------------------------
# SAVE OUTPUTS
# ---------------------------------------------------------------------------

def _save_outputs(comparison: dict, cv_metrics: dict,
                  importance: dict, forecasts: dict) -> None:

    os.makedirs(OUTPUTS_DIR, exist_ok=True)

    # Model comparison CSV
    comp_path = os.path.join(OUTPUTS_DIR, "model_comparison.csv")
    rows = [{"Model": k, **v} for k, v in comparison.items()]
    pd.DataFrame(rows).to_csv(comp_path, index=False)
    log.info("Saved model comparison: %s", comp_path)

    # Cross-validation metrics
    cv_path = os.path.join(OUTPUTS_DIR, "cross_validation_metrics.json")
    with open(cv_path, "w", encoding="utf-8") as f:
        json.dump({"cv_folds": CV_FOLDS, **cv_metrics}, f, indent=2)
    log.info("Saved CV metrics: %s", cv_path)

    # Feature importance
    fi_path = os.path.join(OUTPUTS_DIR, "feature_importance.json")
    with open(fi_path, "w", encoding="utf-8") as f:
        json.dump(importance, f, indent=2)
    log.info("Saved feature importance: %s", fi_path)

    # Feature importance chart
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 4))
        items = sorted(importance.items(), key=lambda x: x[1])
        ax.barh([i[0] for i in items], [i[1] for i in items], color="#2a78d6")
        ax.set_title("Feature Importance - Gradient Boosting Model\n"
                     "MSc Big Data with Banking and Finance | Joseph Richards 2026")
        ax.set_xlabel("Importance score")
        plt.tight_layout()
        fig.savefig(os.path.join(OUTPUTS_DIR, "feature_importance.png"), dpi=150)
        plt.close(fig)
        log.info("Saved feature importance chart")
    except Exception as exc:
        log.warning("Could not save feature importance chart: %s", exc)

    # Residuals chart (Decision Tree vs GB comparison)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        metrics_list = list(comparison.items())
        colours = ["#e34948", "#eda100", "#2a78d6"]
        for ax, (name, m), colour in zip(axes, metrics_list, colours):
            ax.bar(["MAE", "R2*100k", "RMSE"],
                   [m["mae"]/1000, m["r2"]*100000, m["rmse"]/1000],
                   color=colour)
            ax.set_title(name)
            ax.set_ylabel("GBP (thousands) / scaled R2")
        plt.suptitle("Model Performance Comparison\n"
                     "MSc Big Data with Banking and Finance | Joseph Richards 2026",
                     fontsize=12, fontweight="bold")
        plt.tight_layout()
        fig.savefig(os.path.join(OUTPUTS_DIR, "model_comparison.png"), dpi=150)
        plt.close(fig)
        log.info("Saved model comparison chart")
    except Exception as exc:
        log.warning("Could not save model comparison chart: %s", exc)


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------

def load_predictions(regional: dict = None, hpi: dict = None,
                     hpi_trend: dict = None) -> tuple[dict, dict]:

    os.makedirs(CACHE_DIR, exist_ok=True)

    regional  = regional  or {k: dict(v) for k, v in REGIONAL.items()}
    hpi       = hpi       or {k: dict(v) for k, v in HPI.items()}
    hpi_trend = hpi_trend or {k: list(v) for k, v in HPI_TREND.items()}

    # Check cache
    if os.path.exists(MODEL_CACHE):
        age = (time.time() - os.path.getmtime(MODEL_CACHE)) / 86400
        if age < MODEL_CACHE_TTL_DAYS:
            try:
                with open(MODEL_CACHE, encoding="utf-8") as f:
                    cached = json.load(f)
                log.info("ML forecasts loaded from cache (%.0f days old)", age)
                return cached["forecasts"], cached["metrics"]
            except Exception as exc:
                log.warning("Cache unreadable: %s", exc)

    try:
        from sklearn.ensemble import GradientBoostingRegressor
    except ImportError:
        log.warning("scikit-learn not installed. Run: pip install scikit-learn")
        return {}, {}

    # Attempt real data
    df_real = None
    try:
        from uk_housing_dashboard.data.land_registry import load_real_data
        df_real = load_real_data()
    except Exception as exc:
        log.warning("Real data unavailable: %s", exc)

    if df_real is not None and len(df_real) >= 1000:
        log.info("[ml] Training on REAL Land Registry data (%d rows)", len(df_real))
        df, reg_enc, type_enc = _build_real(df_real, regional)
        data_source = "real"
    else:
        log.info("[ml] Training on SYNTHETIC data (real data unavailable)")
        df, reg_enc, type_enc = _build_synthetic(regional, hpi, hpi_trend)
        data_source = "synthetic"

    X = df[FEATURES].values
    y = np.log1p(df["price"].values)

    # Hyperparameter tuning
    log.info("[ml] Running GridSearchCV hyperparameter tuning...")
    best_params = _tune_gb(X, y)

    # Model comparison
    log.info("[ml] Comparing models (Decision Tree / Random Forest / Gradient Boosting)...")
    comparison, best_model = _compare_models(X, y)

    # Cross-validation on best model
    log.info("[ml] Running %d-fold cross-validation...", CV_FOLDS)
    cv_metrics = _cross_validate(GradientBoostingRegressor, best_params, X, y)
    log.info("[ml] CV R2 = %.4f +/- %.4f  MAE = GBP%,.0f +/- GBP%,.0f",
             cv_metrics["r2_mean"], cv_metrics["r2_std"],
             cv_metrics["mae_mean"], cv_metrics["mae_std"])

    # Feature importance
    importance = _extract_importance(best_model, FEATURES)

    # Forecasts with bootstrap CI
    log.info("[ml] Generating forecasts with %d bootstrap samples...", BOOTSTRAP_SAMPLES)
    forecasts = _forecast(best_model, reg_enc, type_enc, X, y, regional, hpi)

    # Save outputs
    _save_outputs(comparison, cv_metrics, importance, forecasts)

    # Combine metrics for dashboard display
    metrics = {
        **cv_metrics,
        "data_source": data_source,
        "model":       "Gradient Boosting",
        "best_params": best_params,
        "comparison":  comparison,
        "importance":  importance,
    }

    # Cache
    with open(MODEL_CACHE, "w", encoding="utf-8") as f:
        json.dump({"forecasts": forecasts, "metrics": metrics}, f)

    log.info("[ml] Done - %d regions forecast, outputs saved to %s", len(forecasts), OUTPUTS_DIR)
    return forecasts, metrics
