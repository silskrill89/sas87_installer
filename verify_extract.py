import sys
sys.path.insert(0, '.')
from src import extractor, cache
import os, shutil

rar = r'C:\Users\aaaaaa\Downloads\GTA SAS july 2026.rar'
dest = os.path.join(cache.CACHE_EXTRACTED, 'verify_test')
os.makedirs(dest, exist_ok=True)
extractor.extract(rar, dest)
count = sum(len(files) for _, _, files in os.walk(dest))
print(f'Extracted {count} files')

key_files = ['gta_sa.exe', 'data', 'models', 'audio', 'text']
for kf in key_files:
    path = os.path.join(dest, kf)
    status = 'EXISTS' if os.path.exists(path) else 'MISSING'
    print(f'  {kf}: {status}')

shutil.rmtree(dest, ignore_errors=True)
print('Verification complete!')
