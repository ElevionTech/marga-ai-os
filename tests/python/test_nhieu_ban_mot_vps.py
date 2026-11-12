"""MARGA deployments can use distinct Compose projects without sharing local state."""
from _paths import ROOT  # noqa: E402
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


base = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
build = (ROOT / "docker-compose.build.yml").read_text(encoding="utf-8")
base_doc = yaml.safe_load(base)
multi = yaml.safe_load((ROOT / "docker-compose.multi.yml").read_text(encoding="utf-8"))
check("default container is independently named for MARGA", "${MARGA_NAME:-marga-ai-os}" in base)
check("container identity can be customized per instance", "${MARGA_NAME:-marga-ai-os}" in build)
check("host port is configurable and loopback-bound", '127.0.0.1:${MARGA_HOST_PORT:-7777}:7777' in base)
check("each instance has project-scoped MARGA state and brain volumes",
      all(name in base for name in ("marga-state:/data", "marga-brains:/brains"))
      and all(not (isinstance(spec, dict) and spec.get("name"))
              for spec in base_doc.get("volumes", {}).values()))
check("multi-instance overlay targets the MARGA service",
      "marga" in multi.get("services", {}) and "javis" not in multi.get("services", {}))
check("shared proxy network uses MARGA identity", "marga-web" in multi.get("networks", {}))

if fails:
    raise SystemExit("FAILED: " + "; ".join(fails))
print("OK - MARGA instance isolation checks passed")
