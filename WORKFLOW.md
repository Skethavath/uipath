UiPath Automation - Workflow & Developer Documentation

Purpose
-------
This document explains the end-to-end workflow for the repository and the `uipath_automation.py` program. It covers runtime sequence, configuration and environment mapping, CLI usage, debugging, and development notes for extending or maintaining the automation.

Project overview
----------------
- Goal: Automate triggering UiPath jobs using Playwright browser automation when API access is not available.
- Key files:
  - `uipath_automation.py` — Main program and `UiPathAutomation` class containing automation logic.
  - `config.json` — Default configuration for URL, timeouts, browser options, and known jobs.
  - `env.example.txt` — Example environment variables to copy into `.env`.
  - `requirements.txt` — Python dependencies (Playwright, python-dotenv).
  - `README.md` — Usage summary and examples.
  - `WORKFLOW.md` — (This file) detailed workflow documentation.

High-level runtime workflow
---------------------------
1. Startup
   - The script loads environment variables via `load_dotenv()` (from `.env` if present).
   - `UiPathAutomation.__init__` reads `config.json` (if present) and resolves effective configuration.
   - Resolution precedence: explicit environment variables override values in `config.json`.

2. Configuration values used
   - `UIPATH_URL` or `config.json -> uipath.url` (default: `https://platform.uipath.com`).
   - `UIPATH_USERNAME`, `UIPATH_PASSWORD` from env (or `.env`).
   - `HEADLESS` or `config.json -> browser.headless` controls Playwright headless mode.
   - `BROWSER_TIMEOUT` or `config.json -> uipath.timeout` sets Playwright timeouts (ms).
   - `browser.slow_mo` in `config.json` optionally slows actions for debugging.

3. Start browser
   - `start_browser()` calls `sync_playwright().start()`, launches Chromium with the configured `headless` and `slow_mo` values.
   - A `BrowserContext` and `Page` are created; `page.set_default_timeout(timeout)` is applied.

4. Authentication
   - `login()` navigates to the base `UIPATH_URL` and calls `_is_logged_in()`.
   - If not logged in and credentials exist, the script attempts automated login:
     - Tries multiple username and password selectors (robust to small variations).
     - Fills fields and attempts several login button selectors; falls back to pressing Enter.
     - Waits for `networkidle` and re-validates login status via `_is_logged_in()`.
   - If credentials are missing or automated login fails, the script may leave the browser open for manual login and await a user keypress to continue.

5. Navigate to Jobs/Processes
   - `navigate_to_jobs()` searches for links or buttons with text like "Jobs" or "Processes" and clicks them.
   - If navigation elements are not found, it attempts direct navigation to `{base_url}/jobs`.

6. Discover available jobs
   - `list_jobs()` queries the jobs page using a set of candidate selectors (table rows, divs, test ids, class name heuristics).
   - It extracts job/process names and returns a list of candidate jobs (name, index, element handle).
   - On failure to find jobs, the script saves `jobs_page_debug.png` for later inspection.

7. Trigger job runs
   - `run_job(job_name)` finds the job row (e.g., `tr:has-text("{job_name}")`) and looks for play/run buttons inside that row.
   - The script tries a set of play/run button selectors (aria labels, button text, title attributes, nearby selectors).
   - On success, it clicks the run button and logs the result.
   - If the script cannot find the job or button, it logs errors and captures screenshots for debugging.

8. Multiple jobs or run-all
   - The CLI supports repeated `--job` flags for sequential runs and a `--all` option to attempt to run all discovered jobs.

9. Logging and artifacts
   - All runtime logs are written to `uipath_automation.log` and stdout.
   - On errors or unexpected layout, screenshots such as `jobs_page_debug.png` and `error_screenshot.png` are saved.

10. Shutdown
   - The program closes the `Page`, `BrowserContext`, and `Browser` after completion; callers should ensure cleanup via try/finally if modifying execution flow.

Program internals (function & behavior summary)
----------------------------------------------
- `UiPathAutomation.__init__(config_path: str = "config.json")`
  - Loads `config.json` (if present)
  - Reads environment variables
  - Sets `self.url`, `self.username`, `self.password`, `self.headless`, `self.timeout`

- `start_browser()`
  - Calls `sync_playwright().start()`
  - Launches Chromium and sets viewport
  - Creates `self.context` and `self.page` and sets default timeout

- `login() -> bool`
  - Navigates to `self.url`, checks `_is_logged_in()`
  - If not logged in and credentials present, attempts to fill forms with robust selector lists and submit
  - Returns True if it determines login success, False otherwise

