"""MARGA update state remains readable while self-updates are disabled by default."""
from _paths import ROOT, SERVER  # noqa: E402,F401
import asyncio
import json
import os
import tempfile

state = tempfile.mkdtemp(prefix="marga-update-test-")
os.environ["MARGA_STATE_DIR"] = state
os.environ["JAVIS_STATE_DIR"] = state
os.environ.pop("MARGA_UPDATE_REPOSITORY", None)

import update_state as us  # noqa: E402
import main  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402

fails = []


def check(name, condition):
    print(("ok   " if condition else "FAIL ") + name)
    if not condition:
        fails.append(name)


check("version comparison remains available", us.ver_newer("1.1.0", "1.0.0") is True)
us.write_state({"phase": "installing", "old_version": "1.0.0"})
check("update status state persists", us.read_state().get("phase") == "installing")
check("health failure still requests rollback", us.update_outcome(False, "1.1.0", "1.0.0", "1.1.0") == "need_rollback")

latest, error = asyncio.run(main._latest_remote_version("1.0.0"))
check("unconfigured version check is local and reports unavailable", latest == "1.0.0" and "unavailable" in error.lower())
response = asyncio.run(main.do_update())
body = json.loads(response.body) if isinstance(response, JSONResponse) else {}
check("update endpoint refuses while no MARGA source is configured", isinstance(response, JSONResponse)
      and response.status_code == 503 and "MARGA" in body.get("error", ""))
check("refusal does not change the state file", us.read_state().get("phase") == "installing")

us.write_state({"phase": "idle", "result": "unavailable"})
status = main.update_status()
check("update status endpoint remains available", status["state"].get("result") == "unavailable")

if fails:
    raise SystemExit("FAILED: " + ", ".join(fails))
print("OK - MARGA update behavior is fail-closed.")
