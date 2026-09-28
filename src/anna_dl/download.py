"""Download a selected book, via Libgen.li when possible."""
import os
import time

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

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


def wait_for_download(path: str) -> str:
    ''' Wait until the file download is completed. Will not work if a corrupted download is already
    in the given path. If the function starts before the download, it won't wait for its completion.'''
    start_time = time.time()
    dl_wait = True

    while dl_wait:
        time.sleep(1) # Precision
        dl_wait = any(book.endswith('.crdownload') for book in os.listdir(path))

    return "%s" % round(time.time() - start_time, 4)


def _show_external_downloads(driver: WebDriver) -> None:
    for xpath in SHOW_EXTERNAL_XPATHS:
        try:
            driver.find_element(By.XPATH, xpath).click()
            return
        except NoSuchElementException:
            continue
    print("Could not find 'show external downloads' link. Looking for direct download links...")


def _download_from_libgen(driver: WebDriver, download_path: str) -> bool:
    '''Follow the Libgen.li mirror and download from it. Returns False on failure.'''
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

        # Look for download link on libgen page
        try:
            driver.execute_script("document.querySelector('a[href*=\"get.php\"]').click();")
        except Exception:
            for xpath in LIBGEN_GET_XPATHS:
                try:
                    driver.find_element(By.XPATH, xpath).click()
                    break
                except NoSuchElementException:
                    continue

        print("Downloading ...")

        dl_time = wait_for_download(download_path)

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


def download(driver: WebDriver, record_url: str, download_path: str) -> None:
    '''Download the book at record_url, or list manual download links if Libgen fails.'''
    driver.get(record_url)

    # Wait for page to load
    time.sleep(2)

    _show_external_downloads(driver)

    # Wait for external downloads to load
    time.sleep(2)

    page_text = driver.find_element(By.XPATH, "/html/body").text.lower()

    if 'libgen' in page_text and _download_from_libgen(driver, download_path):
        return

    print("ERROR: libgen.li link not found or failed.")
    print("The following links require human verification.")
    time.sleep(2)
    _print_download_links(driver)
