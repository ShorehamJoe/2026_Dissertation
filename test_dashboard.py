

import json
import os
import sys
import tempfile
import pytest

# Make package importable when running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


# ===========================================================================
# FIXTURES
# ===========================================================================

@pytest.fixture
def regional():
    from uk_housing_dashboard.data.datasets import REGIONAL
    return {k: dict(v) for k, v in REGIONAL.items()}


@pytest.fixture
def hpi():
    from uk_housing_dashboard.data.datasets import HPI
    return {k: dict(v) for k, v in HPI.items()}


@pytest.fixture
def cohorts():
    from uk_housing_dashboard.data.datasets import COHORTS
    return list(COHORTS)


# ===========================================================================
# CONFIG
# ===========================================================================

class TestConfig:
    def test_deposit_pct_in_range(self):
        from uk_housing_dashboard.config import DEFAULT_DEPOSIT_PCT
        assert 0 < DEFAULT_DEPOSIT_PCT < 1

    def test_mortgage_rate_reasonable(self):
        from uk_housing_dashboard.config import MORTGAGE_RATE
        assert 0.01 < MORTGAGE_RATE < 0.15

    def test_forecast_years_valid(self):
        from uk_housing_dashboard.config import FORECAST_YEARS
        assert len(FORECAST_YEARS) >= 1
        assert all(y > 2024 for y in FORECAST_YEARS)

    def test_sdlt_bands_cover_all_prices(self):
        from uk_housing_dashboard.config import SDLT_STANDARD_BANDS
        # First band starts at 0
        assert SDLT_STANDARD_BANDS[0][0] == 0
        # Each band's upper limit >= next band's lower limit
        for i in range(len(SDLT_STANDARD_BANDS) - 1):
            assert SDLT_STANDARD_BANDS[i][1] == SDLT_STANDARD_BANDS[i+1][0]

    def test_cv_folds_positive(self):
        from uk_housing_dashboard.config import CV_FOLDS
        assert CV_FOLDS >= 2

    def test_paths_are_strings(self):
        from uk_housing_dashboard.config import CACHE_DIR, OUTPUTS_DIR, EVAL_DIR
        assert isinstance(CACHE_DIR,   str)
        assert isinstance(OUTPUTS_DIR, str)
        assert isinstance(EVAL_DIR,    str)


# ===========================================================================
# DATASETS
# ===========================================================================

