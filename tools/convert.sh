#!/usr/bin/env bash
# One-time, on an Apple-silicon Mac. Converts every model into models/ so the app never downloads at run time.
# Needs: uv, git, ~6 GB free disk, internet. Deletes its own throwaway env at the end.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p models
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
git clone -q --depth 1 https://github.com/ml-explore/mlx-examples "$TMP/mlx-examples"
uv venv -q --python 3.12 "$TMP/venv"
VENV_PY="$TMP/venv/bin/python"
uv pip install -q --python "$VENV_PY" -r "$TMP/mlx-examples/whisper/mlx_whisper/requirements.txt" numba torch transformers ctranslate2 "huggingface_hub[cli]" mlx numpy tiktoken safetensors more-itertools
conv() { "$VENV_PY" "$TMP/mlx-examples/whisper/convert.py" --torch-name-or-path "$1" --mlx-path "$2" -q --q-bits "$3"; [ -f "$2/model.safetensors" ] && mv "$2/model.safetensors" "$2/weights.safetensors"; }  # mlx-whisper 0.4.3 loads weights.safetensors
[ -f models/apex-mlx-q8/config.json ] || conv Oriserve/Whisper-Hindi2Hinglish-Apex models/apex-mlx-q8 8
[ -f models/tiny-mlx/config.json ]    || conv openai/whisper-tiny models/tiny-mlx 8
ct2() { "$TMP/venv/bin/ct2-transformers-converter" --model "$1" --output_dir "$2" --quantization int8 --copy_files tokenizer.json preprocessor_config.json --force; }
[ -f models/apex-ct2-int8/model.bin ] || ct2 Oriserve/Whisper-Hindi2Hinglish-Apex models/apex-ct2-int8
[ -f models/tiny-ct2/model.bin ]      || ct2 openai/whisper-tiny models/tiny-ct2
snap() { "$VENV_PY" -c "from huggingface_hub import snapshot_download as s; s('$1', local_dir='$2', allow_patterns=$3)"; }
[ -f models/parakeet-v2-mlx/model.safetensors ] || snap mlx-community/parakeet-tdt-0.6b-v2 models/parakeet-v2-mlx "['*.json','*.safetensors']"
ls models/parakeet-v2-onnx/*.onnx >/dev/null 2>&1 || snap istupakov/parakeet-tdt-0.6b-v2-onnx models/parakeet-v2-onnx "['*']"
# GGML files for the Windows CPU gate (H6, H7): Apex q8, Swift, tiny
[ -d models/ggml ] || { snap gouravg8/gtm-hi2hing-ggml models/ggml "['*.bin','*.gguf']"; snap rohitag13/whisper-hindi2hinglish-swift-GGUF models/ggml "['*.bin','*.gguf']"; snap ggerganov/whisper.cpp models/ggml "['ggml-tiny.bin']"; }
# fixture clips shipped with the Apex repo (Hinglish samples); owner's own clips are added by hand
[ -d tests/fixtures/apex ] || snap Oriserve/Whisper-Hindi2Hinglish-Apex tests/fixtures/apex "['audios/*']"
du -sh models/* tests/fixtures/apex
