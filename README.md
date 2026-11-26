# AutoSort

AutoSort is a Windows-friendly Python application that watches selected folders and moves newly created or moved files into category folders organized by date.

## Features

- Watches Desktop and Downloads folders by default.
- Classifies files into Images, Videos, Audio, Documents, Code, Executables, and Others.
- Creates dated category folders.
- Pauses or resumes file processing from the system tray.
- Sorts existing files on demand.
- Avoids system, temporary, hidden, and development files.
- Does not register itself to run automatically with Windows.

## Requirements

- Python 3.9 or newer
- Windows 10 or newer for the bundled Windows executable

## Run from Source

```powershell
python -m pip install -r requirements.txt
python -m autosort.main
```

The application runs in the system tray. Use the tray menu to pause, sort existing files, open the destination folder, or quit.

## Build a Portable Executable

Run the following command from PowerShell:

```powershell
.\build.bat
```

The generated single-file executable is written to:

```text
dist\AutoSort.exe
```

The executable contains the application dependencies. The target computer does not need Python or the application packages installed.

## Configuration

Configuration is stored in `%APPDATA%\AutoSort\config.json`.

The default destination is `%USERPROFILE%\AutoSorted`. The application creates category subfolders when it starts.

## Project Structure

```text
autosort/       Application source
assets/          Application icon
build.bat       Windows portable-executable build script
dist/            Generated executable
tests/           Automated tests
requirements.txt Runtime dependencies
```

## Development

Run the automated tests with:

```powershell
python -m unittest discover -s tests -v
```

## Next Tasks

1. To test the performance of movement of the file from pen drive to PC with this app vs default file movement speed.

## License

AutoSort is distributed under the MIT License.
