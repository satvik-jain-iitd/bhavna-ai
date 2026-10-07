#!/usr/bin/env bash
# Installs the `bhavna` command (macOS). Run once: tools/install-shortcut.sh
set -e
mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/bhavna" <<SH
#!/usr/bin/env bash
exec uv run --python 3.12 --project "$(cd "$(dirname "$0")/.." && pwd)/macos" "$(cd "$(dirname "$0")/.." && pwd)/macos/dictate.py" "\$@"
SH
chmod +x "$HOME/.local/bin/bhavna"
echo "installed: bhavna  (make sure ~/.local/bin is on your PATH)"
