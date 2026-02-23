import csv
import shutil
from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = root / 'chat.csv'
bak = root / 'chat.csv.bak'

if not src.exists():
    print('chat.csv not found')
    raise SystemExit(1)

shutil.copy2(src, bak)
print(f'Backup written to {bak}')

# read original as comma-delimited (most exports are comma)
with open(bak, 'r', encoding='utf-8-sig', newline='') as fr:
    reader = csv.reader(fr, delimiter=',')
    rows = list(reader)

# write semicolon-delimited with UTF-8 BOM so Excel recognizes encoding
with open(src, 'w', encoding='utf-8-sig', newline='') as fw:
    writer = csv.writer(fw, delimiter=';')
    writer.writerows(rows)

print('Conversion complete: chat.csv is now semicolon-delimited')
