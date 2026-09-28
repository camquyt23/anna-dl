"""Resolve the default download directory from config.json."""
import json
import os
from pathlib import Path

CONFIG_NAME = 'config.json'


def config_paths() -> list[Path]:
    '''Config files to check, in priority order: ./config.json, then the XDG config dir.'''
    xdg_config = os.environ.get('XDG_CONFIG_HOME') or Path.home() / '.config'
    return [Path.cwd() / CONFIG_NAME, Path(xdg_config) / 'anna-dl' / CONFIG_NAME]


def default_download_path() -> str:
    '''download_path from the first config file that sets it, otherwise ./assets.'''
    for path in config_paths():
        if not path.is_file():
            continue
        with open(path, 'r') as f:
            download_path = (json.load(f).get('download_path') or '').strip()
        if download_path:
            return download_path

    return str(Path.cwd() / 'assets')
