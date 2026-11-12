"""Default runtime and memory paths stay inside MARGA, independent of Jarvis env defaults."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))
os.environ.pop("MARGA_STATE_DIR", None)
os.environ.pop("JAVIS_STATE_DIR", None)
os.environ.pop("BRAINS_DIR", None)
os.environ.pop("BRAIN_PATH", None)
os.environ.pop("OBSIDIAN_VAULT_PATH", None)
os.environ.pop("SOURCES_PATH", None)

import config  # noqa: E402
import main  # noqa: E402

expected = ROOT / ".marga"
assert config.STATE_DIR == expected / "state"
assert Path(main.BRAINS_DIR) == expected / "brains"
assert Path(main.BRAIN_PATH) == expected / "brain"
assert Path(main.OBSIDIAN_VAULT_PATH) == expected / "vault"
assert Path(main.SOURCES_PATH) == expected / "brain" / "01 - Sources"
assert ROOT not in config.STATE_DIR.parents or config.STATE_DIR != ROOT

print("MARGA state isolation defaults passed.")
