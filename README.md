# Empório da Música

A local instrument catalogue with a store assistant, built for Artefact's AI Engineer challenge. The prototype combines a clickable collection, a side chat, SQLite-backed tools and an OpenAI-compatible model connection. It runs on your computer without rented hosting.

![The working catalogue and assistant interface](docs/preview.png)

The catalogue, filters, product details, discount calculations, policy lookup, order demonstration check and Markdown conversation export work without an API key. In that mode the interface clearly says Catalogue preview. It uses a small deterministic router and is not an LLM. To interpret free-form messages, connect a tool-capable model in the settings dialog.

The application was checked with Python 3.12 under Ubuntu WSL and Python 3.13 under Windows. Run the following commands from the repository root in Ubuntu or the VS Code WSL terminal.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run.py
```

Open `http://localhost:8765` in your browser. Stop the server with Ctrl+C. If the environment is already installed, only the last command is needed. On this workstation, `start-wsl.cmd` also launches the prepared Ubuntu environment from Windows.

For a separate Windows environment, use the following PowerShell commands. Keep the Windows and WSL environments separate.

```powershell
python -m venv .venv-win
.\.venv-win\Scripts\python.exe -m pip install -r requirements.txt
.\.venv-win\Scripts\python.exe run.py
```

The included `start-windows.cmd` launches an existing Windows environment. Both launchers use the same project files. The generated SQLite databases live in the ignored `.runtime` directory and are rebuilt from the original CSV files at startup. Run one web instance at a time.

Choose Connect a model and enter the API base URL, model ID and key if required. The endpoint must support Chat Completions with function tools. Presets cover common local addresses and OpenAI, but they do not guarantee compatibility. Load models queries the configured endpoint, and manual model entry remains available. A successful model list does not verify tool calling. Qwen3.6-35B-A3B is the reference candidate. A local abliterated Q8_0 variant has passed a two-turn smoke test with a greeting and a selected-product PIX query. Broader model evaluation remains open.

The endpoint address is resolved from Python, not from your browser. A Windows-hosted model service may require a Windows host address when the application runs in WSL. API keys are kept only in the current server-side browser session, never returned to the interface or written to disk. Changing the endpoint without supplying a new key clears the old key. Restarting the server or two hours of inactivity discards the session.

FastAPI serves the HTML, CSS and JavaScript interface without a frontend build step. SQLite handles structured catalogue and order queries. Python validates tool parameters and calculates prices in integer cents with decimal rounding. The model chooses tools, while product cards and factual responses are rendered from tool results. An unsupported final answer without evidence falls back to a clarification instead of displaying unverified model claims. This conservative first version trades flexible phrasing for predictable facts.

The browser and agent share `search_products`, `get_product`, `lookup_policy`, `get_order` and `navigate_catalog`. The chat menu exposes their descriptions and input schemas. The current category, selection, filters and visible product IDs accompany each message. Explicit references take precedence over navigation context. The agent can request catalogue navigation through semantic actions without pixel-based browser automation.

The official MCP Python SDK provides a thin stdio adapter for the three public read tools. Run it from the prepared environment with the following command.

```bash
.venv/bin/python run_mcp.py
```

This command waits for an MCP client on standard input and output, so it does not open a webpage. Configure your MCP host with absolute paths to the environment's Python executable and `run_mcp.py`. The adapter deliberately excludes private orders and browser navigation because it does not share the browser's verified session. It uses the same tool implementations as the web app and never prints ordinary application output into the protocol stream.

The policy tool retrieves complete relevant pages from the supplied PDF and returns their source references with reviewed English summaries. Chat source links open the original manual. This is a small page-level retrieval approach without embeddings or a vector database. It is intentionally limited to named policy topics rather than a general document search engine.

Discounts never stack. The system chooses the highest active product promotion or, when applicable, the 5% PIX discount. PIX eligibility means that the store receives the full amount immediately through PIX, even if the customer's bank finances that payment separately. This comparison and financing interpretation are documented project decisions where the manual is not explicit. Mixed payments do not automatically receive the full PIX discount.

The order dialog checks an order number and matching email against the supplied fictional data. That permits access to that order in the same browser session. It is a demonstration knowledge check, not production authentication. No purchase, refund, complaint registration, real payment or live carrier lookup is performed.

The source data is a snapshot. Estimated delivery dates do not establish actual receipt, and manufacturer warranty terms are not inferred. Conflicting contact information, the undefined shipping rule at exactly R$500 and incomplete return facts are handled as limitations. The app binds only to loopback, rejects unrelated hosts and cross-site API requests, and should not be exposed as a public multi-user service.

Install the development dependencies to run the checks.

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q -o cache_dir=/tmp/artefact-musicstore-pytest
```

For Windows, run the same suite with the Windows interpreter and separate test directories.

```powershell
.\.venv-win\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv-win\Scripts\python.exe -m pytest -q --basetemp .runtime/test-temp-windows-user -o cache_dir=.runtime/pytest-windows-user
```

All 32 test cases passed under WSL. Windows checks include the strict-template regression cases. The tests exercise real SQLite joins, availability and budget filtering, discount boundaries, order scope, independent sessions, provider errors, malformed or repeating tool calls, controlled factual output and a real MCP subprocess handshake. Model responses in automated tests are simulated with an HTTP transport and do not establish Qwen compatibility. Package snapshots are recorded separately in `requirements-lock-windows.txt` and `requirements-lock-wsl.txt` because Windows includes platform-specific dependencies.

Optional browser checks are in `scripts/check_browser.py`. They require the development dependencies, a running server on port 8765 and an installed Chromium-family browser. The script uses an installed Edge, Brave, Chromium or Chrome when found, otherwise Playwright's separately installed browser. It checks catalogue browsing, filtering, product context, settings, tool documentation, failed order verification and mobile layout.

Three recorded conversations under `examples/` were produced through actual HTTP requests to the running preview. They are explicitly labelled as deterministic preview evidence and must not be presented as real LLM evaluation. The chat can export new conversations as Markdown. After selecting and testing a real model, record the final three to five submission conversations and document the model configuration.

I used Codex to inspect the assignment and data, discuss the design, implement the prototype and tests, and prepare documentation following my questions and writing references. The first real inference smoke test used a local Qwen3.6-35B-A3B-abliterated Q8_0 endpoint without a key. It verified a greeting and a tool-backed product price, not the full submission scenarios. The next work is to evaluate the configured model, improve follow-up dialogue, strengthen identity verification if the app moves beyond a local demonstration, and capture final model-backed conversations.

The instrument artwork is original vector illustration rather than product photography. Original Portuguese data and manual files are preserved. Public explanatory material is in English according to the recruiting email. The final Google Forms response should include the public repository link and the evidence required by the challenge.

The agent sends exactly one system message at the beginning of each request, combining its instructions with the current validated UI context. This also applies after conversation history and during tool follow-ups, because the Qwen template rejects later system messages. Restart a running web application after updating the source so that it loads this correction.