- `_is_logged_in() -> bool`
  - Uses an array of positive indicators (text=Jobs, Processes, nav menus) and negative indicators (Sign in, input[type=password])
  - Returns True when page matches logged-in indicators

- `navigate_to_jobs()`
  - Tries multiple link/button selectors for Jobs/Processes
  - Falls back to direct path `/jobs`

- `list_jobs() -> List[Dict]`
  - Uses many candidate selectors to find job/process rows or cards
  - For each element, tries to extract visible name text and returns a list
  - Saves `jobs_page_debug.png` when it cannot find jobs

- `run_job(job_name: str) -> bool`
  - Locates row/div containing `job_name`
  - Looks for play/run button within that row and clicks it
  - If row-based approach fails, iterates alternative play-button selectors
  - Returns True if clicked successfully, False otherwise

- `run_all_jobs()` (implementation detail)
  - Iterates discovered jobs and calls `run_job` for each; returns mapping of job -> success

Configuration & environment mapping
-----------------------------------
Precedence: Environment variables override `config.json`.

Key mappings:
- `UIPATH_URL` → `self.url` (or `config.json` `uipath.url`)
- `UIPATH_USERNAME` → `self.username`
- `UIPATH_PASSWORD` → `self.password`
- `HEADLESS` → `self.headless` (string `true` case-insensitive)
- `BROWSER_TIMEOUT` → `self.timeout` (ms)
- `config.json` keys used: `uipath.timeout`, `browser.headless`, `browser.slow_mo`, `jobs.known_jobs`

CLI usage (examples)
--------------------
List jobs:

```bash
python uipath_automation.py --list-jobs
```

Run a single job (exact name, case-sensitive):

```bash
python uipath_automation.py --job "Daily Sales Report"
```

Run multiple jobs:

```bash
python uipath_automation.py --job "Job 1" --job "Job 2"
```

Run all discovered jobs:

```bash
python uipath_automation.py --all
```

Headless mode (example):

```bash
# via env
set HEADLESS=true
python uipath_automation.py --job "Job"

# or edit config.json -> browser.headless
```

Windows Task Scheduler example (batch file)
------------------------------------------
Create `run_job.bat`:

```batch
@echo off
cd C:\path\to\uipath
set UIPATH_URL=https://platform.uipath.com
set UIPATH_USERNAME=your_user
set UIPATH_PASSWORD=your_pass
python uipath_automation.py --job "Scheduled Job"
```

Then schedule `run_job.bat` in Task Scheduler.

Debugging & troubleshooting
---------------------------
- If login fails:
  - Check `.env` or environment variable values for `UIPATH_USERNAME`, `UIPATH_PASSWORD`, `UIPATH_URL`.
  - Run without headless to observe the login flow.
  - If SSO is used, consider manual login when the browser opens.
- If jobs are not found:
  - Use `--list-jobs` to see the names discovered (or inspect `jobs_page_debug.png`).
  - UiPath UI changes often break selectors; open the saved screenshot and update selectors in `uipath_automation.py` accordingly.
- Check `uipath_automation.log` for detailed error messages and timestamps.
- Saved screenshots: `jobs_page_debug.png`, `error_screenshot.png` help identify DOM changes.

Developer notes & extension points
---------------------------------
- Selector lists are intentionally broad to handle UI variations. If you need higher reliability, narrow selectors to specific attributes used by your tenant.
- Consider switching to Orchestrator REST API or `uipath-python` SDK for more robust automation if API access is available.
- Add explicit retries with exponential backoff around navigation and click operations to reduce flakiness.
- For CI or scheduled runs, prefer headless and keep a separate non-headless debug environment.
- Ensure Playwright browser binaries are installed (`playwright install`) after `pip install -r requirements.txt`.

Security & operational notes
---------------------------
- Do not commit `.env` or real credentials; use environment variables or a secrets manager.
- Logs may contain sensitive information—scrub or restrict access to `uipath_automation.log`.
- Use least-privilege accounts in UiPath to reduce risk when automating job runs.

Suggested improvements
----------------------
- Add unit/integration tests that mock Playwright `Page` interactions so selector changes are easier to validate.
- Add a `--dry-run` flag that lists which actions would be taken without clicking run.
- Add centralized retry and circuit-breaker logic for long-running scheduled executions.
- Optionally implement an Orchestrator API fallback: detect API availability and prefer it over UI automation.

Contact / Next steps
--------------------
If you want, I can:
- Generate a PNG sequence diagram for the workflow.
- Add a `--dry-run` or `--retry` flag to `uipath_automation.py`.
- Create a small wrapper script to run and retry jobs with backoff and reporting.


(End of document)
