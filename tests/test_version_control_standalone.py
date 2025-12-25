"""Standalone tests for the version control mtime logic."""

import time
import tempfile
import shutil
from pathlib import Path
from datetime import datetime


# Replicate the core mtime logic for testing
DEFAULT_SNAPSHOT_DIR = '.version_snapshots'


def save_snapshot_if_file_changed(source_file: str, snapshot_dir: str | None = None) -> Path | None:
    """Save a snapshot of the source file only if mtime has changed."""
    src_path = Path(source_file).resolve()

    if not src_path.exists():
        return None

    # Determine snapshot directory
    if snapshot_dir:
        snap_dir = Path(snapshot_dir).resolve()
    else:
        snap_dir = src_path.parent / DEFAULT_SNAPSHOT_DIR

    snap_dir.mkdir(parents=True, exist_ok=True)

    # Check mtime for changes
    try:
        mtime = src_path.stat().st_mtime
    except OSError:
        return None

    # Read last mtime from marker file
    mtime_file = snap_dir / '.last_mtime'
    last = 0.0
    if mtime_file.exists():
        try:
            last = float(mtime_file.read_text().strip())
        except (ValueError, OSError):
            last = 0.0

    # Stop if no changes
    if mtime == last:
        return None

    # Update marker file with current mtime
    mtime_file.write_text(str(mtime))

    stem = src_path.stem
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    existing = list(snap_dir.glob(f"{stem}_v*.py"))
    version = 0
    for f in existing:
        try:
            parts = f.stem.split('_v')
            if len(parts) >= 2:
                v = int(parts[1].split('_')[0])
                if v >= version:
                    version = v + 1
        except (ValueError, IndexError):
            pass

    filename = f"{stem}_v{version:04d}_{timestamp}.py"
    snapshot_path = snap_dir / filename

    snapshot_path.write_bytes(src_path.read_bytes())
    return snapshot_path


def test_mtime_marker_file():
    """Test .last_mtime marker file is created and used."""
    print("Testing .last_mtime marker file...")

    temp_dir = tempfile.mkdtemp()
    try:
        source_file = Path(temp_dir) / "test_source.py"
        source_file.write_text("# Initial\n")

        # First save should create marker file
        snapshot_path = save_snapshot_if_file_changed(str(source_file))
        assert snapshot_path is not None

        snap_dir = source_file.parent / DEFAULT_SNAPSHOT_DIR
        mtime_file = snap_dir / '.last_mtime'
        assert mtime_file.exists()
        print("  marker_file_created: PASSED")

        # Marker should contain the mtime
        stored_mtime = float(mtime_file.read_text().strip())
        actual_mtime = source_file.stat().st_mtime
        assert stored_mtime == actual_mtime
        print("  marker_contains_mtime: PASSED")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_no_change_returns_none():
    """Test that no change returns None (stops loop)."""
    print("\nTesting no change returns None...")

    temp_dir = tempfile.mkdtemp()
    try:
        source_file = Path(temp_dir) / "test_source.py"
        source_file.write_text("# Initial\n")

        # First save
        result1 = save_snapshot_if_file_changed(str(source_file))
        assert result1 is not None
        print("  first_save: PASSED")

        # Second save without change should return None
        result2 = save_snapshot_if_file_changed(str(source_file))
        assert result2 is None
        print("  no_change_returns_none: PASSED")

        # Third save without change should also return None
        result3 = save_snapshot_if_file_changed(str(source_file))
        assert result3 is None
        print("  repeated_no_change_returns_none: PASSED")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_change_detected_after_modification():
    """Test that changes are detected after file modification."""
    print("\nTesting change detection after modification...")

    temp_dir = tempfile.mkdtemp()
    try:
        source_file = Path(temp_dir) / "test_source.py"
        source_file.write_text("# Initial\n")

        # First save
        save_snapshot_if_file_changed(str(source_file))

        # No change
        result = save_snapshot_if_file_changed(str(source_file))
        assert result is None
        print("  no_change_detected: PASSED")

        # Modify file
        time.sleep(0.1)
        source_file.write_text("# Modified\n")

        # Should detect change now
        result = save_snapshot_if_file_changed(str(source_file))
        assert result is not None
        assert "v0001" in result.name
        print("  change_detected_after_modify: PASSED")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_snapshot_filename_format():
    """Test snapshot filename format."""
    print("\nTesting snapshot filename format...")

    temp_dir = tempfile.mkdtemp()
    try:
        source_file = Path(temp_dir) / "test_source.py"
        source_file.write_text("# test\n")

        snapshot_path = save_snapshot_if_file_changed(str(source_file))

        assert snapshot_path is not None
        filename = snapshot_path.name
        assert filename.startswith("test_source_v0000_")
        assert filename.endswith(".py")
        print("  filename_format: PASSED")

        # Content matches
        assert snapshot_path.read_text() == source_file.read_text()
        print("  content_matches: PASSED")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_nonexistent_file():
    """Test nonexistent file returns None."""
    print("\nTesting nonexistent file...")

    result = save_snapshot_if_file_changed("/nonexistent/path/file.py")
    assert result is None
    print("  returns_none: PASSED")


if __name__ == "__main__":
    test_mtime_marker_file()
    test_no_change_returns_none()
    test_change_detected_after_modification()
    test_snapshot_filename_format()
    test_nonexistent_file()

    print("\n" + "=" * 50)
    print("All tests passed!")
    print("=" * 50)
