'''
Created on Nov 1, 2015

@author: ionut
'''

import datetime
import hashlib
import json
import logging
import os
import pyexiv2
import signal
import time
import tornado.ioloop
import tornado.web
from PIL import Image as PilImage
from StringIO import StringIO
from tornado import gen
from tornado.options import options, define

import cache
import database
import settings
import utils

_status = {'busy': 0, 'messages': []}
define("port", default=8001, help="listen port", type=int)
logging.basicConfig(level=settings.LOG_LEVEL, #filename='photomap.log', 
    format='[%(asctime)s] - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')


@gen.engine
def app_exit():
    i = 0
    while i < 9: #supervisord waits 10 seconds before sending SIGKILL
        if _status['busy'] <= 0:
            break
        i += 1
        logging.info('waiting %d seconds for tasks to finish' % 9-i)
        yield gen.Task(tornado.ioloop.IOLoop.instance().add_timeout, time.time() + 1)
    
    if _status['busy'] <= 0:
        logging.info('exited cleanly after %d iterations' % i)
    else:
        logging.error('forced exit after %d iterations' % i)
    
    logging.info('stopping IOloop...')
    tornado.ioloop.IOLoop.instance().stop()


def configure_signals():
    
    def stopping_handler(signum, frame):
        logging.info('interrupt signal %s received, shutting down' % signum)
        app_exit()
        
    signal.signal(signal.SIGINT, stopping_handler)
    signal.signal(signal.SIGTERM, stopping_handler)


class BaseHandler(tornado.web.RequestHandler):
    
    def initialize(self):
        pass
    
    @tornado.web.asynchronous
    def get(self):
        self.render('base.html')
    
    def post(self):
        self.finish('POST not allowed') 


class MapHandler(BaseHandler):
    
    def on_images(self, images, cached=False):
        if not cached:
            cache.set_value('geotagged_images', images)
        self.render('map.html', images=images)
        _status['busy'] -= 1
    
    @tornado.web.asynchronous
    def get(self):
        _status['busy'] += 1
        images = cache.get_value('geotagged_images')
        if images:
            self.on_images(images, True)
        else:
            query = '''SELECT image.id, ihash, lat, lng, altitude, extract(epoch from moment) as moment, filename, size, make, model, orientation, path, width, height, image.description 
            FROM image LEFT OUTER JOIN camera on image.camera_id = camera.id
            WHERE lat != %s and lng != %s'''
            data = (0, 0)
            database.raw_query(query, data, self.on_images)
    
    def post(self):
        self.finish('POST not allowed')


class GeoHandler(BaseHandler):
    
    def on_images(self, images):
        self.finish(json.dumps(images))
        _status['busy'] -= 1
    
    def on_update(self, response):
        if response:
            cache.del_value('geotagged_images')
            cache.del_value('stats')
            self.finish('image location updated successfully')
        else:
            self.set_status(400, 'image location not updated')
            self.finish()
        _status['busy'] -= 1
    
    @tornado.web.asynchronous
    def get(self, op):
        
        if op == 'get_image_list':
            _status['busy'] += 1
            start_dt = datetime.datetime.strptime(self.get_argument('start_filter', '2012-12-01'), '%Y-%m-%d')
            stop_dt = datetime.datetime.strptime(self.get_argument('stop_filter', '2015-12-01'), '%Y-%m-%d')
            query = '''SELECT image.id, ihash, extract(epoch from moment) as moment, filename, size, make, model, orientation, path, width, height, image.description 
            FROM image LEFT OUTER JOIN camera on image.camera_id = camera.id
            WHERE (lat is %s or lng is %s)
                AND moment between %s AND %s
            ORDER BY moment ASC
            LIMIT 30'''
            data = (None, None, start_dt, stop_dt)
            database.raw_query(query, data, self.on_images)
            
        else:
            self.render('geotag.html')
    
    @tornado.web.asynchronous
    def post(self, op):
        if op == 'update_location':
            _status['busy'] += 1
            ihash = self.get_argument('hash', 'unknown')
            iid = self.get_argument('id', 0)
            lat = self.get_argument('lat')
            lng = self.get_argument('lng')
            try:
                lat = float(lat)
                lng = float(lng)
            except:
                _status['busy'] -= 1
                return self.finish('lat and/or lng invalid')
            
            query = '''UPDATE image set lat=%s, lng=%s WHERE id=%s and ihash=%s RETURNING id'''
            data = (lat, lng, iid, ihash)
            database.raw_query(query, data, self.on_update)
        else:
            self.finish('unknown op')


