"""Settings from config.json: download directory and Anna's Archive mirrors."""
import json
import os
from importlib.resources import files
from pathlib import Path

CONFIG_NAME = 'config.json'


def config_paths() -> list[Path]:
    '''User config files to check, in priority order: ./config.json, then the XDG config dir.'''
    xdg_config = os.environ.get('XDG_CONFIG_HOME') or Path.home() / '.config'
    return [Path.cwd() / CONFIG_NAME, Path(xdg_config) / 'anna-dl' / CONFIG_NAME]


def _get_setting(key: str):
    '''key from the first config file that sets it (non-empty), falling back to the
    defaults.json shipped with the package.'''
    for path in [*config_paths(), files('anna_dl') / 'defaults.json']:
        if not path.is_file():
            continue
        value = json.loads(path.read_text()).get(key)
        if isinstance(value, str):
            value = value.strip()
        if value:
            return value
    return None


def default_download_path() -> str:
    '''download_path from config, otherwise ./assets.'''
    return _get_setting('download_path') or str(Path.cwd() / 'assets')


def configured_mirrors() -> list[str]:
    '''Anna's Archive base URLs to try, in order. Domains change often, so they live in
    config ("mirrors": a list or a single URL) rather than in code.'''
    mirrors = _get_setting('mirrors') or []
    if isinstance(mirrors, str):
        mirrors = [mirrors]
    return [url.strip() for url in mirrors if url.strip()]
