"""Headless Chrome setup."""
import logging
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager


def _chrome_options(headless: bool) -> Options:
    chrome_options = Options()

    # Include this to remove GUI and extensions for the sake of simplicity
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--silent")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    return chrome_options


def _make_executable(path: str) -> str:
    os.chmod(path, 0o755)
    return path


def _resolve_chromedriver(driver_path: str) -> str:
    '''webdriver-manager sometimes returns THIRD_PARTY_NOTICES.chromedriver instead of the
    binary. Find the actual chromedriver executable next to it (or one level up).'''
    if 'THIRD_PARTY_NOTICES' not in driver_path and driver_path.endswith('chromedriver'):
        return driver_path

    driver_dir = os.path.dirname(driver_path)
    for file in os.listdir(driver_dir):
        if file == 'chromedriver' or (file.startswith('chromedriver') and not file.endswith('.txt')):
            return _make_executable(os.path.join(driver_dir, file))

    # Sometimes it's in a sibling subdirectory
    for root, _dirs, files in os.walk(os.path.dirname(driver_dir)):
        if 'chromedriver' in files:
            return _make_executable(os.path.join(root, 'chromedriver'))

    return driver_path


def create_driver(headless: bool = True) -> webdriver.Chrome | None:
    '''Start Chrome (headless unless told otherwise), preferring a webdriver-manager
    chromedriver and falling back to the system one. Returns None (after printing hints)
    if both fail.'''
    # Disable unsightly webdriver-manager log messages
    os.environ['WDM_LOG_LEVEL'] = '0'
    os.environ['WDM_LOG'] = str(logging.NOTSET)
    logging.getLogger('WDM').setLevel(logging.NOTSET)

    chrome_options = _chrome_options(headless)

    try:
        driver_path = _resolve_chromedriver(ChromeDriverManager().install())
        return webdriver.Chrome(service=ChromeService(driver_path), options=chrome_options)
    except Exception as e:
        print(f"Error with ChromeDriverManager: {e}")
        print("Trying alternative approach...")

    # Use system chromedriver if available (installed via homebrew or manually)
    try:
        return webdriver.Chrome(options=chrome_options)
    except Exception as e:
        print(f"System chromedriver also failed: {e}")
        print("\nPlease try one of these solutions:")
        print("1. Install chromedriver manually:")
        print("   brew install chromedriver (on macOS)")
        print("   or download from https://chromedriver.chromium.org/")
        print("2. Clear the webdriver cache:")
        print("   rm -rf ~/.wdm/")
        print("3. Update your Chrome browser to the latest version")
        return None


def enable_downloads(driver: webdriver.Chrome, download_path: str) -> None:
    '''Allow headless Chrome to save downloads into download_path.'''
    driver.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')

    params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': download_path}}
    driver.execute("send_command", params)
