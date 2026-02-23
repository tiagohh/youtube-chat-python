from pathlib import Path
import glob

print('Updating CSV headers to uppercase for all chat*.csv')
for p in glob.glob('chat*.csv'):
    path = Path(p)
    text = path.read_text(encoding='utf-8-sig')
    lines = text.splitlines()
    if not lines:
        continue
    # determine delimiter from first line
    first = lines[0]
    if ';' in first:
        delim=';'
    elif ',' in first:
        delim=','
    else:
        delim=';'
    header = f'AUTHOR{delim}MESSAGE'
    if lines[0].strip() != header:
        lines[0] = header
        path.write_text('\n'.join(lines), encoding='utf-8-sig')
        print('Patched', path)
    else:
        print('Already ok', path)
