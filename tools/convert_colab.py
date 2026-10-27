"""Convert Oriserve Hindi2Hinglish models to MLX q8 on a Colab VM, not on the Mac.
Run: colab run --keep --timeout 2400 tools/convert_colab.py swift prime
Then: colab download /content/out/<folder>.zip models/<folder>.zip ; unzip into models/. <folder> is swift-mlx or prime-mlx-q8 (DIRS below).
Same recipe as tools/convert.sh (mlx-examples whisper/convert.py, q8, weights.safetensors).
"""
import os, subprocess, sys

IDS = {"swift": "Oriserve/Whisper-Hindi2Hinglish-Swift", "prime": "Oriserve/Whisper-Hindi2Hinglish-Prime"}
DIRS = {"swift": "swift-mlx", "prime": "prime-mlx-q8"}


def sh(cmd):
    print("+", cmd, flush=True)
    subprocess.run(cmd, shell=True, check=True)


sh("pip install -q 'mlx[cpu]' numba torch transformers tiktoken safetensors more-itertools huggingface_hub")
MLX_EXAMPLES_SHA = "796f5b53cab69a3d48a44233ce21aae889e94a08"   # main on 2026-04-06; the recipe was tested at this commit. Move it on purpose, then re-run T2.4.
sh("git clone -q https://github.com/ml-explore/mlx-examples /content/mlx-examples || true")
sh(f"git -C /content/mlx-examples checkout -q {MLX_EXAMPLES_SHA}")
sh("pip install -q -r /content/mlx-examples/whisper/mlx_whisper/requirements.txt")
os.makedirs("/content/out", exist_ok=True)
for name in sys.argv[1:] or IDS:
    out = f"/content/out/{DIRS[name]}"
    src = IDS[name]
    from huggingface_hub import snapshot_download
    local = snapshot_download(src, ignore_patterns=["audios/*"])
    if os.path.exists(f"{local}/model.safetensors.index.json"):  # convert.py reads one model.safetensors, Prime is sharded
        from transformers import WhisperForConditionalGeneration
        src = f"/content/{name}-hf"
        sh(f"rm -rf {src} && cp -rL {local} {src} && rm -f {src}/model-*.safetensors {src}/model.safetensors.index.json")
        WhisperForConditionalGeneration.from_pretrained(local).save_pretrained(src, max_shard_size="20GB")
    sh(f"python /content/mlx-examples/whisper/convert.py --torch-name-or-path {src} --mlx-path {out} -q --q-bits 8")
    if os.path.exists(f"{out}/model.safetensors"):  # mlx-whisper 0.4.3 loads weights.safetensors
        os.rename(f"{out}/model.safetensors", f"{out}/weights.safetensors")
    sh(f"cd /content/out && zip -qr {DIRS[name]}.zip {DIRS[name]} && du -sh {DIRS[name]}.zip")
