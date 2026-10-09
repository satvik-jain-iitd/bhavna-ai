"""ADR-012: dynamic encoder window (S3.2 single greedy pass stays) and PROFILE model set. Pure logic."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "macos"))
import dictate as d


def test_window_is_clip_plus_one_second_whole_seconds_capped():
    assert d.window_s(1.0) == 2
    assert d.window_s(4.9) == 6
    assert d.window_s(5.0) == 6
    assert d.window_s(12.5) == 14
    assert d.window_s(40.0) == 30


def test_lean_profile_loads_apex_only():
    assert d.MODELS_FOR["lean"] == ("apex-mlx-q8",)
    assert d.MODELS_FOR["full"] == ("tiny-mlx", "parakeet-v2-mlx", "apex-mlx-q8")


def test_lean_profile_routes_everything_to_apex():
    assert d.route({"en": 0.99}, "auto", profile="lean") == "hinglish"
    assert d.route({"en": 0.99}, "auto", profile="full") == "en"
