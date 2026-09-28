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

Clone the repository and install dependencies
```
git clone https://github.com/camquyt23/anna-dl
cd anna-dl
```
```
uv sync
```

Open help section
```
uv run python annadl --help
```

Ensure your config.json is set if you don't want to use several parameters each time.

Run annadl from anywhere (so you don't need to cd into anna-dl every time) Linux/MacOS — add to your shell rc:
```
alias annadl='uv run --project [CURRENT DIR] python [CURRENT DIR]/annadl'
```

## Usage
```
uv run python annadl [path] --s [query] --n [number of results]
```
Number of results defaults to 5 of the top results available. Use 0 to see all search results on the page.


If a path in the command is specified, it will be used. Otherwise, the download_path in config.json will be used.
If none of these options are available, the program will use `./assets/` as its download folder.

### Example
View 5 search results for "The Pragmatic Programmer". Download the resulting file in /home/johndoe/Documents/books
```
uv run python annadl /home/johndoe/Documents/books --s "The Pragmatic Programmer"
```

View **all** search results on the first page for "Don Quixote". Download the resulting file in ./assets/ (assuming no set path in config.json)
```
uv run python annadl --s "Don Quixote" --n 0
```
