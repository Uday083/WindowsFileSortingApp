"""
Configuration management module for AutoSort.
"""
import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

DEFAULT_CONFIG: Dict[str, Any] = {
    'watched_folders': ['~/Desktop', '~/Downloads'],
    'destination_root': '~/AutoSorted',
    'date_format': '%Y-%m-%d',
    'stabilization_delay_seconds': 2,
    'sort_existing_on_startup': True,
    'excluded_extensions': ['.tmp', '.crdownload', '.part', '.partial', '.download'],
    'excluded_filenames': ['desktop.ini', 'thumbs.db', 'Thumbs.db']
}

class Config:
    def __init__(self):
        self._config = DEFAULT_CONFIG.copy()
        
        # Determine config path
        appdata = os.environ.get('APPDATA')
        if appdata:
            self.config_dir = Path(appdata) / 'AutoSort'
        else:
            self.config_dir = Path.home() / '.config' / 'AutoSort'
            
        self.config_path = self.config_dir / 'config.json'
        self.load()

    def load(self) -> None:
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                    self._config.update(user_config)
                logger.info(f"Loaded config from {self.config_path}")
            except Exception as e:
                logger.error(f"Failed to load config from {self.config_path}: {e}. Using defaults.")
        else:
            logger.info("Config file not found, using default configuration.")

    def save(self) -> None:
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self._config, f, indent=4)
            logger.info(f"Saved config to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save config to {self.config_path}: {e}")

    @property
    def excluded_extensions(self) -> List[str]:
        return self._config.get('excluded_extensions', DEFAULT_CONFIG['excluded_extensions'])

    @property
    def excluded_filenames(self) -> List[str]:
        return self._config.get('excluded_filenames', DEFAULT_CONFIG['excluded_filenames'])

    def get_watched_folders(self) -> List[Path]:
        """Return the list of folders to watch, handling OneDrive Desktop fallback.
        The default config uses '~/Desktop' which may not exist if the user
        syncs Desktop via OneDrive. In that case we fall back to the actual
        Desktop location retrieved from the Windows Shell special folder.
        """
        raw_folders = self._config.get('watched_folders', DEFAULT_CONFIG['watched_folders'])
        resolved = []
        for f in raw_folders:
            expanded = Path(os.path.expanduser(f)).resolve()
            if expanded.exists():
                resolved.append(expanded)
                continue
            # Fallback for Desktop when using OneDrive
            if f.lower().endswith('desktop'):
                # Try OneDrive Desktop
                onedrive = os.getenv('ONEDRIVE')
                if onedrive:
                    alt = Path(onedrive) / 'Desktop'
                    if alt.exists():
                        resolved.append(alt.resolve())
                        continue
                # Fallback to known special folder via shell
                try:
                    from ctypes import windll, wintypes, create_unicode_buffer
                    CSIDL_DESKTOP = 0x0000
                    SHGFP_TYPE_CURRENT = 0
                    buf = create_unicode_buffer(wintypes.MAX_PATH)
                    if windll.shell32.SHGetFolderPathW(0, CSIDL_DESKTOP, 0, SHGFP_TYPE_CURRENT, buf) == 0:
                        special_path = Path(buf.value)
                        if special_path.exists():
                            resolved.append(special_path)
                            continue
                except Exception:
                    pass
            # If we reach here, keep the expanded path (may not exist yet)
            resolved.append(expanded)
        return resolved


    def get_destination_root(self) -> Path:
        dest = self._config.get('destination_root', DEFAULT_CONFIG['destination_root'])
        return Path(os.path.expanduser(dest)).resolve()

    def get_date_folder_name(self) -> str:
        from datetime import datetime
        fmt = self._config.get('date_format', DEFAULT_CONFIG['date_format'])
        return datetime.now().strftime(fmt)

    @property
    def sort_existing_on_startup(self) -> bool:
        return self._config.get('sort_existing_on_startup', True)
