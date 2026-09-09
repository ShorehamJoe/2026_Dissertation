

import json
import logging
import os
import time

import numpy as np

from uk_housing_dashboard.config import (
    FORECAST_YEARS, ML_N_ESTIMATORS, ML_LEARNING_RATE,
    ML_MAX_DEPTH, ML_SUBSAMPLE, ML_RANDOM_STATE,
    CV_FOLDS, SYNTH_PER_CELL,
    CACHE_DIR, OUTPUTS_DIR, MODEL_CACHE_TTL_DAYS,
    INCOME_GROWTH_RATE, DEFAULT_DEPOSIT_PCT, SAVINGS_YEARS_GAP,
)
from uk_housing_dashboard.data.datasets import (
    REGIONAL, HPI, HPI_TREND, HPI_YEARS, COHORTS, CPIH_INDEX,
)

log = logging.getLogger(__name__)

PROP_TYPES   = ["Detached", "Semi-Detached", "Terraced", "Flat"]
FEATURES     = [
    "region_enc", "property_type_enc", "year", "year_norm",
    "affordability_ratio", "median_income", "ons_ratio",
    "momentum_yoy", "growth_3yr",
]
MODEL_CACHE  = os.path.join(CACHE_DIR, "ml_forecast_5yr.json")


# ---------------------------------------------------------------------------
# DATASET BUILDER
# ---------------------------------------------------------------------------

def _build_dataset(regional, hpi, hpi_trend):

    rng      = np.random.default_rng(ML_RANDOM_STATE)
    reg_enc  = {r: i for i, r in enumerate(sorted(regional.keys()))}
    type_enc = {t: i for i, t in enumerate(PROP_TYPES)}
    rows     = []

    for region, rd in regional.items():
        idx    = hpi_trend.get(region, [100] * 10)
        income = rd["income"]
        ratio  = rd["ratio"]

        for prop_type in PROP_TYPES:
            base = hpi.get(region, {}).get(prop_type)
            if not base:
                continue

            for yr_i, year in enumerate(HPI_YEARS):
                year_price = base * (idx[yr_i] / idx[-1])
                mu         = np.log(year_price) - 0.5 * 0.28 ** 2
                prices     = rng.lognormal(mu, 0.28, size=SYNTH_PER_CELL)

                momentum = (idx[yr_i] - idx[yr_i-1]) / idx[yr_i-1] if yr_i > 0 else 0.0
                rolling3 = (idx[yr_i] / idx[max(0, yr_i-3)] - 1) if yr_i >= 3 else momentum

                for p in prices:
                    rows.append([
                        reg_enc[region],
                        type_enc[prop_type],
                        year,
                        (year - 2015) / 9,
                        p / income,
                        income,
                        ratio,
                        momentum,
                        rolling3,
                        p,   # target
                    ])

    arr = np.array(rows, dtype=np.float64)
    X   = arr[:, :len(FEATURES)]
    y   = np.log1p(arr[:, -1])
    log.info("[ml] Dataset: %d rows (%d regions x %d types x %d years x %d)",
             len(X), len(regional), len(PROP_TYPES), len(HPI_YEARS), SYNTH_PER_CELL)
    return X, y, reg_enc, type_enc


# ---------------------------------------------------------------------------
# CROSS-VALIDATION
# ---------------------------------------------------------------------------

def _cross_validate(X, y):

    from sklearn.ensemble        import GradientBoostingRegressor
    from sklearn.model_selection import KFold
    from sklearn.metrics         import mean_absolute_error, r2_score

    kf   = KFold(n_splits=CV_FOLDS, shuffle=True, random_state=ML_RANDOM_STATE)
    r2s, maes, rmses = [], [], []

    for fold, (tr, te) in enumerate(kf.split(X), 1):
        m = GradientBoostingRegressor(
            n_estimators=ML_N_ESTIMATORS, learning_rate=ML_LEARNING_RATE,
            max_depth=ML_MAX_DEPTH, subsample=ML_SUBSAMPLE,
            min_samples_leaf=10, random_state=ML_RANDOM_STATE,
        )
        m.fit(X[tr], y[tr])
        preds   = np.expm1(m.predict(X[te]))
        actuals = np.expm1(y[te])
        r2s.append(float(r2_score(actuals, preds)))
        maes.append(float(mean_absolute_error(actuals, preds)))
        rmses.append(float(np.sqrt(np.mean((actuals - preds) ** 2))))
        log.info("  Fold %d: R2=%.4f  MAE=GBP%,.0f", fold, r2s[-1], maes[-1])

    return {
        "r2_mean":   round(float(np.mean(r2s)),   4),
        "r2_std":    round(float(np.std(r2s)),    4),
        "mae_mean":  round(float(np.mean(maes))),
        "mae_std":   round(float(np.std(maes))),
        "rmse_mean": round(float(np.mean(rmses))),
        "cv_folds":  CV_FOLDS,
    }


