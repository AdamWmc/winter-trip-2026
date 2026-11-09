"""Refresh the checked-in WebP variants and credits from the Wikimedia manifest.

Optional maintenance tool: python3 -m pip install Pillow
Run python3 src/images.py [key ...]. The normal site build uses no extra packages.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
import json
from pathlib import Path
from time import sleep
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from PIL import Image, ImageOps
from booklet_data import PHOTO_TEXT

DIR = Path(__file__).resolve().parents[1] / 'assets/img'
MANIFEST = DIR / 'photos.json'
SIZES = {640: 37000, 1280: 90000, 1920: 160000}
FOOD_SIZES = {640: 37000, 1280: 60000, 1920: 75000}
AGENT = 'WinterTripBooklet/1.0 (https://github.com/AdamWmc/winter-trip-2026)'

def download(url):
    for i in range(3):
        try:
            with urlopen(Request(url, headers={'User-Agent': AGENT}), timeout=35) as response:
                return response.read()
        except HTTPError as error:
            if error.code != 429 or i == 2:
                raise
            retry = error.headers.get('Retry-After', '')
            sleep(max(int(retry) if retry.isdecimal() else 0, 20 * (i + 1)))
        except URLError:
            if i == 2:
                raise
            sleep(2 ** i)

def image_bytes(image, budget):
    for quality in range(86, 0, -5):
        out = BytesIO()
        image.save(out, 'WEBP', quality=quality, method=5)
        if out.tell() <= budget:
            return out.getvalue()
    raise ValueError(f'Could not compress {image.size} within {budget} bytes')

def process(entry):
    key, row = entry
    print('Encoding', key, flush=True)
    image = ImageOps.exif_transpose(Image.open(BytesIO(download(row['download'])))).convert('RGB')
    if 'crop' in row:
        w, h = image.size
        image = image.crop(tuple(round(d * f) for d, f in zip((w, h, w, h), row['crop'])))
    if row.get('format') == 'food':
        center = tuple(float(p.removesuffix('%')) / 100 for p in row['focus'].split())
        # Use the same focal point as object-position, but crop the distributed file too.
        width = min(image.width, image.height * 4 // 3)
        image = ImageOps.fit(image, (width, round(width * .75)), centering=center)
    folder = DIR / row['folder']
    folder.mkdir(parents=True, exist_ok=True)
    for w, budget in (FOOD_SIZES if row.get("format", "").startswith("food") else SIZES).items():
        h = round(w * image.height / image.width)
        im = image.resize((w, h), Image.Resampling.LANCZOS)
        (folder / f"{row['slug']}-{w}.webp").write_bytes(image_bytes(im, budget))
        if w == 640:
            row['width'], row['height'] = w, h
    print(key, row['width'], row['height'], flush=True)

def markdown(value):
    return value.replace('\\', '\\\\').replace('[', '\\[').replace(']', '\\]')

def credits(rows):
    lines = ['# 照片來源與授權', '',
             '原始照片來自 Wikimedia Commons。網頁使用的版本已轉檔和縮放，部分照片有裁切；各版本沿用下列授權。', '']
    for key, row in rows.items():
        credit = f"[{markdown(row['title'])}]({row['source']})"
        license_link = f"[{row['license']}]({row['license_url']})"
        lines.append(f"- `{row['folder']}/{row['slug']}-{{640,1280,1920}}.webp` · {PHOTO_TEXT[key][1]} "
                     f"{credit} — {markdown(row['author'])} · {license_link}")
    (DIR / 'CREDITS.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('key', nargs='*')
    keys = parser.parse_args().key
    rows = json.loads(MANIFEST.read_text(encoding='utf-8'))
    jobs = ((key, rows[key]) for key in (keys or rows))
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(process, jobs))
    MANIFEST.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    credits(rows)

if __name__ == '__main__':
    main()
