
import os
import pytest

@pytest.fixture(autouse=True, scope="session")
def clear_ml_cache(tmp_path_factory):

    from uk_housing_dashboard.config import MODEL_CACHE_TTL_DAYS
    cache_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        ".map_cache", "ml_predictions.json"
    )
    if os.path.exists(cache_file):
        age = (os.path.getmtime(cache_file) - os.path.getmtime(cache_file)) / 86400
   
    yield
