"""
Created on Sep 11, 2012

@author: ionut
"""

import mimetypes
from io import BytesIO
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
        degree = float(exif_data[0][0] / exif_data[0][1])
    else:
        degree = float(exif_data[0])
    if isinstance(exif_data[1], tuple):
        minute = float(exif_data[1][0] / exif_data[1][1])
    else:
        minute = float(exif_data[1])
    if isinstance(exif_data[2], tuple):
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


def encode_multipart_formdata(fields, files):
    """
    Encode multipart data to be used in data import
    adapted from: http://code.activestate.com/recipes/146306/
    :param fields: sequence of (name, value) elements for regular form fields.
    :param files:  sequence of (name, filename, value) elements for data to be uploaded as files
    :return: (content_type, body) ready for httplib.HTTP instance
    """
    boundary = '-------tHISiSsoMeMulTIFoRMbOUNDaRY---'
    fls = []
    for (key, value) in fields:
        fls.append('--' + boundary)
        fls.append('Content-Disposition: form-data; name="%s"' % key)
        fls.append('')
        fls.append(value)
    for (key, filename, value) in files:
        fls.append('--' + boundary)
        fls.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        fls.append('Content-Type: %s' % get_content_type(filename))
        fls.append('')
        fls.append(value)
    fls.append('--' + boundary + '--')
    fls.append('')
    output = BytesIO()
    for content in fls:
        if isinstance(content, bytes):
            output.write(content)
        else:
            output.write(content.encode())
        output.write(b"\r\n")
    body = output.getvalue()
    content_type = 'multipart/form-data; boundary=%s' % boundary
    return content_type, body


def get_content_type(filename):
    """
    Detect file content type using mime
    :param filename: input filename:
    :return: detected file mimetype
    """
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'


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
