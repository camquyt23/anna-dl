"""Command-line entry point: search, pick a result, download it."""
import argparse
import os

from selenium.webdriver.remote.webdriver import WebDriver

from anna_dl.config import configured_mirrors, default_download_path
from anna_dl.download import download
from anna_dl.driver import create_driver, enable_downloads
from anna_dl.search import print_results, search


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog='annadl')

    parser.add_argument('path', metavar='path', type=str, default=default_download_path(), action='store',
                        nargs='?', help='A path for the download')

    parser.add_argument('--s', metavar='search', type=str, action='store',
                        required=True, help='A search query for the download')

    parser.add_argument('--n', metavar='quantity', type=int, default=5,
                        help='Number of search results desired (0 = all results on the page)')

    parser.add_argument('--mirror', metavar='url', action='append',
                        help="Anna's Archive base URL to use instead of the configured mirrors (repeatable)")

    parser.add_argument('--show-browser', action='store_true',
                        help='Open a visible Chrome window instead of headless, so you can complete '
                             'browser verification checks (e.g. DDoS-Guard) by hand')

    return parser.parse_args(argv)


def run(driver: WebDriver, download_path: str, mirrors: list[str], query: str, result_count: int,
        manual_check: bool = False) -> int:
    # Ensure download directory exists
    os.makedirs(download_path, exist_ok=True)
    enable_downloads(driver, download_path)

    book_links = search(driver, mirrors, query, manual_check)
    print(f"Found {len(book_links)} book links")

    if result_count == 0:
        result_count = len(book_links)
    elif len(book_links) < result_count:
        result_count = len(book_links)
        print(f"Only {result_count} results found")

    if result_count == 0:
        print("No results found. Please check your search query, or update the mirrors "
              "in config.json (or pass --mirror) if the domains have changed.")
        if not manual_check:
            print("If a mirror blocks headless Chrome with a verification check, retry with --show-browser.")
        return 1

    book_links = book_links[:result_count]
    sresults = [str(link.get_attribute('href')) for link in book_links]
    print_results(book_links)

    book_selection = int(input("\nEnter desired download: "))

    if book_selection < 1 or book_selection > len(sresults):
        print("Invalid selection")
        return 1

    download(driver, sresults[book_selection-1], download_path, manual_check)
    return 0


def main(argv: list[str] | None = None) -> int:
    # Parse before starting Chrome so --help doesn't need a browser
    args = parse_args(argv)

    driver = create_driver(headless=not args.show_browser)
    if driver is None:
        return 1

    try:
        return run(driver, args.path, args.mirror or configured_mirrors(), args.s, args.n,
                   manual_check=args.show_browser)
    except KeyboardInterrupt:
        print("\nScript interrupted by user")
        return 130
    except Exception as e:
        print(f"An error occurred: {e}")
        return 1
    finally:
        driver.quit()