class TestDatasets:
    def test_all_twelve_regions_present(self, regional):
        expected = {
            "London", "South East", "East of England", "South West",
            "West Midlands", "East Midlands", "Yorkshire and The Humber",
            "North West", "North East", "Wales", "Scotland", "Northern Ireland",
        }
        assert set(regional.keys()) == expected

    def test_regional_income_positive(self, regional):
        for region, data in regional.items():
            assert data["income"] > 0, f"{region}: income must be positive"

    def test_regional_ratio_positive(self, regional):
        for region, data in regional.items():
            assert data["ratio"] > 0, f"{region}: ratio must be positive"

    def test_london_most_expensive(self, regional):
        assert regional["London"]["ratio"] > regional["North East"]["ratio"]
        assert regional["London"]["income"] > regional["North East"]["income"]

    def test_hpi_all_regions_have_four_types(self, hpi):
        types = {"Detached", "Semi-Detached", "Terraced", "Flat"}
        for region, prices in hpi.items():
            for t in types:
                assert t in prices, f"{region} missing property type: {t}"
                assert prices[t] > 0, f"{region}/{t} price must be positive"

    def test_hpi_detached_costlier_than_flat(self, hpi):
        for region, prices in hpi.items():
            assert prices["Detached"] > prices["Flat"], \
                f"{region}: Detached should cost more than Flat"

    def test_cohorts_four_in_order(self, cohorts):
        assert len(cohorts) == 4
        # Savings rate should increase with age (older saves more)
        rates = [c["rate"] for c in cohorts]
        assert rates == sorted(rates), "Cohort savings rates should increase with age"

    def test_cohort_rates_in_range(self, cohorts):
        for c in cohorts:
            assert 0 < c["rate"] < 1, f"{c['label']}: rate must be between 0 and 1"

    def test_cohort_colors_are_hex(self, cohorts):
        import re
        for c in cohorts:
            assert re.match(r"^#[0-9a-fA-F]{6}$", c["color"]), \
                f"{c['label']}: invalid hex color {c['color']}"

    def test_lad_data_nonempty(self):
        from uk_housing_dashboard.data.datasets import LAD_DATA
        assert len(LAD_DATA) >= 40

    def test_lad_kensington_most_expensive(self):
        from uk_housing_dashboard.data.datasets import LAD_DATA
        ratios = {k: v["ratio"] for k, v in LAD_DATA.items()}
        most_exp = max(ratios, key=ratios.get)
        assert "Kensington" in most_exp

    def test_lad_burnley_most_affordable(self):
        from uk_housing_dashboard.data.datasets import LAD_DATA
        ratios = {k: v["ratio"] for k, v in LAD_DATA.items()}
        cheapest = min(ratios, key=ratios.get)
        assert ratios[cheapest] < 4.5

    def test_cities_have_required_fields(self):
        from uk_housing_dashboard.data.datasets import CITIES
        required = {"name", "lat", "lng", "region", "pop"}
        for city in CITIES:
            assert required.issubset(city.keys()), f"{city.get('name')}: missing fields"

    def test_cities_lat_lng_valid(self):
        from uk_housing_dashboard.data.datasets import CITIES
        for city in CITIES:
            assert 49 < city["lat"] < 61, f"{city['name']}: lat out of UK range"
            assert -8 < city["lng"] <  2, f"{city['name']}: lng out of UK range"

    def test_hpi_trend_all_regions(self):
        from uk_housing_dashboard.data.datasets import HPI_TREND, REGIONAL
        for region in REGIONAL:
            assert region in HPI_TREND, f"Missing HPI trend for {region}"
            assert len(HPI_TREND[region]) == 10, f"{region}: trend must have 10 values"


# ===========================================================================
# CALCULATORS
# ===========================================================================

class TestCalculators:


    def test_sdlt_zero_under_250k_standard(self):

        from uk_housing_dashboard.utils.calculators import calc_sdlt
        total, _ = calc_sdlt(200_000, is_ftb=False)
        assert total == 0.0

    def test_sdlt_standard_300k(self):

        from uk_housing_dashboard.utils.calculators import calc_sdlt
        total, rows = calc_sdlt(300_000, is_ftb=False)
        assert total == 2_500.0
        assert len(rows) == 2

    def test_sdlt_standard_500k(self):

        from uk_housing_dashboard.utils.calculators import calc_sdlt
        total, _ = calc_sdlt(500_000, is_ftb=False)
        assert total == 12_500.0

    def test_sdlt_standard_1m(self):

        from uk_housing_dashboard.utils.calculators import calc_sdlt
        total, _ = calc_sdlt(1_000_000, is_ftb=False)
        assert total == 41_250.0

    def test_sdlt_ftb_zero_under_425k(self):

        from uk_housing_dashboard.utils.calculators import calc_sdlt
        total, _ = calc_sdlt(300_000, is_ftb=True)
        assert total == 0.0

    def test_sdlt_ftb_between_thresholds(self):

        from uk_housing_dashboard.utils.calculators import calc_sdlt
        total, _ = calc_sdlt(500_000, is_ftb=True)
        assert total == 3_750.0

    def test_sdlt_ftb_above_cap_uses_standard(self):

        from uk_housing_dashboard.utils.calculators import calc_sdlt
        total_ftb, _    = calc_sdlt(700_000, is_ftb=True)
        total_std, _    = calc_sdlt(700_000, is_ftb=False)
        assert total_ftb == total_std

    def test_sdlt_returns_rows_list(self):

        from uk_housing_dashboard.utils.calculators import calc_sdlt
        _, rows = calc_sdlt(500_000)
        assert isinstance(rows, list)
        assert all("band" in r and "rate" in r and "amount" in r for r in rows)

    def test_sdlt_rows_sum_to_total(self):

        from uk_housing_dashboard.utils.calculators import calc_sdlt
        total, rows = calc_sdlt(800_000)
        assert abs(sum(r["amount"] for r in rows) - total) < 0.01


