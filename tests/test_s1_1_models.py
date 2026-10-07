"""S1.1: convert.sh produces local model folders. Slow: needs the converted weights on disk."""
from pathlib import Path
import pytest

M = Path(__file__).resolve().parents[1] / "models"
slow = pytest.mark.skipif(not M.exists(), reason="models/ not converted yet")


@slow
def test_s1_1_apex_mlx_q8_and_ct2_int8_exist():
    assert (M / "apex-mlx-q8" / "weights.npz").exists() or (M / "apex-mlx-q8" / "weights.safetensors").exists()
    assert (M / "apex-mlx-q8" / "config.json").exists()
    assert (M / "apex-ct2-int8" / "model.bin").exists()
    assert (M / "apex-ct2-int8" / "tokenizer.json").exists()


@slow
def test_s1_1_tiny_and_parakeet_exist():
    assert (M / "tiny-mlx" / "config.json").exists()
    assert (M / "tiny-ct2" / "model.bin").exists()
    assert (M / "parakeet-v2-mlx" / "model.safetensors").exists()
    assert any((M / "parakeet-v2-onnx").glob("*.onnx"))
