# Empório da Música

I built this prototype for Artefact's AI Engineer challenge to help a fictional music shop answer questions about instruments, prices, orders and store policies. Customers can browse the catalogue and ask questions in a side chat. Python and SQLite supply the facts, while a connected model interprets free wording and requests the tools it needs.

![The catalogue and store assistant](docs/preview.png)

The project runs locally without rented hosting. It includes 65 catalogue entries, dedicated product pages, English and Brazilian Portuguese, instrument comparisons and a demonstration order check. Five recorded conversations show what the application actually returned with a local model. The [development record](docs/development-record.md) keeps the detailed experiments, corrections and reproduction notes alongside this shorter guide.

## Start the application

Use Python 3.12 or newer and run these commands from the repository root. The application was checked with Python 3.12 in Ubuntu WSL and Python 3.13 on Windows. Keep their virtual environments separate.

In PowerShell on Windows, create the environment, install the dependencies and start the server.

```powershell
python -m venv .venv-win
.\.venv-win\Scripts\python.exe -m pip install -r requirements.txt
.\.venv-win\Scripts\python.exe run.py
```

In Ubuntu or the VS Code WSL terminal, use the Linux environment instead.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run.py
```

Open `http://localhost:8765` in your browser. Stop the server with Ctrl+C. Once the environment is installed, only the final start command is needed. The included `start-windows.cmd` and `start-wsl.cmd` launch the corresponding prepared environments from Windows. Run one normal shop instance at a time. After changing application source, restart the server to load it.

The server rebuilds its SQLite database in the ignored `.runtime` directory from the supplied CSV files and the documented catalogue corrections. Local image references, test recordings and previously generated databases are not needed to run the shop. A submission check started an export containing only versionable files and verified the rebuilt catalogue, policies, product pages and all 61 published JPGs. It reused installed Python dependencies rather than claiming a fresh dependency installation.

## Browse, connect and ask

Without a model, the interface says Catalogue preview. Browsing, filters, product details, discounts, policy lookup, the demonstration order check and Markdown conversation export still work through a small deterministic router. Free conversation needs a model connection, and preview mode is not presented as an LLM.

Choose Connect a model and enter the API base URL, model ID and a key if required. The endpoint must support Chat Completions with function tools. Load models queries that endpoint, and manual model entry remains available. The presets cover common local addresses and OpenAI, but a returned model list does not prove tool compatibility. The local evaluations used `http://127.0.0.1:8080/v1` through llama.cpp and `llama-swap`. A Windows model service may need its Windows host address when the Python app runs in WSL, because Python resolves the endpoint rather than the browser.

Choose a category, search for an instrument and use the price, payment or availability filters. A product preview links to its full page, where the catalogue description, specifications and relevant delivery, return and warranty information appear together. The section links move to the matching content and support direct links. Product URLs work after reload and with browser back and forward navigation.

Ask about this instrument selects the product and focuses the chat without sending anything. Topic buttons prepare an editable question about sound, build, availability, price, delivery, returns or warranty. You can also open a blank field for your own question. Only Send submits it. An explicitly named instrument takes priority over the current selection, and an ambiguous reference prompts a clarification. A model can suggest another catalogue view, but the separate Open button needs your click before navigation happens.

The EN and BR buttons beside the store location select English or Brazilian Portuguese for the interface and future replies. The pressed button is active, and the browser remembers the choice. Each model request receives the current language, even if an earlier message or the customer's wording uses another language. Switching keeps the conversation and connection. Existing messages retain their original language. The switch is briefly disabled while a reply is running.

For an order question, first use the lookup dialog with the order number and matching email from the fictional dataset. Verification grants access to that order in the same browser session. It is a demonstration knowledge check, not customer authentication. The chat menu also offers a new conversation, a Markdown export and the tool descriptions. A reset clears product comparison preferences and verified order access.

API keys stay in the server's current browser session and are never returned to the interface or written to disk. Changing the endpoint without supplying a new key clears the previous key. Restarting the server or two hours of inactivity discards the session, so there is no permanent conversation history. The Markdown export lets a customer keep a copy.

![A product page with contextual chat](docs/product-page.png)

## Why I chose this design

