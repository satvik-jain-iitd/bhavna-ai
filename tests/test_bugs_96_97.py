"""#96 token cap by audio length; #97 clipboard restore waits longer than a slow paste."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "macos"))
import dictate as d


def test_96_token_cap_grows_with_audio_and_has_a_floor():
    assert d.sample_len(0.8) == 24 + 8 * 1          # at least one second counted
    assert d.sample_len(5.0) == 24 + 40
    assert d.sample_len(30.0) == 24 + 240
    assert d.sample_len(60.0) <= 440                # never above whisper's text context


def test_97_restore_delay_is_longer_than_a_slow_paste():
    assert d.RESTORE_S >= 1.0
