# anna-dl
Python tool allowing easy books downloads from the terminal

Replacement for [zlib-dl](https://github.com/Nquxii/zlib-dl)

<img src="images/demo-f.gif" align="center">

## Features 
- Bypass randomly generated links to downloads
- Obtain a specified number of results
- Retrieve metadata without having to go onto annas-archive.org itself

## Installation
Requires [uv](https://docs.astral.sh/uv/) and Google Chrome.

Install `annadl` as a global command
```
uv tool install git+https://github.com/camquyt23/anna-dl
```

Or clone the repository for development
```
git clone https://github.com/camquyt23/anna-dl
cd anna-dl
uv sync
uv run annadl --help
```

## Configuration
Settings are read from `./config.json` (current directory) first, then `~/.config/anna-dl/config.json`.
```json
{
    "download_path": "/home/johndoe/Documents/books",
    "mirrors": ["https://annas-archive.pk", "https://annas-archive.gl"]
}
```
- `download_path`: where downloads go, so you don't need to pass the path each time.
- `mirrors`: Anna's Archive base URLs, tried in order until one is reachable and returns results. Its domains change often; if searches start failing, point this at the current ones. Defaults to the list in [`src/anna_dl/defaults.json`](src/anna_dl/defaults.json). For a one-off run, use `--mirror URL` (repeatable) instead.

## Usage
```
annadl [path] --s [query] --n [number of results] [--mirror URL] [--show-browser]
```
(Use `uv run annadl ...` inside a clone.)

Number of results defaults to 5 of the top results available. Use 0 to see all search results on the page.

### Browser verification checks
Some mirrors put a verification page (e.g. DDoS-Guard) in front of the site that headless Chrome can't pass, which shows up as "No results". Add `--show-browser` to open a visible Chrome window. When a mirror returns no results, annadl pauses so you can complete the check in that window, then press Enter to retry (or type `s` to skip to the next mirror). It pauses the same way on the Libgen side, if the GET link is missing or the download doesn't start within 30s.
```
annadl --s "The Pragmatic Programmer" --show-browser
```

### Download location
If a path in the command is specified, it will be used. Otherwise, the download_path in config.json will be used.
If none of these options are available, the program will use `./assets/` (relative to the current directory) as its download folder.

### Example
View 5 search results for "The Pragmatic Programmer". Download the resulting file in /home/johndoe/Documents/books
```
annadl /home/johndoe/Documents/books --s "The Pragmatic Programmer"
```

View **all** search results on the first page for "Don Quixote". Download the resulting file in ./assets/ (assuming no set path in config.json)
```
annadl --s "Don Quixote" --n 0
```
