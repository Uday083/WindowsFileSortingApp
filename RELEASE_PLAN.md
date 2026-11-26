# AutoSort Executable Release Plan

## Goal

Produce a reproducible, reviewable release of the Windows `AutoSort.exe` binary. The release must be identifiable by a Git tag, immutable source revision, build metadata, and SHA-256 checksum.

## Current Repository State

- The application version is defined as `1.0.0` in `autosort/__init__.py`.
- The tray displays a separate hard-coded `AutoSort v1.0.0` label in `autosort/tray.py`.
- The portable build script writes `dist/AutoSort.exe`.
- `dist/` is currently ignored by `.gitignore`.
- The generated executable is not automatically committed to Git.

For future releases, keep the source version and displayed version synchronized. Prefer a single version source so the application, build metadata, and release tag cannot drift.

## Release Workflow

### 1. Prepare the release branch

1. Create a release branch or use the default branch.
2. Update the version to the intended semantic version, for example `1.1.0`.
3. Update every user-visible version reference, including the application version and tray label.
4. Add or update release notes for the new version.
5. Commit the version and release-note changes.
6. Confirm that the working tree is clean.

Example version updates:

```powershell
git switch -c release/v1.1.0
# Update autosort/__init__.py and autosort/tray.py
# Update RELEASE_NOTES.md if applicable
git add autosort/__init__.py autosort/tray.py
git commit -m "Release v1.1.0"
```

### 2. Validate the source before building

Run the full validation sequence from the repository root:

```powershell
python -m unittest discover -s tests -v
python -m compileall -q autosort tests
.\build.bat
```

The build must:

- Exit with code `0`.
- Create `dist/AutoSort.exe`.
- Generate no unreviewed source changes.
- Produce the expected version in the executable.

### 3. Create an immutable release tag

After tests and the build succeed, create and push a tag matching the release version:

```powershell
git tag -a v1.1.0 -m "AutoSort v1.1.0"
git push origin release/v1.1.0
git push origin v1.1.0
```

The tag must point exactly at the release commit. Do not move or recreate tags after publishing.

### 4. Build the final executable from the tagged commit

The final build should be performed from the tagged revision on a clean checkout, rather than from an uncommitted working tree:

```powershell
git checkout v1.1.0
git clean -fdx
python -m unittest discover -s tests -v
.\build.bat
```

The command must not include local developer files, temporary configuration, or generated test artifacts.

### 5. Verify the binary

Verify the executable metadata and hash:

```powershell
Get-Item .\dist\AutoSort.exe |
    Select-Object FullName, Length, LastWriteTime

Get-FileHash .\dist\AutoSort.exe -Algorithm SHA256 |
    Select-Object Path, Hash
```

Confirm that:

- The executable exists at `dist/AutoSort.exe`.
- The file is not empty and has a current timestamp.
- The SHA-256 hash is recorded in the release notes.
- The displayed application version matches the tag.
- The binary runs on a Windows test machine.

### 6. Publish the release

Create a GitHub Release for the tag and attach the following files:

- `AutoSort.exe`
- `AutoSort.exe.sha256`
- Optional `RELEASE_NOTES.md`

Recommended checksum content:

```text
AutoSort.exe SHA-256: <hash>
```

The GitHub Release should contain:

1. A short description of the release.
2. The release version and source tag.
3. The SHA-256 checksum.
4. The supported Windows versions.
5. Known limitations or compatibility notes.

### 7. Preserve evidence

For every release, retain:

- The git commit SHA.
- The release tag.
- The build date and build environment.
- The PyInstaller version.
- The Python version.
- The SHA-256 hash.
- The release notes.

This information enables a user or maintainer to reproduce and identify the exact executable version.

## Recommended Artifact Policy

- Commit source code, tests, build scripts, documentation, and release notes.
- Do not commit generated `dist/` or `build/` files to normal branches.
- Publish the final executable as an immutable GitHub Release asset.
- Treat the tag and release asset as the authoritative versioned product.
- Rebuild and republish the same tagged source only when the release is intentionally replaced; otherwise preserve the original release asset.

## Suggested release checklist

- [ ] Version matches the intended semantic version.
- [ ] Tray display matches the application version.
- [ ] Tests pass.
- [ ] Source compilation succeeds.
- [ ] Clean tagged checkout is used for the build.
- [ ] `dist/AutoSort.exe` exists.
- [ ] The executable was tested on Windows.
- [ ] SHA-256 checksum was calculated and recorded.
- [ ] Git tag points to the exact release commit.
- [ ] GitHub Release was published.
- [ ] Release asset and source tag have matching versions.
- [ ] Release notes describe the change and compatibility.

## Rollback

If a release fails:

1. Remove or retract the affected GitHub Release if it has not been distributed.
2. Delete or replace the release tag only when no consumers have already downloaded it.
3. Rebuild from the previous known-good commit.
4. Publish a new versioned tag and Release; do not alter an already published tag.

## Future Improvements

- Centralize the version in one source of truth.
- Add an automated build and release test.
- Store the PyInstaller/Python build versions in release metadata.
- Add a checksum verification step before publishing.
- Add a release manifest containing the commit, tag, binary hash, and build tool versions.
- Consider signing the executable with a code-signing certificate before distribution.
