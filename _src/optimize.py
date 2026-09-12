#!/usr/bin/env python3
"""Turn the raw Portfolio downloads into web-sized WebP + a size manifest."""
import json, pathlib, sys
from PIL import Image, ImageSequence

SRC = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'raw')
OUT = pathlib.Path('media')
OUT.mkdir(exist_ok=True)
MAX_STILL, MAX_ANIM = 1800, 1280
manifest = {}

def fit(w, h, cap):
    if w <= cap: return w, h
    return cap, max(1, round(h * cap / w))

for src in sorted(SRC.iterdir()):
    if src.suffix.lower() not in ('.jpg', '.jpeg', '.png', '.gif'): continue
    dst = OUT / (src.stem + '.webp')
    im = Image.open(src)
    animated = getattr(im, 'n_frames', 1) > 1
    w, h = fit(*im.size, MAX_ANIM if animated else MAX_STILL)
    if not dst.exists():
        if animated:
            frames = [f.convert('RGBA').resize((w, h), Image.LANCZOS)
                      for f in ImageSequence.Iterator(im)]
            durations = []
            im.seek(0)
            for f in ImageSequence.Iterator(im):
                durations.append(f.info.get('duration', 80))
            frames[0].save(dst, 'WEBP', save_all=True, append_images=frames[1:],
                           duration=durations, loop=0, quality=68, method=4)
        else:
            im.convert('RGB' if im.mode in ('CMYK', 'P', 'L') else im.mode)\
              .resize((w, h), Image.LANCZOS)\
              .save(dst, 'WEBP', quality=82, method=5)
    manifest[src.stem] = {'src': 'media/' + dst.name, 'w': w, 'h': h,
                          'anim': animated, 'bytes': dst.stat().st_size}
    print(f"{src.name:44} {src.stat().st_size//1024:6}KB → {dst.stat().st_size//1024:5}KB  {w}x{h}{'  (anim)' if animated else ''}", flush=True)

pathlib.Path('_src/media.json').write_text(json.dumps(manifest, indent=1))
before = sum(p.stat().st_size for p in SRC.iterdir() if p.suffix.lower() in ('.jpg','.jpeg','.png','.gif'))
after = sum(v['bytes'] for v in manifest.values())
print(f"\nTOTAL {before//1024//1024}MB → {after//1024//1024}MB  ({len(manifest)} files)")