I chose FastAPI to serve a small Python application and its HTML, CSS and JavaScript without a frontend build step. SQLite fits the structured catalogue and order data, and parameterized queries make the data reads inspectable. Prices use integer cents and decimal rounding. The model chooses tools, while Python validates the arguments and renders factual replies from the results. This keeps a made up price in raw model text from becoming a customer quote, at the cost of less freedom in the final phrasing.

The browser and agent share `search_products`, `get_product`, `compare_products`, `lookup_policy`, `get_order` and `navigate_catalog`. Current category, selection, filters and visible product IDs accompany each message. Clear requests are bound to the customer's product, category and budget instead of trusting guessed model arguments or an older selection. Unrecognized wording still uses the general model loop, so this is a bounded safeguard rather than a complete language validator. Repeated identical read calls are reused within one turn and remain visible in the trace.

For the short policy manual, I chose retrieval of relevant PDF pages with source references and reviewed summaries rather than adding embeddings and a vector database. Specific questions select the recorded details for instalments, mixed payments, refunds, returns, warranty and shipping. If the model omits a lookup for a supported question, the application performs and logs it. Policy replies leave out unsolicited product overviews. Unknown wording can fall back to a general topic summary, which remains a limitation.

The API boundary lets models change without replacing shop rules. Local llama.cpp through `llama-swap` reused available weights without a paid model service. Bonsai27B has the broad functional acceptance evidence, while the Qwen variants also have recorded security comparisons. Those security checks alone do not establish equivalent functional acceptance. I developed instrument advice on `feature/instrument-advice` to keep the pushed baseline separate during that work. The branch has since been integrated into `main`.

The official MCP Python SDK supplies a thin stdio adapter for the four public read tools. Start it from the prepared environment with `.venv/bin/python run_mcp.py`, or use the Windows interpreter. Configure an MCP host with absolute paths to that interpreter and `run_mcp.py`. It waits for a client on standard input and output rather than opening a webpage. Orders and browser navigation are excluded because that separate process has no verified browser session. Both interfaces use the same tool implementations.

## Decisions about advice, prices and source data

The assistant compares two or three identified instruments using recorded differences, availability, budget, string preference and electronics. Follow up preferences update the comparison. Candidates above the budget remain visible so the answer can explain why they do not fit. Missing weight, tone, comfort or playing feel stays unknown rather than being inferred from brand, material or price. If one confirmed instrument meets the stated conditions, it can support a conditional recommendation. Otherwise the assistant asks for more information. A provider failure produces a labelled catalogue comparison, not a claim of successful model advice.

Discounts never stack. I chose to apply the highest eligible single discount, comparing an active product promotion with the 5% PIX discount when applicable. The manual states no minimum purchase for the PIX discount. The PIX condition is full immediate receipt by the store, even if the customer's bank finances the payment separately. The manual permits mixed payments above R$2,000. Our interpretation excludes the PIX discount for a mixed payment, while an independently valid promotion can still apply. These are documented interpretations where the manual is not explicit.

I also chose to preserve the supplied CSV files when their descriptions contradicted their names or specifications. For the keyboard entries, I explicitly assigned the existing Roland description to Roland product 144 and the Yamaha description to product 142, renamed `Teclado Arranjador Yamaha 61 Teclas`. I subsequently set the derived Roland key count to 88 to match its description. Codex implemented these decisions in a separate [correction layer](src/emporio/data/corrections.py), preserving the original sources and recording the description donor. A visible notice explains that the exact models have not been verified with the manufacturers.

Products 135, 137, 139 and 140 retain their conflicting source claims. English and Portuguese notices appear in the catalogue, preview, product page and relevant replies. SQLite and the tools expose the affected fields, and comparisons exclude these products from confirmed recommendations. Prices and stock remain readable from the snapshot. The [development record](docs/development-record.md) identifies each conflict and its checks. This covers the known contradictions, not a complete manufacturer audit of all 65 products.

I explored instrument images to make the shop easier to browse. Generation produced inaccurate details, while a later photo search could not consistently establish an exact model and clear permission to republish it. The experiments took substantial time, so I chose a consistent illustrative style instead of pursuing exact photographs for every entry. The shop now uses 61 generated illustrations and four neutral vector images for the unresolved products. A red notice, tooltip and alternative text follow the selected language and explain that illustrations can differ from the real product. They do not establish appearance or specifications. The [image index](src/emporio/web/static/products/index.json) retains selection hashes and tolerated differences. Reference photos and unused candidates stay local and are not redistributed. The detailed image history remains in the development record.

