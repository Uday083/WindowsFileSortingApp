"""
Exclusion rules module for AutoSort.
"""
import logging
import sys
from pathlib import Path
from .config import Config

logger = logging.getLogger(__name__)

def has_hidden_attribute(path: Path) -> bool:
    """Check if file has Windows hidden attribute."""
    if sys.platform != 'win32':
        return False
    try:
        import ctypes
        FILE_ATTRIBUTE_HIDDEN = 0x02
        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
        if attrs != -1 and (attrs & FILE_ATTRIBUTE_HIDDEN):
            return True
    except Exception as e:
        logger.debug(f"Failed to get hidden attribute for {path}: {e}")
    return False

def should_exclude(path: Path, config: Config) -> bool:
    """
    Check if a path should be excluded from sorting.
    Returns True if the path should be excluded, False otherwise.
    """
    # 1. Path is inside the destination root
    try:
        dest_root = config.get_destination_root()
        if dest_root in path.resolve().parents or path.resolve() == dest_root:
            logger.debug(f"Excluded '{path}': inside destination root")
            return True
    except Exception as e:
        logger.error(f"Error checking destination root for {path}: {e}")

    # 2. Filename starts with '$' or '~$'
    if path.name.startswith('$') or path.name.startswith('~$'):
        logger.debug(f"Excluded '{path}': starts with $ or ~$")
        return True

    # 3. Filename is in config.excluded_filenames (case-insensitive)
    if path.name.lower() in [f.lower() for f in config.excluded_filenames]:
        logger.debug(f"Excluded '{path}': matches excluded filename")
        return True

    # 4. Extension is in config.excluded_extensions (case-insensitive)
    if path.suffix.lower() in [e.lower() for e in config.excluded_extensions]:
        logger.debug(f"Excluded '{path}': matches excluded extension")
        return True

    # 5. File has Windows hidden attribute
    if has_hidden_attribute(path):
        logger.debug(f"Excluded '{path}': hidden file")
        return True

    # 6. Path contains restricted segments
    restricted_segments = {'program files', 'program files (x86)', 'windows', 'appdata', 'programdata', '$recycle.bin'}
    path_parts = {part.lower() for part in path.parts}
    if path_parts & restricted_segments:
        logger.debug(f"Excluded '{path}': contains restricted path segment")
        return True

    # 7. Directory contains repo/dev markers
    if path.is_dir():
        dev_markers = {'.git', '.svn', '.hg', 'node_modules', '.vscode', '.idea', '__pycache__', '.vs', '.gradle'}
        try:
            for item in path.iterdir():
                if item.name in dev_markers:
                    logger.debug(f"Excluded '{path}': appears to be a dev repository ({item.name})")
                    return True
        except PermissionError:
            pass
        except Exception as e:
            logger.debug(f"Error reading directory {path}: {e}")

    # 8. Filename matches common installer patterns (only for exe/msi)
    # NOTE: This rule is intentionally disabled. It was too aggressive —
    # files like "ChromeSetup.exe" placed deliberately in a watched folder
    # would be silently skipped. Users control exclusions via the Settings GUI.
    #
    # installer_patterns = {'setup', 'install', 'uninstall'}
    # if path.suffix.lower() in {'.exe', '.msi'}:
    #     stem_lower = path.stem.lower()
    #     if any(pattern in stem_lower for pattern in installer_patterns):
    #         return True

    return False
