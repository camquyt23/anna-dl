"""Download a selected book, via Libgen.li when possible."""
import os
import time

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from anna_dl.driver import ask_manual_check

SHOW_EXTERNAL_XPATHS = [
    "//a[contains(text(), 'show external downloads')]",
    "//a[contains(text(), 'external downloads')]",
    "//button[contains(text(), 'show external downloads')]",
]

LIBGEN_XPATHS = [
    "//a[@class='js-download-link' and contains(@href, 'libgen') and text()='Libgen.li']",
    "//a[contains(@href, 'libgen') and contains(@class, 'download')]",
    "//a[contains(text(), 'Libgen') and contains(@href, 'libgen')]",
    "//a[contains(@href, 'libgen')]",
]

LIBGEN_GET_XPATHS = [
    "//a[contains(@href, 'get.php')]",
    "//a[contains(text(), 'GET')]",
    "//a[contains(@href, 'download')]",
]

# Seconds to wait for a download to show up after clicking GET
DOWNLOAD_START_TIMEOUT = 30


def wait_for_download(path: str, before: set[str]) -> str | None:
    '''Wait for a file that isn't in `before` (the directory listing taken before clicking) to
    appear in path and for Chrome to finish it (.crdownload gone). Returns the elapsed seconds,
    or None if no download started within DOWNLOAD_START_TIMEOUT.'''
    start_time = time.time()

    while True:
        time.sleep(1) # Precision
        new_files = set(os.listdir(path)) - before
        if new_files and not any(f.endswith('.crdownload') for f in new_files):
            return "%s" % round(time.time() - start_time, 4)
        if not new_files and time.time() - start_time > DOWNLOAD_START_TIMEOUT:
            return None


def _show_external_downloads(driver: WebDriver) -> None:
    for xpath in SHOW_EXTERNAL_XPATHS:
        try:
            driver.find_element(By.XPATH, xpath).click()
            return
        except NoSuchElementException:
            continue
    print("Could not find 'show external downloads' link. Looking for direct download links...")


def _click_get_link(driver: WebDriver) -> bool:
    '''Click the GET link on a libgen page. Returns False if there is none (e.g. the page is
    a verification check).'''
    try:
        driver.execute_script("document.querySelector('a[href*=\"get.php\"]').click();")
        return True
    except Exception:
        for xpath in LIBGEN_GET_XPATHS:
            try:
                driver.find_element(By.XPATH, xpath).click()
                return True
            except NoSuchElementException:
                continue
    return False


def _download_from_libgen(driver: WebDriver, download_path: str, manual_check: bool) -> bool:
    '''Follow the Libgen.li mirror and download from it. Returns False on failure.

    With manual_check (visible browser), pauses so the user can complete a verification check
    when the GET link is missing or the download doesn't start.'''
    try:
        libgen_link = None
        for xpath in LIBGEN_XPATHS:
            try:
                libgen_link = driver.find_element(By.XPATH, xpath).get_attribute('href')
                break
            except NoSuchElementException:
                continue

        if not libgen_link:
            print("Could not find libgen download link")
            raise NoSuchElementException("Libgen link not found")

        # Open download link on libgen
        driver.get(libgen_link)
        time.sleep(3)

        before = set(os.listdir(download_path))

        # Look for download link on libgen page, reloading after a manual check
        while not _click_get_link(driver):
            if not (manual_check and ask_manual_check("No GET link on the libgen page", "give up on libgen")):
                raise NoSuchElementException("GET link not found on the libgen page")
            driver.get(libgen_link)
            time.sleep(3)

        print("Downloading ...")

        # A check after clicking GET usually continues to the file by itself, so just keep waiting
        while (dl_time := wait_for_download(download_path, before)) is None:
            if not (manual_check and ask_manual_check(
                    f"Download did not start within {DOWNLOAD_START_TIMEOUT}s", "give up on libgen")):
                raise TimeoutError(f"Download did not start within {DOWNLOAD_START_TIMEOUT}s")

        print(f'Successfully downloaded. ({dl_time} seconds)')
        return True

    except Exception as e:
        print(f"Error with libgen download: {e}")
        print("Falling back to manual link selection...")
        return False


def _print_download_links(driver: WebDriver) -> None:
    '''List the remaining download links so the user can open one manually.'''
    try:
        download_elements = driver.find_elements(By.CSS_SELECTOR, 'a.js-download-link')

        if not download_elements:
            download_elements = driver.find_elements(By.CSS_SELECTOR, 'a[href*="download"]')

        if not download_elements:
            download_elements = driver.find_elements(By.XPATH, "//a[contains(@href, 'http') and (contains(@href, 'libgen') or contains(@href, 'download') or contains(@href, 'mirror'))]")

        for i, element in enumerate(download_elements, start=1):
            try:
                link_text = element.text.strip()
                link_href = element.get_attribute('href')

                # Get parent element text for context
                parent_text = ""
                try:
                    parent_text = element.find_element(By.XPATH, "..").text.strip()
                except Exception:
                    pass

                print(f"\nOption {i}:")
                print(f"\tLink Text: {link_text}")
                print(f"\tLink Href: {link_href}")
                if parent_text and parent_text != link_text:
                    print(f"\tContext: {parent_text}")

            except Exception as e:
                print(f"\nOption {i}: Error extracting link info - {e}")

    except Exception as e:
        print(f"Could not find download links: {e}")


def _open_record(driver: WebDriver, record_url: str) -> str:
    '''Open the record page with external downloads expanded; returns its lowercased text.'''
    driver.get(record_url)

    # Wait for page to load
    time.sleep(2)

    _show_external_downloads(driver)

    # Wait for external downloads to load
    time.sleep(2)

    return driver.find_element(By.XPATH, "/html/body").text.lower()


def download(driver: WebDriver, record_url: str, download_path: str, manual_check: bool = False) -> None:
    '''Download the book at record_url, or list manual download links if Libgen fails.'''
    page_text = _open_record(driver, record_url)

    if 'libgen' in page_text:
        if _download_from_libgen(driver, download_path, manual_check):
            return
        # Back to the record page so the fallback lists its links, not the libgen page's
        _open_record(driver, record_url)

    print("ERROR: libgen.li link not found or failed.")
    print("The following links require human verification.")
    time.sleep(2)
    _print_download_links(driver)
