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
Set `download_path` in a `config.json` if you don't want to pass the path each time. It is read from `./config.json` (current directory) first, then `~/.config/anna-dl/config.json`.
```json
{
    "download_path": "/home/johndoe/Documents/books"
}
```

## Usage
```
annadl [path] --s [query] --n [number of results]
```
(Use `uv run annadl ...` inside a clone.)

Number of results defaults to 5 of the top results available. Use 0 to see all search results on the page.

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