# ---------------------------------------------------------------------------
# CONFIDENCE INTERVAL (fast, residual-based)
# ---------------------------------------------------------------------------

def _ci(model, X_train, y_train, pred):

    train_preds = np.expm1(model.predict(X_train))
    actuals     = np.expm1(y_train)
    rmse        = float(np.sqrt(np.mean((actuals - train_preds) ** 2)))
    mean_price  = float(np.mean(actuals))
    scale       = max(pred / mean_price, 0.5) if mean_price > 0 else 1.0
    margin      = 1.645 * rmse * scale
    return round(max(0, pred - margin)), round(pred + margin)


# ---------------------------------------------------------------------------
# FORECAST FEATURE BUILDER
# ---------------------------------------------------------------------------

def _forecast_X(region, prop_type, year, reg_enc, type_enc, regional):

    rd     = regional[region]
    income = rd["income"]
    ratio  = rd["ratio"]
    idx    = HPI_TREND.get(region, [100] * 10)

    # Recent 2-year average growth (post-COVID normalisation period)
    recent = (idx[-1] / idx[-3] - 1) / 2 if len(idx) >= 3 else 0.035

    # Mean reversion toward 3.5% long-run equilibrium
    yrs_ahead  = year - 2024
    equilibrium = 0.035
    revert      = 0.30
    momentum    = recent + (equilibrium - recent) * (1 - (1 - revert) ** yrs_ahead)
    cum_growth  = (1 + momentum) ** yrs_ahead - 1
    proj_price  = HPI.get(region, {}).get(prop_type, ratio * income) * (1 + cum_growth)
    proj_income = income * (1 + INCOME_GROWTH_RATE) ** yrs_ahead

    return np.array([[
        reg_enc.get(region, 0),
        type_enc.get(prop_type, 0),
        year,
        (year - 2015) / 9,
        proj_price / proj_income if proj_income > 0 else ratio,
        proj_income,
        ratio,
        momentum,
        cum_growth,
    ]])


# ---------------------------------------------------------------------------
# AFFORDABILITY FROM FORECASTS
# ---------------------------------------------------------------------------

def _compute_afford(forecasts, regional):

    afford = {}
    for region, rd in regional.items():
        afford[region] = {}
        income_2024    = rd["income"]

        for year in FORECAST_YEARS:
            proj_income = income_2024 * (1 + INCOME_GROWTH_RATE) ** (year - 2024)
            afford[region][str(year)] = {}

            for prop_type in PROP_TYPES:
                pred  = forecasts.get(region, {}).get(prop_type, {}).get(str(year), {}).get("pred", 0)
                if not pred:
                    continue
                deposit = pred * DEFAULT_DEPOSIT_PCT
                ratio   = round(pred / proj_income, 1)
                cohorts = {}
                for c in COHORTS:
                    annual  = proj_income * c["rate"]
                    yts     = round(deposit / annual, 1) if annual > 0 else 99
                    gap5    = round(max(0, deposit - annual * SAVINGS_YEARS_GAP))
                    pct5    = round(min(100, annual * SAVINGS_YEARS_GAP / deposit * 100), 1) if deposit else 0
                    cohorts[c["label"]] = {
                        "years_to_save": yts,
                        "gap_5yr":       gap5,
                        "pct_saved_5yr": pct5,
                    }
                afford[region][str(year)][prop_type] = {
                    "price":   pred,
                    "deposit": round(deposit),
                    "ratio":   ratio,
                    "cohorts": cohorts,
                }
    return afford


# ---------------------------------------------------------------------------
# SAVE CHARTS
# ---------------------------------------------------------------------------

