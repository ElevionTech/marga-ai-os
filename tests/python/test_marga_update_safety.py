"""The inherited updater has no implicit Jarvis source and makes no fetch without configuration."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))

_old_repo = os.environ.pop("MARGA_UPDATE_REPOSITORY", None)
_old_branch = os.environ.pop("MARGA_UPDATE_BRANCH", None)
import updater  # noqa: E402

try:
    assert updater.release_source() == ("", "")

    # A configured Jarvis URL must be rejected and cannot reach git fetch.
    os.environ["MARGA_UPDATE_REPOSITORY"] = "https://github.com/blogminhquy/javis-os"
    assert updater.release_source() == ("", "")
    calls = []
    updater.run = lambda args: calls.append(args)
    result, _safe = updater.merge_release()
    assert result.returncode != 0
    assert calls == []

    # Explicit MARGA configuration is the only way to produce a release source.
    os.environ["MARGA_UPDATE_REPOSITORY"] = "https://github.com/example/marga-ai-os.git"
    os.environ["MARGA_UPDATE_BRANCH"] = "main"
    assert updater.release_source() == ("https://github.com/example/marga-ai-os.git", "main")
finally:
    if _old_repo is None:
        os.environ.pop("MARGA_UPDATE_REPOSITORY", None)
    else:
        os.environ["MARGA_UPDATE_REPOSITORY"] = _old_repo
    if _old_branch is None:
        os.environ.pop("MARGA_UPDATE_BRANCH", None)
    else:
        os.environ["MARGA_UPDATE_BRANCH"] = _old_branch

print("MARGA updater source safety passed.")
