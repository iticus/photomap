'''
Created on May 24, 2016

@author: ionut
'''


import datetime
import hashlib
import json
import logging
import os
import pyexiv2
import tornado.web
from PIL import Image as PilImage
from StringIO import StringIO

import cache
import database
import settings
import utils
from settings import STATUS as status


class BaseHandler(tornado.web.RequestHandler):
    
    def initialize(self):
        pass
    
    @tornado.web.asynchronous
    def get(self):
        self.render('base.html')
    
    def post(self):
        self.finish('POST not allowed') 


class MapHandler(BaseHandler):
    

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        status['busy'] += 1
        images = cache.get_value('geotagged_images')
        if not images:
            query = '''SELECT image.id, ihash, lat, lng, altitude, extract(epoch from moment) as moment, filename, size, make, model, orientation, path, width, height, image.description 
            FROM image LEFT OUTER JOIN camera on image.camera_id = camera.id
            WHERE lat != %s and lng != %s'''
            data = (0, 0)
            images = yield database.raw_query(query, data)
            cache.set_value('geotagged_images', images)

        self.render('map.html', images=images)
        status['busy'] -= 1
    
    
    def post(self):
        self.finish('POST not allowed')


class GeoHandler(BaseHandler):
    

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self, op):
        
        if op == 'get_image_list':
            status['busy'] += 1
            start_dt = datetime.datetime.strptime(self.get_argument('start_filter', '2012-12-01'), '%Y-%m-%d')
            stop_dt = datetime.datetime.strptime(self.get_argument('stop_filter', '2015-12-01'), '%Y-%m-%d')
            query = '''SELECT image.id, ihash, extract(epoch from moment) as moment, filename, size, make, model, orientation, path, width, height, image.description 
            FROM image LEFT OUTER JOIN camera on image.camera_id = camera.id
            WHERE (lat is %s or lng is %s)
                AND moment between %s AND %s
            ORDER BY moment ASC
            LIMIT 30'''
            data = (None, None, start_dt, stop_dt)
            images = yield database.raw_query(query, data)
            self.finish(json.dumps(images))
            status['busy'] -= 1
            
        else:
            self.render('geotag.html')


    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self, op):
        if op == 'update_location':
            status['busy'] += 1
            ihash = self.get_argument('hash', 'unknown')
            iid = self.get_argument('id', 0)
            lat = self.get_argument('lat')
            lng = self.get_argument('lng')
            try:
                lat = float(lat)
                lng = float(lng)
            except:
                status['busy'] -= 1
                raise tornado.gen.Return(self.finish('lat and/or lng invalid'))
            
            query = '''UPDATE image set lat=%s, lng=%s WHERE id=%s and ihash=%s RETURNING id'''
            data = (lat, lng, iid, ihash)
            
            response = yield database.raw_query(query, data)
            if response:
                cache.del_value('geotagged_images')
                cache.del_value('stats')
                self.finish('image location updated successfully')
            else:
                self.set_status(400, 'image location not updated')
                self.finish()
            status['busy'] -= 1

        else:
            self.finish('unknown op')


class UploadHandler(BaseHandler):
    
    
    def get(self):
        self.render('upload.html')
    
    
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        secret = self.get_argument('secret', '')
        if secret != settings.SECRET:
            self.finish('wrong secret')
            return

        status['busy'] += 1
        images = yield database.raw_query("SELECT ihash FROM image", ())
        self.hashes = set()
        for image in images:
            self.hashes.add(image[0])
            
        self.fileinfo = self.request.files['image'][0]
        sha1 = hashlib.sha1()
        sha1.update(self.fileinfo['body'])
        ihash = sha1.hexdigest()
        
        if ihash in self.hashes:
            logging.info('image %s already imported' % ihash)
            status['busy'] -= 1
            self.finish('already imported')
            return
        
        exif_data = pyexiv2.ImageMetadata.from_buffer(self.fileinfo['body'])
        exif_data.read()
        
        size = len(self.fileinfo['body'])
        gps_ref = list('NE0')
        lat = None
        lng = None
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

        cameras = yield database.raw_query("SELECT id, make, model FROM camera", ())
        self.cameras = {}
        for camera in cameras:
            self.cameras[camera[1] + '_' + camera[2]] = camera
        
        if self.camera_make or self.camera_model:
            key = self.camera_make + '_' + self.camera_model
            if key in self.cameras:
                self.image.camera = self.cameras[key][0]
            else:
                camera = database.Camera(make=self.camera_make, model=self.camera_model)
                result = yield camera.save()
                self.image.camera = result[0]
                
        else:
            self.image.camera = None
        
        result = yield self.image.save()
        image_id = result[0]
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
        
        database.raw_query('UPDATE image SET path=%s WHERE id=%s RETURNING id', (self.image.path, image_id))
        cache.del_value('geotagged_images')
        cache.del_value('stats')
        self.finish('image saved, id %d' % image_id)
        status['busy'] -= 1

        
class StatsHandler(BaseHandler):
    

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self, op):
        if op == 'get_stats':
            status['busy'] += 1
            stats = cache.get_value('stats')
            if not stats:
                query = '''SELECT image.id, extract(epoch from moment) as moment, lat, lng, size, make, model, width, height 
                FROM image LEFT OUTER JOIN camera on image.camera_id = camera.id'''
                
                stats = yield database.raw_query(query, ())
                cache.set_value('stats', stats)

            self.finish(json.dumps(stats))
            status['busy'] -= 1

        else:
            self.render('stats.html')