def _save_charts(forecasts, afford):

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker
        import seaborn as sns

        os.makedirs(OUTPUTS_DIR, exist_ok=True)
        fmt_gbp = mticker.FuncFormatter(lambda x, _: f"GBP{x:,.0f}")

        # Chart 1: 12-panel regional forecast (Semi-Detached)
        fig, axes = plt.subplots(3, 4, figsize=(20, 13))
        fig.suptitle(
            "UK Housing Price Forecast 2025-2029 - Semi-Detached\n"
            "Gradient Boosting | 90% Analytical CI | "
            "MSc Big Data with Banking & Finance | Joseph Richards 2026",
            fontsize=11, fontweight="bold", y=0.98
        )
        colours = plt.cm.tab20.colors

        for ax, (region, rd), colour in zip(axes.flatten(), REGIONAL.items(), colours):
            idx       = HPI_TREND.get(region, [100] * 10)
            base      = HPI.get(region, {}).get("Semi-Detached", rd["ratio"] * rd["income"])
            hist      = [base * (idx[i] / idx[-1]) for i in range(len(HPI_YEARS))]
            fy        = FORECAST_YEARS
            fp        = [forecasts[region]["Semi-Detached"][str(y)]["pred"] for y in fy]
            flo       = [forecasts[region]["Semi-Detached"][str(y)]["low"]  for y in fy]
            fhi       = [forecasts[region]["Semi-Detached"][str(y)]["high"] for y in fy]
            pct_29    = forecasts[region]["Semi-Detached"][str(fy[-1])]["pct_change"]

            ax.plot(HPI_YEARS, hist, color=colour, linewidth=2.2, label="Historical")
            ax.fill_between(HPI_YEARS, hist, alpha=0.1, color=colour)
            ax.plot([2024] + fy, [hist[-1]] + fp, color=colour, linewidth=2.2,
                    linestyle="--", label="Forecast")
            ax.fill_between([2024] + fy, [hist[-1]] + flo, [hist[-1]] + fhi,
                            alpha=0.18, color=colour, label="90% CI")
            ax.axvline(x=2024, color="#999", linestyle=":", linewidth=1)
            ax.annotate(f"GBP{fp[-1]:,.0f}\n({pct_29:+.1f}%)",
                        xy=(fy[-1], fp[-1]), fontsize=7.5, ha="right",
                        color=colour, fontweight="bold")
            ax.set_title(region, fontsize=8.5, fontweight="bold")
            ax.yaxis.set_major_formatter(fmt_gbp)
            ax.tick_params(labelsize=7)
            ax.grid(alpha=0.22)
            ax.legend(fontsize=6, loc="upper left")

        plt.tight_layout()
        path = os.path.join(OUTPUTS_DIR, "forecast_regional_5yr.png")
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        log.info("[ml] Saved: %s", path)

        # Chart 2: Gen Z deposit heatmap
        regions  = list(REGIONAL.keys())
        gen_z    = COHORTS[0]["label"]
        data     = np.array([
            [afford[r][str(y)].get("Semi-Detached", {}).get("cohorts", {})
              .get(gen_z, {}).get("years_to_save", 0)
             for y in FORECAST_YEARS]
            for r in regions
        ])
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(data, annot=True, fmt=".1f", cmap="RdYlGn_r",
                    xticklabels=FORECAST_YEARS, yticklabels=regions,
                    ax=ax, linewidths=0.4,
                    cbar_kws={"label": "Years to save 10% deposit"})
        ax.set_title(
            "Gen Z (18-27): Years to Save a 10% Deposit - 5-Year Forecast\n"
            "Semi-Detached | ONS WAS Wave 7 savings rates | Joseph Richards 2026",
            fontsize=10
        )
        plt.tight_layout()
        path2 = os.path.join(OUTPUTS_DIR, "forecast_gen_z_heatmap.png")
        fig.savefig(path2, dpi=150, bbox_inches="tight")
        plt.close(fig)
        log.info("[ml] Saved: %s", path2)

        # Chart 3: Intergenerational gap
        sample = ["London", "South East", "Yorkshire and The Humber",
                  "North East", "Wales", "Scotland"]
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        fig.suptitle(
            "Intergenerational Deposit Gap (Gen Z vs Baby Boomers) 2024-2029\n"
            "Years to save 10% deposit | Semi-Detached | Joseph Richards 2026",
            fontsize=11, fontweight="bold"
        )
        for ax, region in zip(axes.flatten(), sample):
            rd    = REGIONAL[region]
            base  = HPI.get(region, {}).get("Semi-Detached", rd["ratio"] * rd["income"])
            inc24 = rd["income"]

            def yts(price, income, rate):
                return (price * DEFAULT_DEPOSIT_PCT) / (income * rate) if income * rate > 0 else 99

            gz_yrs = [yts(base, inc24, COHORTS[0]["rate"])]
            bm_yrs = [yts(base, inc24, COHORTS[3]["rate"])]
            years_all = [2024] + FORECAST_YEARS

            for year in FORECAST_YEARS:
                inc = inc24 * (1 + INCOME_GROWTH_RATE) ** (year - 2024)
                sd  = afford.get(region, {}).get(str(year), {}).get("Semi-Detached", {})
                pr  = sd.get("price", base)
                gz_yrs.append(yts(pr, inc, COHORTS[0]["rate"]))
                bm_yrs.append(yts(pr, inc, COHORTS[3]["rate"]))

            gaps = [g - b for g, b in zip(gz_yrs, bm_yrs)]
            ax.fill_between(years_all, gz_yrs, bm_yrs, alpha=0.22, color="#e34948")
            ax.plot(years_all, gz_yrs,  "#e34948", linewidth=2.2, label="Gen Z")
            ax.plot(years_all, bm_yrs,  "#1baf7a", linewidth=2.2, label="Baby Boomers")
            ax.axvline(x=2024, color="#888", linestyle=":", linewidth=1)
            ax.set_title(f"{region}\n2029 gap: {gaps[-1]:.1f} yrs",
                         fontsize=8.5, fontweight="bold")
            ax.set_ylabel("Years to save deposit", fontsize=8)
            ax.legend(fontsize=7)
            ax.grid(alpha=0.22)

        plt.tight_layout()
        path3 = os.path.join(OUTPUTS_DIR, "forecast_ig_gap.png")
        fig.savefig(path3, dpi=150, bbox_inches="tight")
        plt.close(fig)
        log.info("[ml] Saved: %s", path3)

    except Exception as exc:
        log.warning("[ml] Chart generation failed: %s", exc)


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------

