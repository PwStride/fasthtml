"""Version control module using mtime-based change detection."""

from pathlib import Path
from datetime import datetime

from starlette.routing import WebSocketRoute
from fasthtml.basics import FastHTML, Script

__all__ = ["FastHTMLWithVersionControl"]

# Default snapshot directory name
DEFAULT_SNAPSHOT_DIR = '.version_snapshots'


def save_snapshot_if_file_changed(source_file: str, snapshot_dir: str | None = None) -> Path | None:
    """
    Save a snapshot of the source file only if mtime has changed.

    Uses a .last_mtime marker file on disk to track the last known mtime.

    Args:
        source_file: Path to the Python source file
        snapshot_dir: Optional custom snapshot directory

    Returns:
        Path to the saved snapshot, or None if no change or source doesn't exist
    """
    src_path = Path(source_file).resolve()

    if not src_path.exists():
        return None

    # Determine snapshot directory
    if snapshot_dir:
        snap_dir = Path(snapshot_dir).resolve()
    else:
        snap_dir = src_path.parent / DEFAULT_SNAPSHOT_DIR

    # Create snapshot directory if needed
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

    # Generate snapshot filename: {stem}_v{version}_{timestamp}.py
    stem = src_path.stem
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Find next version number
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

    # Copy the file content
    snapshot_path.write_bytes(src_path.read_bytes())

    print(f"[VersionControl] Saved: {filename}")
    return snapshot_path


def VersionControlJs(reload_attempts:int=20, reload_interval:int=1000, **kwargs):
    """JavaScript that connects to version control WebSocket."""
    src = """
    (() => {
        let attempts = 0;
        const connect = () => {
            const socket = new WebSocket(`ws://${window.location.host}/version-control`);
            socket.onopen = async() => {
                const res = await fetch(window.location.href);
                if (res.ok) {
                    attempts ? window.location.reload() : console.log('VersionControl connected');
                }};
            socket.onclose = () => {
                !attempts++ ? connect() : setTimeout(() => { connect() }, %d);
                if (attempts > %d) window.location.reload();
            }};
        connect();
    })();
    """
    return Script(src % (reload_interval, reload_attempts))


async def version_control_ws(websocket):
    """WebSocket endpoint for version control."""
    await websocket.accept()
    save_snapshot_if_file_changed(_ws_source_file, _ws_snapshot_dir)
    await websocket.close()


# Module-level config for WebSocket endpoint
_ws_source_file = None
_ws_snapshot_dir = None


class FastHTMLWithVersionControl(FastHTML):
    """
    `FastHTMLWithVersionControl` enables automatic version snapshots.

    Saves a versioned copy of the source file whenever changes are detected via mtime.
    Snapshots are stored in `.version_snapshots/` with naming: {filename}_v{version}_{timestamp}.py

    How does it work?
      - A WebSocket is created at `/version-control`
      - When the server reloads (file saved), mtime is checked
      - If mtime changed, a new snapshot is saved
      - uvicorn's --reload handles file watching automatically

    Usage:
        >>> from fasthtml.common import *
        >>> app = FastHTMLWithVersionControl(__file__)
        >>>
        >>> @app.route('/')
        >>> def index(): return 'Hello'
        >>>
        >>> serve()
    """

    def __init__(self, source_file: str, *args, snapshot_dir: str | None = None, **kwargs):
        global _ws_source_file, _ws_snapshot_dir

        self.source_file = str(Path(source_file).resolve())
        self.snapshot_dir = snapshot_dir

        # Set module-level config for WebSocket
        _ws_source_file = self.source_file
        _ws_snapshot_dir = snapshot_dir

        # Add version control JS and WebSocket route
        kwargs["hdrs"] = [*(kwargs.get("hdrs") or []), VersionControlJs(**kwargs)]
        kwargs["routes"] = [*(kwargs.get("routes") or []), WebSocketRoute("/version-control", endpoint=version_control_ws)]
        super().__init__(*args, **kwargs)

        # Save initial snapshot
        snap_path = save_snapshot_if_file_changed(self.source_file, self.snapshot_dir)
        if snap_path:
            print(f"[VersionControl] Monitoring: {self.source_file}")
            print(f"[VersionControl] Snapshots: {snap_path.parent}")
