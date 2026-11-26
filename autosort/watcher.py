"""
File system watcher module for AutoSort.

Uses watchdog to monitor directories in real-time and trigger
file classification and sorting.
"""
import logging
import threading
from pathlib import Path
from typing import Dict

from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEventHandler,
    FileSystemEvent,
    FileCreatedEvent,
    DirCreatedEvent,
    FileMovedEvent,
    DirMovedEvent,
)

from autosort.classifier import classify
from autosort.excluder import should_exclude
from autosort.mover import move_to_sorted
from autosort.config import Config

logger = logging.getLogger(__name__)


class SortHandler(FileSystemEventHandler):
    """Event handler for file system changes."""

    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self._timers: Dict[str, threading.Timer] = {}
        self.is_paused = True

    def _process_path(self, raw_path: str):
        """Processes a file path after the stabilization delay."""
        # Remove timer from dict
        self._timers.pop(raw_path, None)

        if self.is_paused:
            logger.debug(f"Skipping {raw_path} (paused)")
            return

        path = Path(raw_path)

        if not path.exists():
            logger.debug(f"Skipping {path} (no longer exists)")
            return

        if should_exclude(path, self.config):
            logger.debug(f"Skipping {path} (excluded)")
            return

        try:
            category = classify(path)
            move_to_sorted(path, category, self.config)
        except Exception as e:
            logger.error(f"Error processing {path}: {e}")

    def _schedule_processing(self, raw_path: str):
        """Schedules file processing with a debounce timer."""
        if self.is_paused:
            return

        path = Path(raw_path)

        if should_exclude(path, self.config):
            return

        # Cancel existing timer if any (debounce rapid events)
        if raw_path in self._timers:
            self._timers[raw_path].cancel()

        delay = self.config._config.get(
            'stabilization_delay_seconds', 2.0
        )

        timer = threading.Timer(delay, self._process_path, args=[raw_path])
        self._timers[raw_path] = timer
        timer.start()
        logger.debug(f"Scheduled processing for {path} in {delay}s")

    def on_created(self, event: FileSystemEvent):
        """Called when a file or directory is created."""
        # Process both files AND directories (folders should be sorted too)
        self._schedule_processing(event.src_path)

    def on_moved(self, event: FileSystemEvent):
        """Called when a file or directory is moved or renamed."""
        # Process both files AND directories
        self._schedule_processing(event.dest_path)


class AutoSortWatcher:
    """Manages directory observers."""

    def __init__(self, config: Config):
        self.config = config
        self.observers: list[Observer] = []
        self.handler = SortHandler(config)
        self._is_running = False

    @property
    def is_running(self) -> bool:
        return self._is_running

    def start(self):
        """Starts watching configured folders."""
        if self._is_running:
            return

        for folder in self.config.get_watched_folders():
            if not folder.exists():
                logger.warning(f"Watched folder does not exist: {folder}")
                continue

            observer = Observer()
            observer.schedule(self.handler, str(folder), recursive=False)
            self.observers.append(observer)
            observer.start()
            logger.info(f"Started watching: {folder}")

        self._is_running = True
        logger.info("AutoSort watcher started")

    def stop(self):
        """Stops all observers."""
        if not self._is_running:
            return

        for observer in self.observers:
            observer.stop()
            
        for observer in self.observers:
            observer.join()
            
        self.observers.clear()
        
        # Cancel pending timers
        for path, timer in list(self.handler._timers.items()):
            timer.cancel()
        self.handler._timers.clear()

        self._is_running = False
        logger.info("AutoSort watcher stopped")

    def pause(self):
        """Pauses file processing."""
        self.handler.is_paused = True
        logger.info("AutoSort watcher paused")

    def resume(self):
        """Resumes file processing."""
        self.handler.is_paused = False
        logger.info("AutoSort watcher resumed")

    def sort_existing(self):
        """Scans all watched folders and sorts existing files/directories."""
        logger.info("Sorting existing files in watched folders...")
        sorted_count = 0
        skipped_count = 0

        for folder in self.config.get_watched_folders():
            if not folder.exists():
                logger.warning(f"Watched folder does not exist: {folder}")
                continue

            logger.info(f"Scanning existing files in: {folder}")
            try:
                for item in folder.iterdir():
                    if self.handler.is_paused:
                        logger.info("Sorting paused, stopping existing file scan")
                        return sorted_count

                    if should_exclude(item, self.config):
                        logger.debug(f"Skipping excluded item: {item}")
                        skipped_count += 1
                        continue

                    try:
                        category = classify(item)
                        result = move_to_sorted(item, category, self.config)
                        if result:
                            sorted_count += 1
                            logger.info(f"Sorted existing: '{item.name}' -> {category}")
                        else:
                            skipped_count += 1
                    except Exception as e:
                        logger.error(f"Error sorting existing item {item}: {e}")
                        skipped_count += 1

            except PermissionError as e:
                logger.error(f"Permission denied scanning {folder}: {e}")
            except Exception as e:
                logger.error(f"Error scanning {folder}: {e}")

        logger.info(f"Existing file sort complete: {sorted_count} sorted, {skipped_count} skipped")
        return sorted_count
