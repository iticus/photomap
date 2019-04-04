"""
Created on May 24, 2016

@author: ionut
"""

import datetime
import hashlib
import json
import logging
import os
from io import BytesIO

import piexif
import tornado.web
from PIL import Image as PilImage

import cache
import database
import utils
import settings
from settings import STATUS as status


class BaseHandler(tornado.web.RequestHandler):
    """
    Handler for home, inherited by subsequent handlers
    """

    def initialize(self):
        pass

    @tornado.web.asynchronous
    def get(self):
        self.render('base.html')

    def post(self):
        self.finish('POST not allowed')


class MapHandler(BaseHandler):
    """
    Handler for /map (main map)
    """

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        status['busy'] += 1
        images = cache.get_value('geotagged_images')
        if not images:
            query = '''
                SELECT image.id, ihash, lat, lng, altitude, extract(epoch from moment) as moment,
                filename, size, make, model, orientation, path, width, height, image.description
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
    """
    Handler for manually geotagging photos (/geotag)
    """

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self, op):
        if op == 'get_image_list':
            status['busy'] += 1
            start_dt = datetime.datetime.strptime(self.get_argument('start_filter', '2012-12-01'), '%Y-%m-%d')
            stop_dt = datetime.datetime.strptime(self.get_argument('stop_filter', '2015-12-01'), '%Y-%m-%d')
            query = '''
                SELECT image.id, ihash, extract(epoch from moment) as moment, filename, size,
                make, model, orientation, path, width, height, image.description
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
    """
    Handler for manual uploading pictures (manually or via import script)
    """

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
        hashes = set()
        for image in images:
            hashes.add(image[0])

        fileinfo = self.request.files['image'][0]
        sha1 = hashlib.sha1()
        sha1.update(fileinfo['body'])
        ihash = sha1.hexdigest()

        if ihash in hashes:
            logging.info('image %s already imported', ihash)
            status['busy'] -= 1
            self.finish('already imported')
            return

        exif_data = piexif.load(fileinfo['body'])
        size = len(fileinfo['body'])
        width = -1
        height = -1
        gps_ref = ["N", "E", "0"]
        lat = None
        lng = None
        altitude = -1

        if piexif.ExifIFD.PixelXDimension in exif_data.get("Exif", {}):
            width = exif_data["Exif"][piexif.ExifIFD.PixelXDimension]
        if piexif.ExifIFD.PixelYDimension in exif_data.get("Exif", {}):
            height = exif_data["Exif"][piexif.ExifIFD.PixelYDimension]

        if "GPS" in exif_data:
            lat = utils.exif2gps(exif_data["GPS"].get(piexif.GPSIFD.GPSLatitude))
            lng = utils.exif2gps(exif_data["GPS"].get(piexif.GPSIFD.GPSLongitude))
            altitude = exif_data["GPS"].get(piexif.GPSIFD.GPSAltitude, -1)
            if isinstance(altitude, tuple):
                altitude = altitude[0] / altitude[1]

            if piexif.GPSIFD.GPSLatitudeRef in exif_data["GPS"]:
                gps_ref[0] = exif_data["GPS"].get(piexif.GPSIFD.GPSLatitudeRef, b"").decode()
                if gps_ref[0] == "S":
                    lat = -1 * lat
            if piexif.GPSIFD.GPSLongitudeRef in exif_data["GPS"]:
                gps_ref[1] = exif_data["GPS"].get(piexif.GPSIFD.GPSLongitudeRef, b"").decode()
                if gps_ref[0] == "W":
                    lng = -1 * lng
            if piexif.GPSIFD.GPSAltitudeRef in exif_data["GPS"]:
                gps_ref[2] = str(exif_data["GPS"].get(piexif.GPSIFD.GPSAltitudeRef, ""))

        camera_make = exif_data["0th"].get(piexif.ImageIFD.Make, b"").decode().strip("\x00")
        camera_model = exif_data["0th"].get(piexif.ImageIFD.Model, b"").decode().strip("\x00")
        if camera_make in camera_model:
            camera_model = camera_model.replace(camera_make, "").strip()
        orientation = exif_data["0th"].get(piexif.ImageIFD.Orientation, -1)
        moment = exif_data["0th"].get(piexif.ImageIFD.DateTime, b"1970:01:01 00:00:00")
        moment = datetime.datetime.strptime(moment.decode(), "%Y:%m:%d %H:%M:%S")

        image = database.Image(
            ihash=ihash, description='', album=None,
            moment=moment, width=width, height=height, orientation=orientation,
            filename=fileinfo['filename'], size=size, path='',
            lat=lat, lng=lng, altitude=altitude, gps_ref=''.join(gps_ref), access=0
        )

        cameras = yield database.raw_query("SELECT id, make, model FROM camera", ())
        camera_dict = {}
        for camera in cameras:
            camera_dict[camera[1] + '_' + camera[2]] = camera

        if camera_make or camera_model:
            key = camera_make + '_' + camera_model
            if key in camera_dict:
                image.camera = camera_dict[key][0]
            else:
                camera = database.Camera(make=camera_make, model=camera_model)
                result = yield camera.save()
                image.camera = result[0]

        else:
            image.camera = None

        result = yield image.save()
        image_id = int(result[0])
        path = 'pic' + str(int(image_id/1000))
        image.path = path
        path = 'original/' + path

        image_file = PilImage.open(BytesIO(fileinfo['body']))
        directory = settings.MEDIA_PATH + '/' + path
        if not os.path.exists(directory):
            os.makedirs(directory)

        output_file = open(directory + '/' + image.ihash, 'wb')
        output_file.write(fileinfo['body'])
        output_file.close()

        resolutions = [(64, 64), (192, 192), (960, 960)]
        for resolution in resolutions:
            directory = settings.MEDIA_PATH + '/thumbnails/' + str(resolution[0])
            directory += 'px/pic' + str(int(image_id)/1000)
            if not os.path.exists(directory):
                os.makedirs(directory)
            outfile = directory + '/' + image.ihash
            utils.make_thumbnail(image_file, outfile, resolution[0], resolution[1])

        database.raw_query('UPDATE image SET path=%s WHERE id=%s RETURNING id',
                           (image.path, image_id))
        cache.del_value('geotagged_images')
        cache.del_value('stats')
        self.finish('image saved, id %d' % image_id)
        status['busy'] -= 1


class StatsHandler(BaseHandler):
    """
    Handler for rendering image stats
    """

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self, op):
        if op == 'get_stats':
            status['busy'] += 1
            stats = cache.get_value('stats')
            if not stats:
                query = '''
                    SELECT image.id,extract(epoch from moment) as moment,lat,lng,size,make,model,
                    width, height FROM image LEFT OUTER JOIN camera on image.camera_id = camera.id
                '''

                stats = yield database.raw_query(query, ())
                cache.set_value('stats', stats)

            self.finish(json.dumps(stats))
            status['busy'] -= 1

        else:
            self.render('stats.html')
