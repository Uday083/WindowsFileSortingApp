"""
File/folder mover module for AutoSort.
"""
import logging
import shutil
import time
from pathlib import Path
from typing import Optional
from .config import Config

logger = logging.getLogger(__name__)

def _wait_for_file_ready(path: Path, timeout: int = 10) -> bool:
    """
    Waits until a file's size stops changing, indicating it's ready.
    """
    if not path.exists():
        return False
        
    if path.is_dir():
        return True

    start_time = time.time()
    last_size = -1
    stable_count = 0
    
    while time.time() - start_time < timeout:
        try:
            current_size = path.stat().st_size
            if current_size == last_size:
                stable_count += 1
                if stable_count >= 2:
                    return True
            else:
                stable_count = 0
            last_size = current_size
        except Exception as e:
            logger.debug(f"Error checking size for {path}: {e}")
        time.sleep(0.5)
        
    logger.warning(f"Timeout waiting for file {path} to be ready.")
    return False

def _generate_unique_path(target: Path) -> Path:
    """
    Generates a unique path by appending ' (2)', ' (3)', etc., if the file already exists.
    """
    if not target.exists():
        return target

    directory = target.parent
    extension = target.suffix
    
    # Handle multiple dot extensions like .tar.gz
    if target.name.lower().endswith('.tar.gz'):
        stem = target.name[:-7]
        extension = '.tar.gz'
    elif target.name.lower().endswith('.tar.bz2'):
        stem = target.name[:-8]
        extension = '.tar.bz2'
    elif target.name.lower().endswith('.tar.xz'):
        stem = target.name[:-7]
        extension = '.tar.xz'
    else:
        stem = target.stem

    counter = 2
    while True:
        new_name = f"{stem} ({counter}){extension}"
        new_target = directory / new_name
        if not new_target.exists():
            return new_target
        counter += 1

def move_to_sorted(source: Path, category: str, config: Config) -> Optional[Path]:
    """
    Moves a file or directory to the sorted destination based on its category.
    """
    if not source.exists():
        logger.error(f"Source path {source} does not exist.")
        return None

    if source.is_file() and not _wait_for_file_ready(source):
        logger.error(f"Source file {source} is not ready for moving (might be still downloading).")
        return None

    try:
        dest_root = config.get_destination_root()
        date_folder = config.get_date_folder_name()
        
        target_dir = dest_root / category / date_folder
        target_dir.mkdir(parents=True, exist_ok=True)
        
        target_path = target_dir / source.name
        target_path = _generate_unique_path(target_path)
        
        logger.info(f"Moving '{source}' to '{target_path}'")
        shutil.move(str(source), str(target_path))
        
        return target_path
    except PermissionError as e:
        logger.error(f"Permission denied moving {source}: {e}")
    except FileNotFoundError as e:
        logger.error(f"File not found during move {source}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error moving {source}: {e}")
        
    return None
