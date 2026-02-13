# filesystem_watcher.py - Monitors Inbox/ for new file drops
import time
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from base_watcher import BaseWatcher


class InboxHandler(FileSystemEventHandler):
    """Watchdog handler that collects new files dropped into Inbox/."""

    def __init__(self):
        self.pending_files = []

    def on_created(self, event):
        if not event.is_directory:
            self.pending_files.append(Path(event.src_path))


class FileSystemWatcher(BaseWatcher):
    def __init__(self, vault_path: str):
        super().__init__(vault_path, check_interval=5)
        self.inbox = self.vault_path / 'Inbox'
        self.inbox.mkdir(exist_ok=True)
        self.handler = InboxHandler()
        self.observer = Observer()
        self.observer.schedule(self.handler, str(self.inbox), recursive=False)
        self.observer.start()
        self.logger.info(f'Watching {self.inbox} for new files')

    def check_for_updates(self) -> list:
        """Return list of new files detected by watchdog."""
        items = list(self.handler.pending_files)
        self.handler.pending_files.clear()
        # Filter out files that no longer exist (moved/deleted quickly)
        return [f for f in items if f.exists()]

    def create_action_file(self, filepath: Path) -> Path:
        """Create a task file in Needs_Action/ for the dropped file."""
        stat = filepath.stat()
        now = datetime.now()
        safe_name = filepath.stem.replace(' ', '_')

        content = f'''---
type: file_drop
filename: {filepath.name}
source_path: {filepath}
size_bytes: {stat.st_size}
detected: {now.isoformat()}
priority: normal
status: pending
---

## File Drop Detected

**File:** `{filepath.name}`
**Size:** {stat.st_size:,} bytes
**Dropped:** {now.strftime('%Y-%m-%d %H:%M:%S')}

## Suggested Actions
- [ ] Review file contents
- [ ] Classify and route to appropriate workflow
- [ ] Archive or delete after processing
'''
        action_file = self.needs_action / f'FILE_{safe_name}_{now.strftime("%Y%m%d_%H%M%S")}.md'
        action_file.write_text(content, encoding='utf-8')
        self.logger.info(f'Created action file: {action_file.name} for {filepath.name}')
        return action_file

    def stop(self):
        """Stop the watchdog observer."""
        self.observer.stop()
        self.observer.join()
