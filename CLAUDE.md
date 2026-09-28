# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

`anna-dl` is a terminal tool that searches annas-archive.org, shows metadata for the top results, lets the user pick one interactively, and downloads it (via the Libgen.li mirror) using headless Chrome driven by Selenium. The whole program is a single extensionless Python script: `annadl`.

## Commands

Managed with uv (`pyproject.toml` + `uv.lock`; no build system, the project itself is not installed).

```sh
uv sync                                               # create .venv and install deps
uv run python annadl --help
uv run python annadl [path] --s "query" [--n 5]       # --n 0 = all results on the first page
uv add <pkg>                                          # add a dependency (updates pyproject + lock)
```

Running `annadl` requires Google Chrome. `webdriver-manager` downloads a matching chromedriver into `~/.wdm/`. There are no tests, linter, or CI configured. A real run hits the network and blocks on `input()` for the selection.

## Architecture (`annadl`)

Everything runs top-level, in this order. The only function is `dlwait`.

1. **Config / download path.** Precedence: positional CLI `path` > `config.json` `download_path` > `./assets/`. `config.json` and `assets/` are resolved relative to the script's realpath (`C_DIR`), not the cwd. `assets/` is git-ignored except its `.gitignore`. `config.json` is tracked, so don't commit a personal path in it.
2. **argparse** runs before the browser starts, so `--help` works without Chrome.
3. **Driver setup.** `ChromeDriverManager().install()`, plus a workaround for webdriver-manager sometimes returning the `THIRD_PARTY_NOTICES.chromedriver` path instead of the binary. It searches sibling and parent dirs and chmods the binary. If that fails it falls back to `webdriver.Chrome()` (system chromedriver), then exits with hints.
4. **Enable headless downloads.** It registers a custom `send_command` on `driver.command_executor._commands` (private Selenium API) and calls CDP `Page.setDownloadBehavior`.
5. **Search.** It loads `https://annas-archive.org/search?q=...` and collects result links via the CSS selector `a.js-vim-focus.custom-a`. For each result it walks up to 5 parent elements to find the card container. It reads the author from `search?q=` links and uses regexes on the container text to get year, language (`Name [xx]`), format, and size.
6. **Selection → record page.** It clicks "show external downloads" (tries several XPaths), then looks for a libgen link using an ordered list of XPath selectors. On the libgen page it clicks the `get.php` link, and `dlwait()` polls the download dir for `.crdownload` files.
7. **Fallback.** It prints the remaining download links (`a.js-download-link`, etc.) for manual/human-verified download.

## Gotchas

- **Scraping is brittle.** Selectors track Anna's Archive / Libgen markup, and most commits in history are "updated for UI changes". When fixing, prefer adding to the ordered selector lists over replacing them, and keep the fallbacks.
- **The fallback in step 7 only runs when `'libgen'` is missing from the page text.** The other half of that condition, `'Error with libgen download:' in str(locals())`, is effectively always false, because the message is only printed and never stored.
- **`dlwait()` can return early.** It sleeps 1s and then returns as soon as no `.crdownload` file exists. If the download hasn't started within that first second, it returns immediately. A stale `.crdownload` already in the directory makes it wait forever.
- The search query is inserted into the URL without URL-encoding.
