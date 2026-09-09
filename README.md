# UK Housing Affordability Dashboard v4

**MSc Big Data with Banking and Finance**
Sheffield Hallam University | Joseph Richards | 2026

Dissertation: *"A Data-Driven Model for Predicting UK Housing Affordability
Across Generations Using Wealth and Income Distribution Data"*

Supervised by Joshua Thompson

---

## Quick start

```bash
pip install -r requirements.txt
python run.py
```

---

## Structure

```
uk_housing_dashboard/
  config.py                  Single source of truth for all constants
  main.py                    Entry point - orchestrates all steps
  run.py                     Top-level launcher

  data/
    datasets.py              Embedded ONS / Land Registry datasets (fallback)
    live_data.py             Live API fetch (ONS + Land Registry, 30-day TTL)
    land_registry.py         Real LR bulk data downloader + cleaner
    ml_model.py              Gradient Boosting with CV, grid search, bootstrap CI

  map/
    geojson_loader.py        LAD boundary GeoJSON (ONS, 30-day TTL)
    html_builder.py          Assembles the complete HTML dashboard
    panels.py                JavaScript panel section builders
    styles.py                CSS stylesheet

  utils/
    cache.py                 Network fetch + configurable TTL cache
    calculators.py           SDLT calculator with doctests
    evaluation.py            User evaluation form + analysis
    logger.py                Logging setup (console + file)
    postcode.py              Postcode-to-LAD lookup (postcodes.io)

  tests/
    test_dashboard.py        43 unit + integration tests

  outputs/                   Generated on first run
    model_comparison.csv     Decision Tree / RF / GB comparison
    cross_validation_metrics.json  5-fold CV results
    feature_importance.json  GB feature importances
    feature_importance.png   Chart
    model_comparison.png     Performance comparison chart
    gantt_chart.png          Dissertation project Gantt
    evaluation_summary.txt   Auto-generated after 1+ eval response
    dashboard.log            Full run log with timestamps
```

---

## Features

| Feature | Detail |
|---|---|
| Live data | ONS GDHI + Land Registry HPI APIs (30-day cache) |
| Real LR data | Bulk download integration (falls back to synthetic if unavailable) |
| ML forecasts | Gradient Boosting, 5-fold CV, GridSearchCV tuning, bootstrap CI |
| Model comparison | Decision Tree / Random Forest / Gradient Boosting side-by-side |
| Choropleth map | 318 LADs coloured by affordability ratio |
| Year animation | Play button animates 2015-2024 price history |
| Postcode search | Zooms map and loads LAD panel via postcodes.io |
| Price sparkline | Year-on-year HPI chart per region |
| ML forecast panel | 2025-2027 with bootstrap confidence intervals |
| Feature importance | Per-region chart showing model drivers |
| FTB vs all-buyer | First-time buyer price comparison |
| Deposit gap | Years-to-save and 5-year shortfall by cohort |
| Stamp duty | Full band breakdown, FTB relief, cap warning |
| Rent vs buy | Monthly mortgage vs rent as % income, verdict |
| PDF export | Prints current data panel to A4 |
| Colour-blind mode | Blue-orange Okabe-Ito palette toggle |
| Accessibility | ARIA labels, keyboard nav, mobile responsive |
| User evaluation | 14-question TAM + research form, auto-analysis |
| Gantt chart | Auto-generated dissertation project timeline |
| Logging | Timestamped log to outputs/dashboard.log |

---

## Running tests

```bash
pytest uk_housing_dashboard/tests/test_dashboard.py -v
```

43 tests covering: config, datasets, SDLT calculator, HTML builder,
Land Registry cleaner, ML model, evaluation form, cache, integration.

Running doctests:

```bash
python -m doctest uk_housing_dashboard/utils/calculators.py -v
```

---

## Data sources (all Open Government Licence v3.0)

| Dataset | Source | Used for |
|---|---|---|
| Regional GDHI | ONS Regional Economic Analysis 2023 | Regional income |
| UK HPI prices | HM Land Registry Q4 2024 | Embedded price baseline |
| UK HPI bulk CSV | HM Land Registry (live) | Real model training data |
| HPI annual trend | HM Land Registry 2015-2024 | Sparkline + year slider |
| Housing affordability ratios | ONS 2023 | Map colouring, panel KPI |
| Savings rates | ONS Wealth & Assets Survey Wave 7 | Cohort deposit calculator |
| Homeownership | Resolution Foundation / ONS LFS 2023 | Panel KPI |
| Private rental | ONS Private Rental Statistics 2024 | Rent vs buy |
| Rental yields | Savills Residential Research 2024 | Rent vs buy |
| LAD boundaries | ONS Open Geography Portal May 2023 | Choropleth map |
| Postcode lookup | postcodes.io (OGL data) | Postcode search |

---

## Ethics

UREC2 form completed.
Evaluation form: no personally identifiable information collected.
All data stored locally. GDPR compliant.
AI tool use declared at AITS Level 2 (AI for Shaping).

---

## Dependencies

```bash
pip install -r requirements.txt
```

Core: requests, scikit-learn, numpy, pandas, matplotlib, seaborn, openpyxl
