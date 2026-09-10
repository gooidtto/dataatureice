import importlib.util
from pathlib import Path
ROOT=Path(__file__).parents[1]
spec=importlib.util.spec_from_file_location('phone_search',ROOT/'phone_search.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
def test_num_rejects_range_or_slash_price():
    assert mod.num('12/15') is None
    assert mod.num('/') is None
    assert mod.num('12.5') == 12.5
def test_key_normalizes_model_spelling():
    assert mod.key('iPhone 6-SP') == mod.key('iphone6sp')
