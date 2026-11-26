import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from autosort.classifier import classify
from autosort.config import Config
from autosort.excluder import should_exclude
from autosort.mover import move_to_sorted


class ClassifierTests(unittest.TestCase):
    def test_classifies_supported_file_types(self):
        self.assertEqual(classify(Path("photo.JPG")), "Images")
        self.assertEqual(classify(Path("movie.MKV")), "Videos")
        self.assertEqual(classify(Path("song.mp3")), "Audio")
        self.assertEqual(classify(Path("report.pdf")), "Documents")
        self.assertEqual(classify(Path("program.py")), "Code")
        self.assertEqual(classify(Path("installer.exe")), "Executables")
        self.assertEqual(classify(Path("unknown.xyz")), "Others")

    def test_classifies_directories_as_documents(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            self.assertEqual(classify(Path(temp_dir)), "Documents")


class ExcluderTests(unittest.TestCase):
    def test_excludes_configured_extensions_and_filenames(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            destination = Path(temp_dir) / "AutoSorted"
            config = Config()
            config._config.update(
                {
                    "destination_root": str(destination),
                    "excluded_extensions": [".tmp"],
                    "excluded_filenames": ["desktop.ini"],
                }
            )

            self.assertTrue(should_exclude(Path(temp_dir) / "file.tmp", config))
            self.assertTrue(should_exclude(Path(temp_dir) / "desktop.ini", config))
            self.assertFalse(should_exclude(Path(temp_dir) / "file.txt", config))

    def test_excludes_files_inside_destination_root(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "AutoSorted"
            destination.mkdir()
            config = Config()
            config._config["destination_root"] = str(destination)

            self.assertTrue(should_exclude(destination / "file.txt", config))


class ConfigTests(unittest.TestCase):
    def test_loads_configuration_from_appdata(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "AutoSort" / "config.json"
            config_path.parent.mkdir()
            config_path.write_text(
                json.dumps({"destination_root": str(Path(temp_dir) / "Sorted")}),
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"APPDATA": temp_dir}, clear=False):
                config = Config()

            self.assertEqual(config.get_destination_root(), Path(temp_dir) / "Sorted")


class MoverTests(unittest.TestCase):
    def test_moves_file_to_category_and_date_folder(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            destination = Path(temp_dir) / "Sorted"
            source_dir.mkdir()
            source = source_dir / "photo.jpg"
            source.write_bytes(b"image data")

            config = Config()
            config._config["destination_root"] = str(destination)
            moved = move_to_sorted(source, "Images", config)

            self.assertIsNotNone(moved)
            self.assertTrue(moved.exists())
            self.assertEqual(moved.parent.name, config.get_date_folder_name())
            self.assertEqual(moved.parent.parent.name, "Images")
            self.assertFalse(source.exists())


if __name__ == "__main__":
    unittest.main()
