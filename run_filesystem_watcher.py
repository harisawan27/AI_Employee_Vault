# run_filesystem_watcher.py - Entry point for the File System Watcher
import sys
import logging
from pathlib import Path
from filesystem_watcher import FileSystemWatcher
from config import VAULT_PATH

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(VAULT_PATH / 'Logs' / 'filesystem_watcher.log')
    ]
)
logger = logging.getLogger('FileSystemWatcherRunner')


def main():
    logger.info('=== WEBXES Tech File System Watcher Starting ===')
    logger.info(f'Vault: {VAULT_PATH}')
    logger.info(f'Monitoring: {VAULT_PATH}/Inbox/')

    # Ensure folders exist
    for folder in ['Inbox', 'Needs_Action']:
        (VAULT_PATH / folder).mkdir(exist_ok=True)

    watcher = FileSystemWatcher(vault_path=str(VAULT_PATH))
    logger.info('File System Watcher is now running. Press Ctrl+C to stop.')

    try:
        watcher.run()
    except KeyboardInterrupt:
        logger.info('File System Watcher stopped by user.')
        watcher.stop()
    except Exception as e:
        logger.error(f'Fatal error: {e}', exc_info=True)
        watcher.stop()
        sys.exit(1)


if __name__ == '__main__':
    main()
