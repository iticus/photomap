"""
Created on Sep 11, 2012
@author: ionut
"""

import asyncio
import hashlib
import os

from PIL import Image as PilImage

import database
from settings import MEDIA_PATH
from utils import make_thumbnail


async def main() -> None:
    """
    Main function to check thumbnails for already imported photos
    """
    base_dir = MEDIA_PATH
    images = await database.raw_query("SELECT id, ihash, lat, lng, altitude, path, filename from image", ())
    for image in images:
        ihash = image[1]
        path = image[5]
        filename = image[6]

        thumb1 = os.path.join(base_dir, "thumbnails/64px", path, ihash)
        thumb2 = os.path.join(base_dir, "thumbnails/192px", path, ihash)
        thumb3 = os.path.join(base_dir, "thumbnails/960px", path, ihash)
        original = os.path.join(base_dir, "original/", path, ihash)
        if os.path.isfile(thumb1) and os.path.isfile(thumb2) and os.path.isfile(thumb3) and os.path.isfile(original):
            continue
        print(f"missing file: {ihash}")
        for root, _, files in os.walk("/media/ionut/Poze"):
            for file in files:
                if file == filename:
                    file_path = os.path.join(root, file)
                    file_desc = open(file_path, "rb").read()
                    sha1 = hashlib.sha1()
                    sha1.update(file_desc)
                    new_hash = sha1.hexdigest()
                    if new_hash == ihash:
                        print("found", root, file, filename, original)
                        fwd = open(original, "wb")
                        fwd.write(file_desc)
                        fwd.close()
                        image_file = PilImage.open(file_path)
                        make_thumbnail(image_file, thumb1, 64, 64)
                        make_thumbnail(image_file, thumb2, 192, 192)
                        make_thumbnail(image_file, thumb3, 960, 960)
                        break


if __name__ == "__main__":
    asyncio.run(main())