class UploadHandler(BaseHandler):
    
    @tornado.web.asynchronous
    def _on_image_save(self, image_id):
        cache.del_value('geotagged_images')
        cache.del_value('stats')
        self.finish('image saved, id %d' % image_id[0])
        _status['busy'] -= 1
    
    @tornado.web.asynchronous
    def _on_image_add(self, image_id):
        image_id = image_id[0]
        path = 'pic' + str(int(image_id)/1000)
        self.image.path = path
        path = 'original/' + path
        
        image_file = PilImage.open(StringIO(self.fileinfo['body']))
        directory = settings.MEDIA_PATH + '/' + path
        if not os.path.exists(directory):
            os.makedirs(directory)
         
        output_file = open(directory+'/'+self.image.ihash, 'wb')
        output_file.write(self.fileinfo['body'])
        output_file.close()
         
        resolutions = [(64, 64), (192, 192), (960, 960)]
        for resolution in resolutions:
            directory = settings.MEDIA_PATH + '/thumbnails/' + str(resolution[0]) + 'px/pic' + str(int(image_id)/1000)
            if not os.path.exists(directory):
                os.makedirs(directory)
            outfile = directory + '/' + self.image.ihash
            utils.make_thumbnail(image_file, outfile, resolution[0], resolution[1])
        
        database.raw_query('UPDATE image SET path=%s WHERE id=%s RETURNING id', (self.image.path, image_id), self._on_image_save)

    @tornado.web.asynchronous
    def _save_image(self, camera_id):
        if camera_id:
            self.image.camera = camera_id
        
        self.image.save(self._on_image_add)
    
    @tornado.web.asynchronous
    def _on_cameras(self, cameras):
        self.cameras = {}
        for camera in cameras:
            self.cameras[camera[1] + '_' + camera[2]] = camera
        
        if self.camera_make or self.camera_model:
            key = self.camera_make + '_' + self.camera_model
            if key in self.cameras:
                self.image.camera = self.cameras[key][0]
                self._save_image(None)
            else:
                camera = database.Camera(make=self.camera_make, model=self.camera_model)
                camera.save(self._save_image)
        else:
            self.image.camera = None
            self._save_image(None)
    
    @tornado.web.asynchronous
    def _on_hashes(self, images):
        self.hashes = set()
        for image in images:
            self.hashes.add(image[0])
            
        self.fileinfo = self.request.files['image'][0]
        sha1 = hashlib.sha1()
        sha1.update(self.fileinfo['body'])
        ihash = sha1.hexdigest()
        
        if ihash in self.hashes:
            logging.info('image %s already imported' % ihash)
            _status['busy'] -= 1
            return self.finish('already imported')
        
        exif_data = pyexiv2.ImageMetadata.from_buffer(self.fileinfo['body'])
        exif_data.read()
        
        size = len(self.fileinfo['body'])
        gps_ref = list('NE0')
        lat = 0
        lng = 0
        altitude = 0
        
        if 'Exif.Image.ImageWidth' in exif_data.keys():
            width = int(exif_data['Exif.Image.ImageWidth'].value)
        elif 'Exif.Photo.PixelXDimension' in exif_data.keys():
            width = int(exif_data['Exif.Photo.PixelXDimension'].value)
        else:
            width = exif_data.dimensions[0]
            
        if 'Exif.Image.ImageLength' in exif_data.keys():
            height = int(exif_data['Exif.Image.ImageLength'].value)
        elif 'Exif.Photo.PixelYDimension' in exif_data.keys():
            height = int(exif_data['Exif.Photo.PixelYDimension'].value)
        else:
            height = exif_data.dimensions[1]
        
        if 'Exif.GPSInfo.GPSLatitude' in exif_data.keys():
            lat = utils.exif2gps(exif_data['Exif.GPSInfo.GPSLatitude'].value) 
        if 'Exif.GPSInfo.GPSLongitude' in exif_data.keys():
            lng = utils.exif2gps(exif_data['Exif.GPSInfo.GPSLongitude'].value) 
        if 'Exif.GPSInfo.GPSAltitude' in exif_data.keys():
            altitude = float(exif_data['Exif.GPSInfo.GPSAltitude'].value) 
        
        if 'Exif.GPSInfo.GPSLatitudeRef' in exif_data.keys():
            gps_ref[0] = exif_data['Exif.GPSInfo.GPSLatitudeRef'].value 
        if 'Exif.GPSInfo.GPSLongitudeRef' in exif_data.keys():
            gps_ref[1] = exif_data['Exif.GPSInfo.GPSLongitudeRef'].value 
        if 'Exif.GPSInfo.GPSAltitudeRef' in exif_data.keys():
            gps_ref[2] = exif_data['Exif.GPSInfo.GPSAltitudeRef'].value

        self.camera_make = ''
        self.camera_model = ''
        orientation = 1
        moment = datetime.datetime(1970, 1, 1)

        if 'Exif.Image.Make' in exif_data.keys():
            self.camera_make = exif_data['Exif.Image.Make'].value
        if 'Exif.Image.Model' in exif_data.keys():
            self.camera_model = exif_data['Exif.Image.Model'].value
        if 'Exif.Image.Orientation' in exif_data.keys():
            orientation = exif_data['Exif.Image.Orientation'].value
        if 'Exif.Image.DateTime' in exif_data.keys():
            moment = exif_data['Exif.Image.DateTime'].value
        
        self.image = database.Image(ihash=ihash, description='', album=None,
            moment=moment, width=width, height=height, orientation=orientation,
            filename=self.fileinfo['filename'], size=size, path='', 
            lat=lat, lng=lng, altitude=altitude, gps_ref=''.join(gps_ref), access=0)

        database.raw_query("SELECT id, make, model FROM camera", (), self._on_cameras)
        
    
    def get(self):
        self.render('upload.html')
    
    @tornado.web.asynchronous
    def post(self):
        secret = self.get_argument('secret', '')
        if secret != settings.SECRET:
            return self.finish('wrong secret')

        _status['busy'] += 1
        database.raw_query("SELECT ihash FROM image", (), self._on_hashes)
        
        
