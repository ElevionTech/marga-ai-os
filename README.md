# MARGA AI OS

MARGA AI OS is a self-hosted AI agent operating system built around a FastAPI backend, a browser dashboard, persistent conversations, file-based memory, agents, workflows, MCP integrations, and pluggable model providers.

The project is currently in active development. The local deployment and core offline tests are usable, but provider integrations, Docker deployment, browser coverage, and production hardening still require environment-specific validation.

## Features

- FastAPI and Uvicorn backend with a plain HTML, CSS, and JavaScript dashboard.
- AI provider routing for API, OAuth, and local CLI providers.
- Streaming chat, session persistence, agents, teams, tasks, workflows, and background execution.
- Markdown-based brains with SQLite session and memory indexes.
- MCP and plugin integrations with permission checks and protected-path handling.
- English-only built-in interface with MARGA violet branding.
- Local Docker definitions with isolated MARGA state and loopback-only development binding.

## Technology stack

- Python 3.12
- FastAPI and Uvicorn
- SQLite and Markdown-based persistence
- HTML, CSS, and JavaScript dashboard
- Docker Compose for deployment options
- Python and JavaScript test suites

## Windows development setup

Use an independently installed Python 3.12 interpreter. Do not reuse another project's virtual environment.

```powershell
cd C:\Users\geral\marga-ai-os
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The repository excludes `.venv`, `.marga`, databases, logs, credentials, caches, and other local runtime state through `.gitignore`.

## Start locally

The verified local startup command is:

```powershell
cd C:\Users\geral\marga-ai-os
$env:PYTHONPATH = (Join-Path (Get-Location) "server")
.\.venv\Scripts\python.exe -m uvicorn main:app --app-dir server --host 127.0.0.1 --port 28779
```

Open <http://127.0.0.1:28779>. Fresh-state initialization can take approximately 20 seconds. Local runtime data is written below `.marga` unless deployment variables explicitly provide another MARGA-owned location.

Do not bind a fresh administrator setup to a public interface. Configure the owner-controlled setup token before using a reverse proxy or public deployment.

## AI providers

Provider setup is available from the authenticated Models page. Options include OpenAI API, OpenAI OAuth, Claude Code CLI, Gemini API, Ollama Local, and other compatible providers.

ChatGPT subscription access and API billing are separate products. OpenAI API usage may incur charges. Claude Code and other CLI providers use their own local authentication and plan terms. Ollama Local keeps inference on the configured machine but requires local hardware and a reachable Ollama endpoint.

No provider credentials are included in this repository. The first live provider conversation should use an isolated session with tools and external MCP actions disabled, and should be approved separately before sending data outside the machine.

## Testing

Examples using the MARGA interpreter:

```powershell
.\.venv\Scripts\python.exe -m compileall -q server
node tests/js/test_i18n.mjs
.\.venv\Scripts\python.exe -m pytest -q
git diff --check
```

Some platform-specific and legacy tests require separate Linux, Bash, Docker, browser, or provider environments. A passing offline test does not prove live provider or production deployment readiness.

## Security and privacy

- Never commit `.env` files, API keys, tokens, authentication state, private keys, databases, logs, conversations, or brain data.
- Keep `.marga` and deployment volumes private and separate from any other installation.
- Use loopback binding for local development.
- Review tool permission modes before connecting MCP servers or enabling plugins.
- Plugins execute inside the application process and are trusted code, not an operating-system sandbox.
- The inherited Jarvis updater remains disabled until an approved MARGA update source is configured.

## License and attribution

MARGA AI OS retains the source project's MIT license and required third-party attribution notices. Historical attribution and compatibility identifiers are preserved where required.
