import csv
import sys
from pathlib import Path

if len(sys.argv) < 2:
    print('Usage: python convert_to_semicolon.py <file.csv>')
    raise SystemExit(1)

p = Path(sys.argv[1])
if not p.exists():
    print('File not found:', p)
    raise SystemExit(1)

bak = p.with_suffix(p.suffix + '.bak')
if not bak.exists():
    p.replace(bak)
else:
    # if backup exists, overwrite original with backup contents for conversion
    p.unlink()
    bak.replace(p)

# Read as comma-delimited and write back as semicolon with BOM
with open(bak, 'r', encoding='utf-8-sig', newline='') as fr:
    reader = csv.reader(fr, delimiter=',')
    rows = list(reader)

with open(p, 'w', encoding='utf-8-sig', newline='') as fw:
    writer = csv.writer(fw, delimiter=';')
    writer.writerows(rows)

print('Converted', p, '-> semicolon-delimited (backup at', bak, ')')