class StatsHandler(BaseHandler):
    
    def on_images(self, images, cached=False):
        if not cached:
            cache.set_value('stats', images)
        self.finish(json.dumps(images))
        _status['busy'] -= 1
    
    @tornado.web.asynchronous
    def get(self, op):
        if op == 'get_stats':
            _status['busy'] += 1
            images = cache.get_value('stats')
            if images:
                self.on_images(images, True)
            else:
                query = '''SELECT image.id, extract(epoch from moment) as moment, lat, lng, size, make, model, width, height 
                FROM image LEFT OUTER JOIN camera on image.camera_id = camera.id'''
                database.raw_query(query, (), self.on_images)
            
        else:
            self.render('stats.html')
        
        
if __name__ == "__main__":
    
    configure_signals()
    options.parse_command_line()
    application = tornado.web.Application([
        (r"/", BaseHandler),
        (r"/map/?", MapHandler),
        (r"/geotag/?([^/]+)?/?", GeoHandler),
        (r"/stats/?([^/]+)?/?", StatsHandler),
        (r"/upload/?", UploadHandler),
        (r'/media/(.*)', tornado.web.StaticFileHandler, {'path': settings.MEDIA_PATH}),
    ], debug=settings.DEBUG, gzip=True,
    template_path=settings.TEMPLATE_PATH,
    static_path=settings.STATIC_PATH)
    
    logging.info('starting photomap...')
    application.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()