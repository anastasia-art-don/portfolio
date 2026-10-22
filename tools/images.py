"""Prepare the portfolio photos for the web.

Every photo is kept in three sizes: assets/<name>.webp for large screens, assets/m/<name>.webp for phones and assets/thumbs/<name>.webp for the strip under a gallery. The site loads the large file when a smaller one is missing, so the smaller copies only make it faster.

    python3 tools/images.py                    make the phone copies and thumbnails that are missing or older than their photo
    python3 tools/images.py ORIGINAL [NAME]    add or replace assets/NAME.webp from an original JPG, PNG or PDF, then make its copies

Needs Pillow (pip install pillow); a PDF original also needs pdftoppm from poppler.
"""

import io
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageCms, ImageOps

ASSETS = Path(__file__).resolve().parent.parent / 'assets'
LARGE = 2400
PHONE = 1400
THUMB = (200, 160)

# Print originals are far larger than Pillow's guard against decompression bombs.
Image.MAX_IMAGE_PIXELS = None


def read_original(path):
    """Open an original as an sRGB image, the colour space browsers assume.

    A PDF contributes its first page. Print files are CMYK and some photos carry a wide-gamut profile; both are converted through their embedded colour profile, so colours on screen match the original.
    """
    if path.suffix.lower() == '.pdf':
        with tempfile.TemporaryDirectory() as folder:
            subprocess.run(['pdftoppm', '-r', '110', '-png', '-singlefile', str(path), f'{folder}/page'], check=True)
            image = Image.open(f'{folder}/page.png')
            image.load()
    else:
        image = Image.open(path)
        image.load()
    image = ImageOps.exif_transpose(image)
    profile = image.info.get('icc_profile')
    if profile:
        image = ImageCms.profileToProfile(
            image, ImageCms.ImageCmsProfile(io.BytesIO(profile)), ImageCms.createProfile('sRGB'),
            outputMode='RGBA' if image.mode == 'RGBA' else 'RGB')
    if image.mode == 'RGBA' and image.getchannel('A').getextrema()[0] == 255:
        return image.convert('RGB')
    if image.mode not in ('RGB', 'RGBA'):
        return image.convert('RGBA' if image.has_transparency_data else 'RGB')
    return image


def shrink(image, long_side):
    """Return a copy no longer than long_side on either side; smaller images stay as they are."""
    image = image.copy()
    image.thumbnail((long_side, long_side), Image.LANCZOS)
    return image


def save(image, path, quality):
    path.parent.mkdir(exist_ok=True)
    image.save(path, 'WEBP', quality=quality, method=6)


def add_original(original, name):
    """Write assets/<name>.webp from an original, replacing the photo of that name."""
    save(shrink(read_original(original), LARGE), ASSETS / f'{name}.webp', 86)


def make_copies():
    """Write the phone copy and the thumbnail of every photo that lacks them or has changed since."""
    for photo in sorted(ASSETS.glob('*.webp')):
        copies = (ASSETS / 'm' / photo.name, ASSETS / 'thumbs' / photo.name)
        if all(copy.exists() and copy.stat().st_mtime >= photo.stat().st_mtime for copy in copies):
            continue
        with Image.open(photo) as image:
            image.load()
            save(shrink(image, PHONE), copies[0], 82)
            save(ImageOps.fit(image, THUMB, Image.LANCZOS), copies[1], 78)
        print('Copies made:', photo.name)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        original = Path(sys.argv[1])
        add_original(original, sys.argv[2] if len(sys.argv) > 2 else original.stem)
    make_copies()
