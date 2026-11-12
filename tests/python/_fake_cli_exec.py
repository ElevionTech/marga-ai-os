"""Run test-only Python CLI fixtures through Windows' Python interpreter.

Production CLIs are native executables. The fixtures in these tests are Python
scripts without executable wrappers, which POSIX can launch via their shebang
but Windows cannot. Only registered fake paths are rewritten.
"""
from __future__ import annotations

import os
import subprocess
import sys
import asyncio
from pathlib import Path


_FAKE_CLI_PATHS: set[str] = set()
_ORIGINAL_POPEN = subprocess.Popen
_ORIGINAL_ASYNC_EXEC = asyncio.create_subprocess_exec


def register_fake_cli(path: str | Path) -> str:
    value = str(Path(path).resolve())
    _FAKE_CLI_PATHS.add(os.path.normcase(value))
    return value


def _windows_command(command):
    if not isinstance(command, (list, tuple)) or not command:
        return command
    first = os.path.normcase(str(Path(command[0]).resolve()))
    if first in _FAKE_CLI_PATHS:
        return [sys.executable, str(Path(command[0]).resolve()), *command[1:]]
    return command


def _fixture_popen(args, *positional, **kwargs):
    # The adapter keys off the actual host platform, not os.name, which some
    # tests temporarily override to exercise Windows-specific command options.
    if sys.platform == "win32":
        args = _windows_command(args)
    return _ORIGINAL_POPEN(args, *positional, **kwargs)


async def _fixture_async_exec(program, *args, **kwargs):
    if sys.platform == "win32":
        command = _windows_command([program, *args])
        program, *args = command
    return await _ORIGINAL_ASYNC_EXEC(program, *args, **kwargs)


if sys.platform == "win32":
    subprocess.Popen = _fixture_popen
    asyncio.create_subprocess_exec = _fixture_async_exec