# ===========================================================================
# CACHE
# ===========================================================================

class TestCache:
    def test_cache_dir_created(self):
        from uk_housing_dashboard.utils.cache import _CACHE
        assert os.path.isdir(_CACHE)

    def test_fetch_and_cache(self, tmp_path, monkeypatch):

        import uk_housing_dashboard.utils.cache as cache_mod
        monkeypatch.setattr(cache_mod, "_CACHE", str(tmp_path))

        dummy = b"hello world"
        monkeypatch.setattr(cache_mod, "_fetch", lambda url, timeout=30: dummy)

        result = cache_mod._load("test.txt", "http://example.com/test.txt", "test")
        assert result == dummy
        assert os.path.exists(os.path.join(str(tmp_path), "test.txt"))

    def test_cache_hit_skips_fetch(self, tmp_path, monkeypatch):

        import time
        import uk_housing_dashboard.utils.cache as cache_mod
        monkeypatch.setattr(cache_mod, "_CACHE", str(tmp_path))
        monkeypatch.setattr(cache_mod, "_TTL",   999 * 86400)  # very long TTL

        path = os.path.join(str(tmp_path), "cached.txt")
        with open(path, "wb") as f:
            f.write(b"cached content")

        fetch_called = []
        monkeypatch.setattr(cache_mod, "_fetch",
                            lambda url, timeout=30: fetch_called.append(1) or b"new")

        result = cache_mod._load("cached.txt", "http://example.com", "test")
        assert result == b"cached content"
        assert len(fetch_called) == 0


# ===========================================================================
# EVALUATION
# ===========================================================================

class TestEvaluation:
    def test_question_count(self):
        from uk_housing_dashboard.utils.evaluation import QUESTIONS
        assert len(QUESTIONS) >= 14

    def test_all_questions_have_required_fields(self):
        from uk_housing_dashboard.utils.evaluation import QUESTIONS
        for q in QUESTIONS:
            assert "id"   in q, f"Missing id in question: {q}"
            assert "text" in q, f"Missing text in question: {q}"
            assert "type" in q, f"Missing type in question: {q}"

    def test_radio_questions_have_options(self):
        from uk_housing_dashboard.utils.evaluation import QUESTIONS
        for q in QUESTIONS:
            if q["type"] == "radio":
                assert "options" in q and len(q["options"]) >= 2, \
                    f"Radio question {q['id']} needs at least 2 options"

    def test_scale_questions_have_anchors(self):
        from uk_housing_dashboard.utils.evaluation import QUESTIONS
        for q in QUESTIONS:
            if q["type"] == "scale":
                assert "anchors" in q and len(q["anchors"]) == 2, \
                    f"Scale question {q['id']} needs exactly 2 anchors"
                assert "scale"   in q and q["scale"] >= 3

    def test_save_response(self, tmp_path, monkeypatch):
        import uk_housing_dashboard.utils.evaluation as eval_mod
        monkeypatch.setattr(eval_mod, "EVAL_DIR",  str(tmp_path))
        monkeypatch.setattr(eval_mod, "EVAL_FILE",
                            os.path.join(str(tmp_path), "responses.json"))

        rid = eval_mod.save_response({"role": "Student", "useful_overall": "4"})
        assert rid == "R001"
        assert os.path.exists(os.path.join(str(tmp_path), "responses.json"))

    def test_save_multiple_responses(self, tmp_path, monkeypatch):
        import uk_housing_dashboard.utils.evaluation as eval_mod
        ef = os.path.join(str(tmp_path), "responses.json")
        monkeypatch.setattr(eval_mod, "EVAL_DIR",  str(tmp_path))
        monkeypatch.setattr(eval_mod, "EVAL_FILE", ef)

        eval_mod.save_response({"role": "Adviser"})
        eval_mod.save_response({"role": "Researcher"})
        with open(ef) as f:
            data = json.load(f)
        assert len(data) == 2
        assert data[1]["_id"] == "R002"

    def test_build_eval_form_html_contains_questions(self):
        from uk_housing_dashboard.utils.evaluation import build_eval_form_html, QUESTIONS
        html = build_eval_form_html()
        for q in QUESTIONS:
            assert q["id"] in html, f"Question {q['id']} missing from form HTML"

    def test_analyse_no_responses(self, tmp_path, monkeypatch):
        import uk_housing_dashboard.utils.evaluation as eval_mod
        monkeypatch.setattr(eval_mod, "EVAL_FILE",
                            os.path.join(str(tmp_path), "nonexistent.json"))
        result = eval_mod.analyse_responses()
        assert result == {}


