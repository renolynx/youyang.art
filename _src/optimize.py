#!/usr/bin/env python3
"""Turn raw images into web-sized WebP and record their sizes in _src/media.json.

Usage:  python3 _src/optimize.py <folder-or-files...>
New entries are merged into the existing manifest; files already optimized are
kept unless the source is newer than the WebP.
"""
import json, pathlib, sys
from PIL import Image, ImageSequence, ImageOps

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'media'
MANIFEST = ROOT / '_src/media.json'
MAX_STILL, MAX_ANIM = 1800, 1280
EXT = ('.jpg', '.jpeg', '.png', '.gif', '.webp')

def fit(w, h, cap):
    if max(w, h) <= cap: return w, h
    scale = cap / max(w, h)
    return max(1, round(w * scale)), max(1, round(h * scale))

def optimize_one(src, manifest):
    """Optimize one file into media/<stem>.webp; returns (stem, entry)."""
    src = pathlib.Path(src)
    OUT.mkdir(exist_ok=True)
    dst = OUT / (src.stem + '.webp')
    im = Image.open(src)
    animated = getattr(im, 'n_frames', 1) > 1
    if not animated:
        im = ImageOps.exif_transpose(im)
    w, h = fit(*im.size, MAX_ANIM if animated else MAX_STILL)
    if not dst.exists() or dst.stat().st_mtime < src.stat().st_mtime:
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
    entry = {'src': 'media/' + dst.name, 'w': w, 'h': h,
             'anim': animated, 'bytes': dst.stat().st_size}
    manifest[src.stem] = entry
    return src.stem, entry

def load_manifest():
    return json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}

def save_manifest(manifest):
    MANIFEST.write_text(json.dumps(manifest, indent=1))

def optimize(paths):
    manifest = load_manifest()
    done = []
    for p in paths:
        p = pathlib.Path(p)
        files = sorted(x for x in p.iterdir() if x.suffix.lower() in EXT) if p.is_dir() else [p]
        for src in files:
            if src.suffix.lower() not in EXT: continue
            stem, e = optimize_one(src, manifest)
            done.append(stem)
            print(f"{src.name:44} {src.stat().st_size//1024:6}KB → {e['bytes']//1024:5}KB  {e['w']}x{e['h']}{'  (anim)' if e['anim'] else ''}", flush=True)
    save_manifest(manifest)
    return done

if __name__ == '__main__':
    optimize(sys.argv[1:] or ['raw'])
