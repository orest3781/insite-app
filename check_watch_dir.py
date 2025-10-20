from src.core.config import ConfigManager
from pathlib import Path
import os

config = ConfigManager(Path('.'))
watch_dir = config.get('watch_directory')

print(f'Watch directory: {watch_dir}')
print(f'Auto enqueue: {config.get("auto_enqueue_on_add")}')
print(f'Directory exists: {os.path.exists(watch_dir)}')

if os.path.exists(watch_dir):
    files = [f for f in os.listdir(watch_dir) if os.path.isfile(os.path.join(watch_dir, f))]
    print(f'Files in directory: {len(files)}')
    print('\nFirst 10 files:')
    for f in files[:10]:
        print(f'  {f}')
else:
    print(f'\n❌ Watch directory does not exist: {watch_dir}')
