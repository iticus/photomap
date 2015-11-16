'''
Created on Sep 11, 2012

@author: ionut
'''

from PIL import Image as PilImage
from StringIO import StringIO
import mimetypes


def exif2gps(exif_data):
    degree = float(exif_data[0])
    minute = float(exif_data[1])
    second = float(exif_data[2])
    return degree + minute / 60.0 + second / 3600.0


def make_thumbnail(image, outfile, width, height):
    
    size = (width, height)
    try:
        temp = image.copy()
        temp.thumbnail(size, PilImage.ANTIALIAS)
        temp.save(outfile, "JPEG")
    except IOError as e:
        print('cannot create thumbnail for %s; %s' % (image.filename, e.message))
        
        
"adapted from: http://code.activestate.com/recipes/146306/" 
def encode_multipart_formdata(fields, files): 
    """ fields is a sequence of (name, value) elements for regular form fields. 
        files is a sequence of (name, filename, value) elements for data to be uploaded as files 
        Return (content_type, body) ready for httplib.HTTP instance 
    """ 
    BOUNDARY = '-------tHISiSsoMeMulTIFoRMbOUNDaRY---' 
    CRLF = '\r\n' 
    L = [] 
    for (key, value) in fields: 
        L.append('--' + BOUNDARY) 
        L.append('Content-Disposition: form-data; name="%s"' % key) 
        L.append('') 
        L.append(value) 
    for (key, filename, value) in files: 
        L.append('--' + BOUNDARY) 
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename)) 
        L.append('Content-Type: %s' % get_content_type(filename)) 
        L.append('') 
        L.append(value) 
    L.append('--' + BOUNDARY + '--') 
    L.append('') 
    b = StringIO() 
    for l in L: 
        b.write(l) 
        b.write(CRLF) 
    body = b.getvalue() 
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY 
    return content_type, body 


def get_content_type(filename): 
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream' 


if __name__ == '__main__':
    
    images = ['/home/ionut/img_test/test1.jpg', '/home/ionut/img_test/test2.jpg', '/home/ionut/img_test/test3.jpg']
    resolutions = [(960, 960), (192, 192), (64, 64)]
    
    for image in images:
        im1 = PilImage.open(image)
        for resolution in resolutions:
            outfile = image.replace('.jpg','_') + str(resolution[0]) + '.jpg'
            make_thumbnail(im1, outfile, resolution[0], resolution[1])
    
    