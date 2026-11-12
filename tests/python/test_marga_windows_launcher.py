"""Static safety checks for the MARGA Windows launcher."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
launcher = (ROOT / "start-marga.ps1").read_text(encoding="utf-8")
compat = (ROOT / "start-javis.vbs").read_text(encoding="utf-8")
autostart = (ROOT / "javis-autostart.ps1").read_text(encoding="utf-8")

checks = {
    "stable MARGA state root": '".marga\\state"' in launcher,
    "MARGA state variable is set": "$env:MARGA_STATE_DIR = $State" in launcher,
    "legacy state variable is synchronized": "$env:JAVIS_STATE_DIR = $State" in launcher,
    "loopback binding": "--host 127.0.0.1" in launcher,
    "MARGA port default": "$Port = if ($env:MARGA_PORT)" in launcher and "28779" in launcher,
    "explicit plugin disable remains authoritative": "JAVIS_ENABLE_USER_PLUGINS" in launcher
    and "JAVIS_ENABLE_VAULT_PLUGINS" in launcher,
    "legacy VBS wrapper delegates to MARGA": "start-marga.ps1" in compat,
    "Windows autostart delegates to MARGA": "start-marga.ps1" in autostart,
}

failed = [name for name, ok in checks.items() if not ok]
for name, ok in checks.items():
    print(("PASS: " if ok else "FAIL: ") + name)
if failed:
    raise SystemExit(1)
