"""CPKから指定パターンに合うエントリを展開する。
使い方: python cpk_extract.py <cpk> <出力先> <正規表現> [...]
CRILAYLA圧縮は crila.py で自動展開。パスの階層はそのまま維持する。
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cpk, crila

def main():
    path, outdir, pats = sys.argv[1], sys.argv[2], [re.compile(p, re.I) for p in sys.argv[3:]]
    hdr, rows, toc_off, content_off, f = cpk.toc(path)
    base = toc_off if content_off is None or toc_off < content_off else content_off
    n = 0
    for r in rows:
        name = f"{r['DirName']}/{r['FileName']}"
        if not any(p.search(name) for p in pats):
            continue
        f.seek(r['FileOffset'] + base)
        raw = f.read(r['FileSize'])
        data = crila.decompress(raw)
        if len(data) != r['ExtractSize']:
            print(f"SIZE MISMATCH {name}: {len(data)} != {r['ExtractSize']}", file=sys.stderr)
        dst = os.path.join(outdir, *name.split('/'))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, 'wb') as o:
            o.write(data)
        n += 1
        print(f"{len(data):>9} {name}")
    print(f"{n} files")

main()
