"""
File type classification module for AutoSort.
"""
import logging
from pathlib import Path
from typing import Dict, Set

logger = logging.getLogger(__name__)

CATEGORY_MAP: Dict[str, Set[str]] = {
    'Images': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico', '.tiff', '.tif', '.raw', '.heic', '.heif'},
    'Videos': {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg'},
    'Audio': {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.opus'},
    'Documents': {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf', '.odt', '.ods', '.odp', '.csv', '.epub', '.pages', '.numbers', '.key'},
    'Code': {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.hpp', '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.html', '.css', '.scss', '.less', '.json', '.xml', '.yaml', '.yml', '.md', '.sql', '.r', '.m', '.ipynb', '.sh', '.bat', '.ps1', '.cmd'},
    'Executables': {'.exe', '.msi', '.appimage', '.deb', '.rpm', '.dmg', '.app'}
}

ARCHIVE_EXTENSIONS: Set[str] = {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.tar.gz', '.tar.bz2', '.tar.xz'}

# Reverse lookup dictionary: extension -> category
EXTENSION_TO_CATEGORY: Dict[str, str] = {}
for category, exts in CATEGORY_MAP.items():
    for ext in exts:
        EXTENSION_TO_CATEGORY[ext] = category

def classify(path: Path) -> str:
    """
    Classifies a file or directory into a category based on its extension or properties.
    """
    if path.is_dir():
        logger.debug(f"Classified directory '{path}' as 'Documents'")
        return 'Documents'
        
    ext = path.suffix.lower()
    if path.name.lower().endswith('.tar.gz'):
        ext = '.tar.gz'
    elif path.name.lower().endswith('.tar.bz2'):
        ext = '.tar.bz2'
    elif path.name.lower().endswith('.tar.xz'):
        ext = '.tar.xz'

    if ext in ARCHIVE_EXTENSIONS:
        logger.debug(f"Classified archive '{path}' as 'Documents'")
        return 'Documents'

    category = EXTENSION_TO_CATEGORY.get(ext)
    if category:
        logger.debug(f"Classified file '{path}' as '{category}'")
        return category

    logger.debug(f"Classified file '{path}' as 'Others'")
    return 'Others'
