"""
Created on Sep 11, 2012
@author: ionut
"""

import hashlib
import os
import tornado
from PIL import Image as PilImage
from utils import make_thumbnail
from tornado.gen import coroutine

import database
from settings import MEDIA_PATH


@coroutine
def main():
    base_dir = MEDIA_PATH
    images = yield database.raw_query("SELECT id, ihash, lat, lng, altitude, path, filename from image", ())
    for image in images:
        ihash = image[1]
        path = image[5]
        filename = image[6]

        thumb1 = os.path.join(base_dir, "thumbnails/64px", path, ihash)
        thumb2 = os.path.join(base_dir, "thumbnails/192px", path, ihash)
        thumb3 = os.path.join(base_dir, "thumbnails/960px", path, ihash)
        original = os.path.join(base_dir, "original/", path, ihash)
        if (not os.path.isfile(thumb1) or not os.path.isfile(thumb2) or not os.path.isfile(thumb3) or
                not os.path.isfile(original)):
            print("missing file: %s" % ihash)
            for root, dirs, files in os.walk("/media/ionut/Poze"):
                for file in files:
                    if file == filename:
                        fp = os.path.join(root, file)
                        fd = open(fp, "rb").read()
                        sha1 = hashlib.sha1()
                        sha1.update(fd)
                        new_hash = sha1.hexdigest()
                        if new_hash == ihash:
                            print("found", root, file, filename, original)
                            fw = open(original, "wb")
                            fw.write(fd)
                            fw.close()
                            image_file = PilImage.open(fp)
                            make_thumbnail(image_file, thumb1, 64, 64)
                            make_thumbnail(image_file, thumb2, 192, 192)
                            make_thumbnail(image_file, thumb3, 960, 960)
                            break


if __name__ == "__main__":
    tornado.ioloop.IOLoop.instance().run_sync(main)
