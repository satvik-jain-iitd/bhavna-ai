"""E4: router threshold (S4.1) and pinned modes / key map (S4.3). Pure logic."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "macos"))
import dictate as d


def test_s4_1_clear_english_goes_to_parakeet():
    assert d.route({"en": 0.93, "hi": 0.03}, "auto") == "en"


def test_s4_1_hinglish_goes_to_apex():
    assert d.route({"en": 0.55, "hi": 0.40}, "auto") == "hinglish"


def test_s4_1_boundary_is_english():
    assert d.route({"en": 0.80}, "auto") == "en"


def test_s4_1_unknown_language_goes_to_apex():
    assert d.route({"ur": 0.9}, "auto") == "hinglish"


def test_s4_3_pinned_mode_skips_lid():
    assert d.route(None, "hinglish") == "hinglish"
    assert d.route(None, "en") == "en"


def test_s4_3_two_key_layout_is_one_dict_entry():
    keys = {"alt_r": "en", "cmd_r": "hinglish"}
    assert d.route(None, keys["cmd_r"]) == "hinglish"