# ===========================================================================
# ML MODEL (lightweight - no full training)
# ===========================================================================

class TestMLModel:
    def test_synthetic_dataset_shape(self):

        from uk_housing_dashboard.data.ml_model import _build_synthetic, FEATURES
        from uk_housing_dashboard.data.datasets import REGIONAL, HPI, HPI_TREND
        df, reg_enc, type_enc = _build_synthetic(
            {k: dict(v) for k, v in REGIONAL.items()},
            {k: dict(v) for k, v in HPI.items()},
            {k: list(v) for k, v in HPI_TREND.items()},
        )
        assert len(df) > 1000
        for f in FEATURES:
            assert f in df.columns, f"Missing feature: {f}"

    def test_feature_importance_keys(self):

        from uk_housing_dashboard.data.ml_model import _extract_importance, FEATURES
        try:
            from sklearn.ensemble import GradientBoostingRegressor
            import numpy as np
            X = np.random.rand(200, len(FEATURES))
            y = np.random.rand(200)
            m = GradientBoostingRegressor(n_estimators=10, random_state=42)
            m.fit(X, y)
            imp = _extract_importance(m, FEATURES)
            assert len(imp) == len(FEATURES)
            assert all(isinstance(v, float) for v in imp.values())
        except ImportError:
            pytest.skip("scikit-learn not installed")

    def test_bootstrap_ci_bounds(self):

        from uk_housing_dashboard.data.ml_model import _bootstrap_ci
        try:
            from sklearn.ensemble import GradientBoostingRegressor
            import numpy as np
            from uk_housing_dashboard.data.ml_model import FEATURES
            X = np.random.rand(200, len(FEATURES))
            y = np.log1p(np.random.rand(200) * 300000)
            m = GradientBoostingRegressor(n_estimators=10, random_state=42)
            m.fit(X, y)
            X_pred = np.random.rand(1, len(FEATURES))
            pred = float(np.expm1(m.predict(X_pred)[0]))
            low, high = _bootstrap_ci(X, y, X_pred, n=10)
            assert low <= high
            assert low > 0
            assert high > 0
        except ImportError:
            pytest.skip("scikit-learn not installed")


# ===========================================================================
# HTML BUILDER
# ===========================================================================

class TestHTMLBuilder:
    def test_build_returns_string(self):
        from uk_housing_dashboard.map.html_builder import build
        html = build("null")
        assert isinstance(html, str)
        assert len(html) > 1000

    def test_build_contains_required_elements(self):
        from uk_housing_dashboard.map.html_builder import build
        html = build("null")
        for element in ["<!DOCTYPE html>", "leaflet", "sel-region",
                        "sel-year", "sel-deposit", "eval-pane"]:
            assert element in html, f"Missing required element: {element}"

    def test_build_cp1252_safe(self):

        from uk_housing_dashboard.map.html_builder import build
        html = build("null")
        try:
            html.encode("cp1252")
        except UnicodeEncodeError as exc:
            pytest.fail(f"HTML contains non-cp1252 character: {exc}")

    def test_build_with_forecasts(self):

        from uk_housing_dashboard.map.html_builder import build
        forecasts = {"London": {"Semi-Detached": {"2025": {"pred": 700000, "low": 630000, "high": 770000}}}}
        html      = build("null", forecasts=forecasts, metrics={"r2_mean": 0.92})
        assert "ML_FORECASTS" in html
        assert "700000"       in html

    def test_build_with_eval_form(self):

        from uk_housing_dashboard.map.html_builder   import build
        from uk_housing_dashboard.utils.evaluation   import build_eval_form_html
        form = build_eval_form_html()
        html = build("null", eval_form_html=form)
        assert "eval-form" in html

    def test_data_badges_in_header(self):
        """Header should contain data source badges."""
        from uk_housing_dashboard.map.html_builder import build
        html = build("null", data_notes={"income": "ONS API (live)", "hpi": "embedded"})
        assert "data-badge" in html


