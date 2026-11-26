"""
Main entry point for AutoSort.
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from autosort.config import Config
from autosort.watcher import AutoSortWatcher
from autosort.tray import AutoSortTray


def setup_logging():
    """Sets up application logging."""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    if sys.platform == 'win32':
        app_data = os.getenv('APPDATA', os.path.expanduser('~'))
    else:
        app_data = os.path.expanduser('~/.config')
        
    app_dir = os.path.join(app_data, 'AutoSort')
    os.makedirs(app_dir, exist_ok=True)
    log_file = os.path.join(app_dir, 'autosort.log')

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)
    file_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(console_handler)

def main():
    """Application entry point."""
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        config = Config()

        # Pre-create destination folder structure
        dest_root = config.get_destination_root()
        dest_root.mkdir(parents=True, exist_ok=True)

        from autosort.classifier import CATEGORY_MAP
        categories = list(CATEGORY_MAP.keys()) + ['Others']
        for category in categories:
            (dest_root / category).mkdir(parents=True, exist_ok=True)

        watcher = AutoSortWatcher(config)
        watcher.start()

        # Sort existing files in watched folders on startup
        if config.sort_existing_on_startup:
            logger.info("Sorting existing files on startup...")
            count = watcher.sort_existing()
            logger.info(f"Startup sort complete: {count} files sorted")

        tray = AutoSortTray(watcher, config)
        logger.info("Starting AutoSort tray application...")
        tray.run()

    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt, stopping...")
        if 'watcher' in locals():
            watcher.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
