"""
System tray module for AutoSort.
"""
import logging
import os
import sys
import subprocess
from typing import Optional

import pystray
from PIL import Image, ImageDraw

from autosort.watcher import AutoSortWatcher
from autosort.config import Config

logger = logging.getLogger(__name__)

IS_WINDOWS = sys.platform == 'win32'


class AutoSortTray:
    """System tray application for AutoSort."""
    
    def __init__(self, watcher: AutoSortWatcher, config: Config):
        self.watcher = watcher
        self.config = config
        self.icon: Optional[pystray.Icon] = None
        
    def _create_image(self) -> Image.Image:
        """Creates a simple 64x64 folder icon."""
        width = 64
        height = 64
        
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        folder_color = (76, 175, 80, 255)  # Green
        
        # Draw tab
        draw.rectangle([8, 12, 28, 20], fill=folder_color)
        # Draw body
        draw.rectangle([8, 20, 56, 52], fill=folder_color)
        
        return image

    def _toggle_pause(self, icon: pystray.Icon, item: pystray.MenuItem):
        if self.watcher.handler.is_paused:
            self.watcher.resume()
        else:
            self.watcher.pause()
            
    def _open_destination(self, icon: pystray.Icon, item: pystray.MenuItem):
        dest = str(self.config.get_destination_root())
        if not os.path.exists(dest):
            logger.warning(f"Destination root does not exist: {dest}")
            return
            
        try:
            if IS_WINDOWS:
                os.startfile(dest)
            elif sys.platform == 'darwin':
                subprocess.call(['open', dest])
            else:
                subprocess.call(['xdg-open', dest])
        except Exception as e:
            logger.error(f"Failed to open destination folder: {e}")

    def _quit(self, icon: pystray.Icon, item: pystray.MenuItem):
        self.watcher.stop()
        icon.stop()

    def _sort_existing(self, icon: pystray.Icon, item: pystray.MenuItem):
        """Triggers sorting of existing files in watched folders."""
        import threading
        def _run():
            logger.info("Manual sort of existing files triggered from tray")
            count = self.watcher.sort_existing()
            logger.info(f"Manual sort complete: {count} files sorted")
            # Notify the user with a balloon so they know it finished
            try:
                if count > 0:
                    msg = f"{count} file{'s' if count != 1 else ''} sorted successfully."
                else:
                    msg = "No files to sort (all files already sorted or excluded)."
                icon.notify(msg, 'AutoSort — Sort Complete')
            except Exception:
                pass  # notify() not supported on all platforms
        threading.Thread(target=_run, daemon=True).start()

    def run(self):
        """Runs the system tray icon (blocking)."""
        menu_items = [
            pystray.MenuItem('AutoSort v1.0.0', lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                lambda text: 'Resume' if self.watcher.handler.is_paused else 'Pause',
                self._toggle_pause
            ),
            pystray.MenuItem('Sort Existing Files Now', self._sort_existing),
            pystray.MenuItem('Open AutoSorted Folder', self._open_destination),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Quit', self._quit),
        ]

        self.icon = pystray.Icon(
            'AutoSort',
            self._create_image(),
            title='AutoSort',
            menu=pystray.Menu(*menu_items)
        )

        def _on_ready(icon):
            """Called by pystray once the icon is actually painted in the tray."""
            icon.visible = True
            try:
                icon.notify(
                    'AutoSort is running.\nRight-click this icon to Pause or Quit.',
                    'AutoSort'
                )
            except Exception:
                pass  # some platforms/pystray versions don't support notify()

        try:
            self.icon.run(setup=_on_ready)
        except Exception as e:
            logger.error(f"Tray icon error: {e}", exc_info=True)
            self.watcher.stop()

