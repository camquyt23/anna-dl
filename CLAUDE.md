# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

`anna-dl` is a terminal tool that searches annas-archive.org, shows metadata for the top results, lets the user pick one interactively, and downloads it (via the Libgen.li mirror) using headless Chrome driven by Selenium. It is a uv-managed package (`src/anna_dl/`, `uv_build` backend) exposing the console script `annadl`.

## Commands

```sh
uv sync                                          # create .venv, install deps + the package (editable)
uv run annadl --help                             # or: uv run python -m anna_dl --help
uv run annadl [path] --s "query" [--n 5]         # --n 0 = all results on the first page
uv add <pkg>                                     # add a dependency (updates pyproject + lock)
uv lock --upgrade                                # upgrade all locked deps
uv tool install .                                # install `annadl` globally from a clone
```

Running `annadl` requires Google Chrome. `webdriver-manager` downloads a matching chromedriver into `~/.wdm/`. There are no tests or CI configured. A real run hits the network and blocks on `input()` for the selection. To exercise the flow offline, patch `anna_dl.search.SEARCH_URL` to a local `file://` HTML fixture and call `anna_dl.cli.main([...])`.

## Architecture (`src/anna_dl/`)

`cli.main()` runs these in order:

1. **`config.default_download_path()`** sets the argparse default for the positional `path`. Precedence: CLI `path` > `download_path` in `./config.json` (cwd) > `~/.config/anna-dl/config.json` (`$XDG_CONFIG_HOME`) > `./assets/` (cwd). The repo's tracked `config.json` and `assets/` (git-ignored except its `.gitignore`) are used only when running from the repo root. Don't commit a personal path in `config.json`.
2. **argparse** runs before Chrome starts, so `--help` works without a browser.
3. **`driver.create_driver()`** uses `ChromeDriverManager().install()`. `_resolve_chromedriver` works around webdriver-manager sometimes returning the `THIRD_PARTY_NOTICES.chromedriver` path. If that fails it falls back to `webdriver.Chrome()` (Selenium Manager / system chromedriver). It returns `None` after printing hints if both fail.
4. **`driver.enable_downloads()`** registers a custom `send_command` on `driver.command_executor._commands` (private Selenium API) and calls CDP `Page.setDownloadBehavior`.
5. **`search.search()`** loads `SEARCH_URL` and returns links matching `a.js-vim-focus.custom-a`. **`search.print_results()`** walks up to 5 parents to find each result card, then reads the author (from `search?q=` links) and uses regexes on the card text for year, language (`Name [xx]`), format, and size.
6. **`download.download()`** opens the record page and clicks "show external downloads" (`SHOW_EXTERNAL_XPATHS`). It finds a libgen link (`LIBGEN_XPATHS`), clicks `get.php` on libgen (`LIBGEN_GET_XPATHS`), and `wait_for_download()` polls for `.crdownload` files. If libgen is absent or `_download_from_libgen` returns False, it prints the remaining `a.js-download-link` links for manual download.

`cli.main()` owns cleanup and exit codes: `driver.quit()` runs in `finally`. It returns 1 on errors and invalid selections, and 130 on Ctrl-C.

## Gotchas

- **Scraping is brittle.** Selectors track Anna's Archive / Libgen markup, and most commits in history are "updated for UI changes". Selectors live in ordered lists (module-level constants in `download.py`, `SEARCH_URL` in `search.py`). Prefer adding fallbacks over replacing them.
- **`annas-archive.org` may not resolve** (DNS/seizure). The domain is hardcoded in `search.SEARCH_URL`.
- **`wait_for_download()` can return early.** It sleeps 1s and then returns as soon as no `.crdownload` file exists. If the download hasn't started within that second, it returns immediately and reports success. A stale `.crdownload` in the directory makes it wait forever.
- The search query is inserted into the URL without URL-encoding.
- `uvx ruff check src` flags the broad `except Exception` blocks (`BLE001`). They are intentional, for scraping robustness. There is no project ruff config.
