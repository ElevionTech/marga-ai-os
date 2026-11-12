"""Offline checks for MARGA's isolated and fail-closed Compose definitions."""
from _paths import ROOT  # noqa: E402
import re
import sys

try:
    import yaml
except ImportError:
    print("BLOCKED: PyYAML is unavailable")
    raise SystemExit(2)

fails = []


def check(name, condition):
    print(("ok   " if condition else "FAIL ") + name)
    if not condition:
        fails.append(name)


def compose(name):
    return yaml.safe_load((ROOT / name).read_text(encoding="utf-8"))


for name in ("docker-compose.yml", "docker-compose.build.yml"):
    doc = compose(name)
    service = doc["services"]["marga"]
    check(f"{name}: builds the MARGA source", service.get("build", {}).get("context") == ".")
    check(f"{name}: uses local MARGA image without pull", service.get("image") == "marga-ai-os:local"
          and service.get("pull_policy") == "build")
    check(f"{name}: local loopback-only publish", service.get("ports") == ["127.0.0.1:${MARGA_HOST_PORT:-7777}:7777"])
    check(f"{name}: requires owner bootstrap token", "MARGA_SETUP_TOKEN" in service.get("environment", {}).get("MARGA_SETUP_TOKEN", ""))
    check(f"{name}: independent persistent state and brain volumes",
          set(doc["volumes"]) == {"marga-state", "marga-brains", "marga-claude-auth", "marga-codex-auth"})
    check(f"{name}: no Watchtower/update sidecar", "watchtower" not in doc["services"])

host = compose("docker-compose.hostinger.yml")
production = host["services"]["marga"]
check("public profile is explicit", production.get("profiles") == ["production"])
check("production image has no Jarvis/default fallback", "${MARGA_IMAGE:?" in production.get("image", ""))
check("production requires owner bootstrap token", "${MARGA_SETUP_TOKEN:?" in production["environment"]["MARGA_SETUP_TOKEN"])
check("production has no Watchtower or auto-update sidecar", "watchtower" not in host["services"])
check("production state and brain volumes are MARGA-specific",
      set(host["volumes"]) == {"marga-state", "marga-brains", "marga-claude-auth", "marga-codex-auth"})

for name in ("docker-compose.yml", "docker-compose.build.yml", "docker-compose.hostinger.yml"):
    text = (ROOT / name).read_text(encoding="utf-8").lower()
    check(f"{name}: no inherited Jarvis image or predictable Watchtower token",
          "ghcr.io/blogminhquy/javis-os" not in text and "javis-update" not in text
          and "watchtower_token" not in text)

dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
check("Docker image is branded MARGA", 'org.opencontainers.image.title="MARGA AI OS"' in dockerfile)
check("Docker image source stamp uses MARGA namespace", "ARG MARGA_IMAGE_SOURCE" in dockerfile)
check("Docker defaults persist MARGA state and isolated brains",
      "MARGA_STATE_DIR=/data/state" in dockerfile and "BRAINS_DIR=/brains" in dockerfile)

updater = (ROOT / "server" / "updater.py").read_text(encoding="utf-8")
check("manual update shell entrypoint does not run git pull", "git pull" not in (ROOT / "update.sh").read_text(encoding="utf-8"))
check("updater source cannot fall back to Jarvis", "blogminhquy/javis-os.git" not in updater)
check("update shell reports disabled state", "MARGA self-update is unavailable" in (ROOT / "update.sh").read_text(encoding="utf-8"))

if fails:
    print("FAILED:", "; ".join(fails))
    sys.exit(1)
print("OK - deployment configuration is independent and fail-closed")