## What was checked

The current suite passed 153 tests under Windows during the submission review on 4 November 2026. Earlier suites also passed under WSL. These checks cover SQLite queries, discounts, order scope, separate sessions, languages, tool validation, provider failures and an actual MCP subprocess handshake. Their simulated model responses do not establish real model compatibility. Separate browser checks covered product navigation, editable chat drafts, desktop and mobile layouts, language switching and confirmation before agent navigation.

Install the development dependencies and run the suite from the repository root. On Windows use the separate test directories below.

```powershell
.\.venv-win\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv-win\Scripts\python.exe -m pytest -q --basetemp .runtime/test-temp-windows-user -o cache_dir=.runtime/pytest-windows-user
```

In WSL, use the Linux interpreter.

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q -o cache_dir=/tmp/artefact-musicstore-pytest
```

The five actual model conversations cover [catalogue prices and availability](examples/01-catalogue-live.md), [order verification](examples/02-orders-live.md), [service, context and language](examples/03-service-context-live.md), [specific policy questions](examples/04-bonsai-policy-review.md) and [instrument comparisons](examples/05-bonsai-instrument-advice.md). They use prepared questions rather than independent customer traffic and distinguish real provider calls from direct application answers. The broader Bonsai run passed 24 steps with 21 chat turns and three verification or reset events. Seventeen turns used the provider and four were direct clarifications or stock checks. The [acceptance record](docs/model-acceptance.json) preserves the checks and application hashes.

The requested prompt injection review is complete. Bonsai27B, abliterated Qwen Q8_0, Qwen NVFP4/BF16 and Qwen GSQ were tested with the original attacks and targeted conversations involving three messages. Earlier navigation failures led to explicit confirmation and a reset correction. In the current application samples, no unauthorized application effect was observed, although raw models sometimes followed attacks, adopted false prices or disclosed internal context. Timeouts, empty replies and truncated outputs are retained as failures or inconclusive results. The [development record](docs/development-record.md) links each model report and preserves the differences between raw responses, tool attempts and visible effects.

On 4 November 2026 I accepted those limits for the local prototype and retained the 45 second provider read deadline, 2,048 token completion budget and existing safeguards. Larger budgets did not provide a general cure. This decision does not turn failed cases into passes or certify a production service. The model profiles and runtime settings differ, so the observations are not a general model ranking.

## Limits and further work

The data is a supplied snapshot, not a live shop or carrier connection. Estimated delivery is not proof of receipt. Manufacturer warranty terms are not inferred, and conflicting contact information, incomplete return facts and the undefined shipping rule at exactly R$500 remain visible limitations. The order check does not authenticate a real customer. The app performs no purchase, payment, refund or complaint registration. It binds to loopback, rejects unrelated hosts and cross site API requests, and is not ready for public access by multiple customers.

With more time I would add proper customer authentication, connect catalogue and order tools to actual store services and confirm the remaining product identities with the team. I would extend functional acceptance for each supported model, improve ambiguous references and make timeout and incomplete output handling clearer. Public hosting and real transactions would require separate implementation and review.

## How coding AI was used

I used Codex to inspect the assignment and data, discuss decisions, implement the prototype and tests, and prepare documentation from my questions and writing references. Codex also prepared the English catalogue translations while preserving the Portuguese source files. Decisions about discounts, catalogue corrections, illustration standards and accepted prototype risks came from that discussion, with implementation delegated to the coding agent. The image work also involved Hermes and the local ComfyUI workflow. Its initial automated approval was not reliable enough, so visual findings and changed decisions remain documented rather than hidden.

The [quality record](docs/quality-notes.md) explains observed defects and corrections. Raw test recordings, reference images, generation workflows and internal working notes remain local. The public repository includes the application, supplied data, selected illustrations, reproducible checks and compact evidence. Public explanations are in English, while authentic customer messages and source data may remain Portuguese. The final Google Forms response should include the public repository link and the evidence requested by the challenge.
