
import json
import logging
import os
import tempfile
import webbrowser

from uk_housing_dashboard.config import OUTPUTS_DIR, CACHE_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def run():
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    os.makedirs(CACHE_DIR,   exist_ok=True)

    log.info("=" * 55)
    log.info("UK Housing Affordability Dashboard")
    log.info("MSc Big Data with Banking and Finance")
    log.info("Sheffield Hallam University | Joseph Richards 2026")
    log.info("=" * 55)


    log.info("[1/3] Training 5-year predictive model (2025-2029)...")
    try:
        from uk_housing_dashboard.data.ml_forecast import load_predictions
        forecasts, afford, metrics = load_predictions()
        log.info(
            "      Model ready: R2=%.4f +/-%.4f  MAE=GBP%,.0f  "
            "Regions=%d  Years=%d",
            metrics.get("r2_mean", 0), metrics.get("r2_std", 0),
            metrics.get("mae_mean", 0), len(forecasts), 5,
        )
    except Exception as exc:
        log.warning("      ML model unavailable (%s) - dashboard runs without forecasts", exc)
        forecasts, afford, metrics = {}, {}, {}


    log.info("[2/3] Loading LAD boundaries...")
    try:
        from uk_housing_dashboard.map.geojson_loader import load_geojson
        geojson_str = load_geojson()
    except Exception as exc:
        log.warning("      Boundaries unavailable (%s) - city-only mode", exc)
        geojson_str = "null"

  
    log.info("[3/3] Building dashboard...")
    from uk_housing_dashboard.map.html_builder import build
    html = build(
        geojson_str,
        forecasts=forecasts,
        afford=afford,
        metrics=metrics,
    )

    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False,
        prefix="uk_housing_dashboard_", encoding="utf-8",
    )
    tmp.write(html)
    tmp.close()

    log.info("Opening dashboard: %s", tmp.name)
    if forecasts:
        log.info(
            "5-year forecasts: %d regions | "
            "R2=%.4f | MAE=GBP%,.0f | Charts saved to %s",
            len(forecasts), metrics.get("r2_mean", 0),
            metrics.get("mae_mean", 0), OUTPUTS_DIR,
        )
    webbrowser.open(f"file://{tmp.name}")
    log.info("Dashboard ready.")


if __name__ == "__main__":
    run()
