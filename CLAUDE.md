# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

`anna-dl` is a terminal tool that searches annas-archive.org, shows metadata for the top results, lets the user pick one interactively, and downloads it (via the Libgen.li mirror) using headless Chrome driven by Selenium. It is a uv-managed package (`src/anna_dl/`, `uv_build` backend) exposing the console script `annadl`.

## Commands

```sh
uv sync                                          # create .venv, install deps + the package (editable)
uv run annadl --help                             # or: uv run python -m anna_dl --help
uv run annadl [path] --s "query" [--n 5]         # --n 0 = all results on the first page
uv run annadl --s "query" --mirror https://...   # override configured mirrors (repeatable)
uv run annadl --s "query" --show-browser         # visible Chrome; pause for manual verification (search + libgen)
uv add <pkg>                                     # add a dependency (updates pyproject + lock)
uv lock --upgrade                                # upgrade all locked deps
uv tool install .                                # install `annadl` globally from a clone
```

Running `annadl` requires Google Chrome. `webdriver-manager` downloads a matching chromedriver into `~/.wdm/`. There are no tests or CI configured. A real run hits the network and blocks on `input()` for the selection. To exercise the flow offline, serve HTML fixtures with `python -m http.server`: put the results page at `search/index.html` and the record page next to it. Then run `uv run annadl --s x --mirror http://127.0.0.1:PORT`.

## Architecture (`src/anna_dl/`)

`cli.main()` runs these in order:

1. **`config.py`** resolves settings. Each key comes from the first source that sets it: `./config.json` (cwd), then `~/.config/anna-dl/config.json` (`$XDG_CONFIG_HOME`), then the packaged `src/anna_dl/defaults.json`.
   - `default_download_path()` sets the argparse default for the positional `path`. Precedence: CLI `path` > config `download_path` > `./assets/` (cwd).
   - `configured_mirrors()` returns the Anna's Archive base URLs (`mirrors`). `--mirror` replaces them entirely. The repo's tracked `config.json` and `assets/` (git-ignored except its `.gitignore`) are used only when running from the repo root. Don't commit a personal path in `config.json`.
2. **argparse** runs before Chrome starts, so `--help` works without a browser.
3. **`driver.create_driver(headless=not --show-browser)`** uses `ChromeDriverManager().install()`. `_resolve_chromedriver` works around webdriver-manager sometimes returning the `THIRD_PARTY_NOTICES.chromedriver` path. If that fails it falls back to `webdriver.Chrome()` (Selenium Manager / system chromedriver). It returns `None` after printing hints if both fail.
4. **`driver.enable_downloads()`** registers a custom `send_command` on `driver.command_executor._commands` (private Selenium API) and calls CDP `Page.setDownloadBehavior`.
5. **`search.search()`** tries each mirror in order: `base_url + SEARCH_PATH`. It returns links matching `a.js-vim-focus.custom-a` from the first mirror that is reachable and has results. Unreachable (`WebDriverException`) and empty (parked domain, anti-bot page) mirrors fall through to the next one. With `--show-browser` (`manual_check`), an empty page prompts via `input()`: Enter reloads the search URL after the user completes a check in the Chrome window, and `s` skips the mirror. Record/libgen URLs are then taken from scraped hrefs, so only the search base URL is configured. **`search.print_results()`** walks up to 5 parents to find each result card, then reads the author (from `search?q=` links) and uses regexes on the card text for year, language (`Name [xx]`), format, and size.
6. **`download.download()`** opens the record page (`_open_record`) and clicks "show external downloads" (`SHOW_EXTERNAL_XPATHS`). It then finds a libgen link (`LIBGEN_XPATHS`) and clicks the GET link on libgen (`_click_get_link`, `LIBGEN_GET_XPATHS`). `wait_for_download(path, before)` waits for a file that wasn't in the pre-click listing to appear and finish (`.crdownload` gone). It returns `None` if nothing starts within `DOWNLOAD_START_TIMEOUT` (30s).
   - A missing GET link or a download that never starts counts as a failure. With `manual_check`, both pause via `driver.ask_manual_check()`, the same prompt `search()` uses. A missing GET link reloads the libgen page on retry. A download that never starts just keeps waiting, because a check after clicking GET usually continues to the file by itself.
   - On failure it reopens the record page and prints its `a.js-download-link` links for manual download.

`cli.main()` owns cleanup and exit codes: `driver.quit()` runs in `finally`. It returns 1 on errors and invalid selections, and 130 on Ctrl-C.

## Gotchas

- **Scraping is brittle.** Selectors track Anna's Archive / Libgen markup, and most commits in history are "updated for UI changes". Selectors live in ordered lists (module-level constants in `download.py`). Prefer adding fallbacks over replacing them.
- **Domains change; keep URLs out of code.** When a domain dies, update `src/anna_dl/defaults.json`, not the Python source. As of 2026-09: `.org` and `.se` are NXDOMAIN and `.li` is parked. `.pk` (DDoS-Guard) and `.gs` are live but show anti-bot challenges to headless Chrome, so use `--show-browser` for those. Some look-alike domains are fakes (e.g. `.is` and `.cc` in 2026-09): they have different markup and gate downloads behind login, payment or Telegram. Verify a new domain before adding it to `defaults.json`: it should use `/md5/<hash>` record links and match `a.js-vim-focus.custom-a`.
- Libgen links are matched by the substring `libgen` in hrefs and page text (`LIBGEN_XPATHS`), not by a fixed domain.
- **`wait_for_download()` gives up after 30s in headless mode.** A slow libgen server that takes longer to start sending the file is reported as a failure, even though Chrome may still finish the download in the background until `driver.quit()`.
- The search query is inserted into the URL without URL-encoding.
- `uvx ruff check src` flags the broad `except Exception` blocks (`BLE001`). They are intentional, for scraping robustness. There is no project ruff config.
