#!/usr/bin/env python3
"""ビルドした .uf2 を GitHub Pages（docs/firmware）に置き、版の情報を latest.json に書く。

使い方: publish_fw.py <artifact のフォルダ> <出力先フォルダ> <コミット SHA>
版は、ファームウェアに埋め込んだ "JUPFW:" に続く文字列（ビルド日時）を .uf2 の中身から読み取る。
"""
import datetime, json, pathlib, re, shutil, struct, sys

src, dst, sha = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3]
uf2s = sorted(src.rglob('*.uf2'))
if not uf2s:
    sys.exit('no .uf2 found in ' + str(src))
uf2 = uf2s[0]
raw = uf2.read_bytes()

# UF2 は 512 バイトのブロックの並び。中のデータを書き込み先アドレス順につなぐ
blocks = []
for off in range(0, len(raw) - 511, 512):
    b = raw[off:off + 512]
    m0, m1, _flags, addr, size = struct.unpack_from('<IIIII', b, 0)
    if m0 != 0x0A324655 or m1 != 0x9E5D5157:
        continue
    blocks.append((addr, b[32:32 + size]))
image = b''.join(d for _, d in sorted(blocks))
m = re.search(rb'JUPFW:([ -~]{1,40}?)\x00', image)
if not m:
    sys.exit('firmware build marker JUPFW: not found')
version = m.group(1).decode('ascii')

dst.mkdir(parents=True, exist_ok=True)
name = 'ogm10_jupiter_vial.uf2'
shutil.copyfile(uf2, dst / name)
info = {
    'version': version,
    'file': name,
    'size': len(raw),
    'commit': sha,
    'published': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
}
(dst / 'latest.json').write_text(json.dumps(info, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print(json.dumps(info, ensure_ascii=False))