def load_predictions(regional=None, hpi=None, hpi_trend=None):

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
                log.info("[ml] Loaded from cache (%.0f days old)", age)
                return cached["forecasts"], cached["afford"], cached["metrics"]
            except Exception:
                pass

    try:
        from sklearn.ensemble import GradientBoostingRegressor
    except ImportError:
        log.warning("[ml] scikit-learn not installed. Run: pip install scikit-learn")
        return {}, {}, {}

    log.info("[ml] Training 5-year forecast model...")
    X, y, reg_enc, type_enc = _build_dataset(regional, hpi, hpi_trend)

    log.info("[ml] Running %d-fold cross-validation...", CV_FOLDS)
    metrics = _cross_validate(X, y)
    log.info("[ml] CV R2=%.4f +/-%.4f  MAE=GBP%,.0f", metrics["r2_mean"],
             metrics["r2_std"], metrics["mae_mean"])

    # Final model on all data
    model = GradientBoostingRegressor(
        n_estimators=ML_N_ESTIMATORS, learning_rate=ML_LEARNING_RATE,
        max_depth=ML_MAX_DEPTH, subsample=ML_SUBSAMPLE,
        min_samples_leaf=10, random_state=ML_RANDOM_STATE,
    )
    model.fit(X, y)

    # Feature importance
    metrics["importance"] = {
        FEATURES[i]: round(float(v), 4)
        for i, v in enumerate(model.feature_importances_)
    }

    # Generate forecasts
    log.info("[ml] Generating forecasts 2025-2029...")
    forecasts = {}
    for region in regional:
        forecasts[region] = {}
        for prop_type in PROP_TYPES:
            forecasts[region][prop_type] = {}
            base = hpi.get(region, {}).get(prop_type)
            if not base:
                continue
            for year in FORECAST_YEARS:
                X_p  = _forecast_X(region, prop_type, year, reg_enc, type_enc, regional)
                pred = round(float(np.expm1(model.predict(X_p)[0])))
                lo, hi = _ci(model, X, y, pred)

                # Real-terms price (projected CPIH ~2.5%/yr)
                proj_cpih  = 133.1 * (1.025 ** (year - 2024))
                real_price = round(pred * (133.1 / proj_cpih))

                forecasts[region][prop_type][str(year)] = {
                    "pred":       pred,
                    "low":        lo,
                    "high":       hi,
                    "real_price": real_price,
                    "pct_change": round((pred / base - 1) * 100, 1),
                }

    afford = _compute_afford(forecasts, regional)

    # Save charts
    _save_charts(forecasts, afford)

    # Cache
    with open(MODEL_CACHE, "w", encoding="utf-8") as f:
        json.dump({"forecasts": forecasts, "afford": afford, "metrics": metrics}, f)

    log.info("[ml] Done. Forecasts: %d regions x %d types x %d years",
             len(forecasts), len(PROP_TYPES), len(FORECAST_YEARS))
    return forecasts, afford, metrics
