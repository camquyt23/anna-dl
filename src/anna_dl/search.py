"""Search Anna's Archive and print metadata for the results."""
import re
import time

from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from anna_dl.driver import ask_manual_check

# Appended to each mirror's base URL (see config.configured_mirrors)
SEARCH_PATH = "/search?q={query}"


def _load_results(driver: WebDriver, url: str) -> list[WebElement]:
    driver.get(url)

    # Wait for page to load
    time.sleep(2)

    # scroll to the bottom of the page so that every element I search for is returned.
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # Wait a bit more for dynamic content
    time.sleep(1)

    return driver.find_elements(By.CSS_SELECTOR, 'a.js-vim-focus.custom-a')


def search(driver: WebDriver, mirrors: list[str], query: str, manual_check: bool = False) -> list[WebElement]:
    '''Try each mirror in order and return the result title links from the first one that
    is reachable and has results. Dead or parked domains fall through to the next mirror.

    With manual_check (visible browser), an empty page pauses so the user can complete a
    browser verification (e.g. DDoS-Guard) in the Chrome window and retry.'''
    for base_url in mirrors:
        print(f"Searching {base_url} ...")
        url = base_url.rstrip('/') + SEARCH_PATH.format(query=query)
        try:
            book_links = _load_results(driver, url)
            while not book_links and manual_check and ask_manual_check("No results", "skip this mirror"):
                book_links = _load_results(driver, url)
        except WebDriverException as e:
            print(f"\tUnreachable: {(e.msg or str(e)).splitlines()[0]}")
            continue

        if book_links:
            return book_links
        print("\tNo results")

    return []


def _find_container(book_link: WebElement) -> WebElement:
    '''Walk up from the title link to the result card that holds its metadata.'''
    container = book_link
    try:
        for _ in range(5):  # Try up to 5 parent levels
            container = container.find_element(By.XPATH, "..")
            classes = container.get_attribute('class') or ""
            if 'flex' in classes and ('pt-3' in classes or 'border-b' in classes):
                break
    except Exception:
        # If we can't find the container, use the book_link's grandparent
        container = book_link.find_element(By.XPATH, "../..")
    return container


def _extract_author(container: WebElement, title: str) -> str:
    try:
        for link in container.find_elements(By.TAG_NAME, 'a'):
            href = link.get_attribute('href') or ""
            text = link.text.strip()
            # Skip the main title link and empty links
            if href and 'search?q=' in href and text and text != title:
                # Author names are usually short
                if len(text.split(',')) <= 2 and len(text.split()) <= 4:
                    return text
    except Exception as e:
        print(f"\t  Error extracting author: {e}")
    return "Unknown"


def _extract_year(text: str) -> str:
    year_match = re.search(r'\b(19|20)\d{2}\b', text)
    return year_match.group(0) if year_match else "Unknown"


def _extract_metadata(text: str) -> tuple[str, str, str]:
    '''Return (language, format, size) parsed from the result card text.'''
    # Language (pattern like "English [en]")
    language_match = re.search(r'(\w+)\s+\[([a-z]{2})\]', text)
    # File format (like EPUB, PDF)
    format_match = re.search(r'\b(EPUB|PDF|MOBI|AZW3|TXT|DOC|DOCX)\b', text, re.IGNORECASE)
    # File size (like 0.3MB)
    size_match = re.search(r'(\d+\.?\d*\s*[MKG]B)', text, re.IGNORECASE)

    return (
        language_match.group(1) if language_match else "Unknown",
        format_match.group(1).upper() if format_match else "Unknown",
        size_match.group(1) if size_match else "Unknown",
    )


def print_results(book_links: list[WebElement]) -> None:
    '''Print a numbered list of results with whatever metadata can be scraped.'''
    for i, book_link in enumerate(book_links, start=1):
        try:
            title = book_link.text.strip()
            container = _find_container(book_link)
            print(f"\n[{i}] {title}")

            all_text = container.text

            print(f"\tAuthor: {_extract_author(container, title)}")
            print(f"\tYear: {_extract_year(all_text)}")

            language, file_format, file_size = _extract_metadata(all_text)
            print(f"\tLanguage: {language}")
            print(f"\tFormat: {file_format}, Size: {file_size}")

            if i == 1:  # Print debug info for first result
                print(f"\t  Debug - Container text preview: {all_text[:200]}...")

        except Exception as e:
            print(f"\n[{i}] Error extracting info for book {i}: {e}")
            # Print at least the title if we can get it
            try:
                print(f"\tTitle: {book_link.text.strip()}")
            except Exception:
                print("\tCould not extract title")