# ===========================================================================
# LAND REGISTRY MODULE
# ===========================================================================

class TestLandRegistry:
    def test_postcode_to_region_london(self):
        from uk_housing_dashboard.data.land_registry import _postcode_to_region
        assert _postcode_to_region("SW1A 1AA") == "London"
        assert _postcode_to_region("EC1A 1BB") == "London"

    def test_postcode_to_region_manchester(self):
        from uk_housing_dashboard.data.land_registry import _postcode_to_region
        assert _postcode_to_region("M1 1AE") == "North West"

    def test_postcode_to_region_sheffield(self):
        from uk_housing_dashboard.data.land_registry import _postcode_to_region
        assert _postcode_to_region("S1 2HE") == "Yorkshire and The Humber"

    def test_postcode_to_region_belfast(self):
        from uk_housing_dashboard.data.land_registry import _postcode_to_region
        assert _postcode_to_region("BT1 1AA") == "Northern Ireland"

    def test_postcode_to_region_unknown(self):
        from uk_housing_dashboard.data.land_registry import _postcode_to_region
        assert _postcode_to_region("XX99 9XX") == ""
        assert _postcode_to_region("")           == ""
        assert _postcode_to_region(None)         == ""

    def test_clean_removes_outliers(self):

        import pandas as pd
        from uk_housing_dashboard.data.land_registry import _clean
        df = pd.DataFrame({
            "price":            [100_000, 200_000, 300_000, 1, 999_999_999],
            "date_of_transfer": ["2023-01-01"] * 5,
            "postcode":         ["SW1A 1AA", "SW1A 1AA", "SW1A 1AA", "SW1A 1AA", "SW1A 1AA"],
            "property_type":    ["D", "S", "T", "D", "D"],
        })
        result = _clean(df)
        # Extreme outlier (999M) and very low price (1) should be removed
        assert result["price"].max() < 999_999_999
        assert result["price"].min() > 1

    def test_clean_maps_property_types(self):

        import pandas as pd
        from uk_housing_dashboard.data.land_registry import _clean
        df = pd.DataFrame({
            "price":            [200_000, 300_000, 400_000, 250_000],
            "date_of_transfer": ["2023-06-01"] * 4,
            "postcode":         ["SW1A 1AA", "M1 1AE", "LS1 1AA", "B1 1AA"],
            "property_type":    ["D", "S", "T", "F"],
        })
        result = _clean(df)
        assert set(result["property_type"].unique()).issubset(
            {"Detached", "Semi-Detached", "Terraced", "Flat"}
        )


# ===========================================================================
# INTEGRATION TEST
# ===========================================================================

class TestIntegration:
    def test_full_pipeline_no_network(self, monkeypatch):

        import uk_housing_dashboard.utils.cache as cache_mod
        import uk_housing_dashboard.data.live_data as live_mod
        import uk_housing_dashboard.data.land_registry as lr_mod

        # Simulate network failure
        monkeypatch.setattr(cache_mod, "_fetch",
                            lambda *a, **kw: (_ for _ in ()).throw(ConnectionError("offline")))
        monkeypatch.setattr(lr_mod, "load_real_data", lambda: None)

        from uk_housing_dashboard.data.live_data  import load_live_data
        from uk_housing_dashboard.data.ml_model   import load_predictions
        from uk_housing_dashboard.map.html_builder import build

        regional, hpi, hpi_trend, hpi_years, notes = load_live_data()
        assert len(regional) == 12
        assert "embedded" in notes.get("income", "").lower() or \
               "embedded" in notes.get("hpi",    "").lower()

        forecasts, metrics = load_predictions(regional, hpi, hpi_trend)
        assert len(forecasts) > 0

        html = build("null", regional=regional, hpi=hpi,
                     hpi_trend=hpi_trend, hpi_years=hpi_years,
                     forecasts=forecasts, metrics=metrics)
        assert len(html) > 5000
        html.encode("cp1252")   # must be Windows-safe
