"""One-time: store Parakeet weights as bf16 (half the file, half the load) since parakeet-mlx casts to bf16 anyway."""
import sys, mlx.core as mx
p = sys.argv[1]
w = mx.load(p); mx.save_safetensors(p, {k: v.astype(mx.bfloat16) if v.dtype == mx.float32 else v for k, v in w.items()})
print("ok", p)
