"""
Created on Sep 11, 2012

@author: ionut
"""

import os
from PIL import Image as PilImage


def exif2gps(exif_data):
    """
    Transform coordinate from DMS into D.D
    :param exif_data: image exif data:
    :return: degrees in D.D format
    """
    if not exif_data:
        return None
    if isinstance(exif_data[0], tuple):
        if exif_data[0][1] == 0:  # avoid division by 0
            return None
        degree = float(exif_data[0][0] / exif_data[0][1])
    else:
        degree = float(exif_data[0])
    if isinstance(exif_data[1], tuple):
        minute = float(exif_data[1][0] / exif_data[1][1])
        if exif_data[1][1] == 0:
            return None
    else:
        minute = float(exif_data[1])
    if isinstance(exif_data[2], tuple):
        if exif_data[2][1] == 0:
            return None
        second = float(exif_data[2][0] / exif_data[2][1])
    else:
        second = float(exif_data[2])
    return degree + minute / 60.0 + second / 3600.0


def make_thumbnail(image, outfile, width, height):
    """
    Create new thumbnail from image
    :param image: input image to create thumbnail from
    :param outfile: target filename for output
    :param width: thumbnail width
    :param height: thumbnail height
    """
    size = (width, height)
    try:
        temp = image.copy()
        temp.thumbnail(size, PilImage.ANTIALIAS)
        temp.save(outfile, "JPEG")
    except IOError as exc:
        print('cannot create thumbnail for %s: %s' % (image.filename, exc))


def generate_path(base_path: str, ihash: str) -> str:
    path = os.path.join(base_path, ihash[0], ihash[1])
    return path


def main():
    """
    Test make thumbnail
    """
    images = ['/home/ionut/img_test/test1.jpg', '/home/ionut/img_test/test2.jpg',
              '/home/ionut/img_test/test3.jpg']
    resolutions = [(960, 960), (192, 192), (64, 64)]

    for image in images:
        im1 = PilImage.open(image)
        for resolution in resolutions:
            outfile = image.replace('.jpg', '_') + str(resolution[0]) + '.jpg'
            make_thumbnail(im1, outfile, resolution[0], resolution[1])


if __name__ == '__main__':
    main()
