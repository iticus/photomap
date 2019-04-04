"""
Created on Nov 1, 2015

@author: ionut
"""

import datetime
import logging
import momoko
import tornado

import settings


logger = logging.getLogger('db')
_db = momoko.Pool(dsn=settings.DSN, raise_connect_errors=True)
_db.connect()


@tornado.gen.coroutine
def raw_query(query, data):
    try:
        cursor = yield _db.execute(query, data)
    except Exception as e:
        logger.error('cannot retrieve record(s): %s' % e)
        raise tornado.gen.Return(False)

    result = cursor.fetchall()
    logger.debug('got %d results' % len(result))
    raise tornado.gen.Return(result)

    
class Album:
    """
    Main album class used for album db interaction
    """

    def __init__(self, name=None, description=None, start_moment=None, stop_moment=None):
        self.name = name
        self.description = description
        self.start_moment = start_moment
        self.stop_moment = stop_moment
        self.create_statement = '''CREATE TABLE album(
          id serial NOT NULL,
          name text UNIQUE NOT NULL,
          description text NOT NULL,
          start_moment timestamp without time zone,
          stop_moment timestamp without time zone,
          CONSTRAINT album_pkey PRIMARY KEY (id)
        )'''

    @tornado.gen.coroutine
    def save(self):
        if not self.name or not self.description:
            raise Exception('cannot save album, name or description missing')

        if not (0 < len(self.name) < 256) or not (0 < len(self.description) < 8192):
            raise Exception('cannot save album, name or description length incorrect')

        if not isinstance(self.start_moment, datetime.datetime) or not isinstance(self.stop_moment, datetime.datetime):
            raise Exception('cannot save album, start_moment and stop_moment must be of type datetime.datetime')

        data = [self.name, self.description, self.start_moment, self.start_moment]
        if not hasattr(self, 'id'):
            query = 'INSERT INTO album(name,description,start_moment,stop_moment) VALUES(%s, %s, %s, %s) RETURNING id'
        else:
            data.append(self.id)
            query = 'UPDATE album SET name=%s, description=%s, start_moment=%s, stop_moment=%s WHERE id=%s RETURNING id'

        try:
            cursor = yield _db.execute(query, data)
        except Exception as e:
            logger.error('cannot save album: %s' % e)
            raise tornado.gen.Return(False)

        result = cursor.fetchall()
        logger.debug('got result %s saving album' % result)
        raise tornado.gen.Return(result[0])

    @tornado.gen.coroutine
    def delete(self):
        if not hasattr(self, 'id'):
            raise Exception('cannot delete album without id field')

        query = 'DELETE FROM album WHERE id=%s'
        data = (self.id, )
        try:
            cursor = yield _db.execute(query, data)
        except Exception as e:
            logger.error('cannot delete album: %s' % e)
            raise tornado.gen.Return(False)

        result = cursor.fetchall()
        logger.debug('got result %s saving album' % result)
        raise tornado.gen.Return(result[0])


class Camera:
    """
    Main camera module for handling camera objects
    """

    def __init__(self, make=None, model=None):
        self.make = make
        self.model = model
        self.create_statement = '''CREATE TABLE camera(
          id serial NOT NULL,
          make text NOT NULL,
          model text NOT NULL,
          CONSTRAINT camera_pkey PRIMARY KEY (id)
        )'''

    @tornado.gen.coroutine
    def save(self):
        if not self.make or not self.model:
            raise Exception('cannot save camera, make or model missing')

        if not (0 < len(self.make) < 256) or not (0 < len(self.model) < 256):
            raise Exception('cannot save camera, make or model length incorrect')

        data = [self.make, self.model]
        if not hasattr(self, 'id'):
            query = 'INSERT INTO camera(make, model) VALUES(%s, %s) RETURNING id'
        else:
            data.append(self.id)
            query = 'UPDATE camera SET make=%s, model=%s WHERE id=%s RETURNING id'

        try:
            cursor = yield _db.execute(query, data)
        except Exception as e:
            logger.error('cannot save camera: %s' % e)
            raise tornado.gen.Return(False)

        result = cursor.fetchall()
        logger.debug('got result %s saving camera' % result)
        raise tornado.gen.Return(result[0])

    @tornado.gen.coroutine
    def delete(self):
        if not hasattr(self, 'id'):
            raise Exception('cannot delete camera without id field')
        
        query = 'DELETE FROM camera WHERE id=%s'
        data = (self.id, )

        try:
            cursor = yield _db.execute(query, data)
        except Exception as e:
            logger.error('cannot delete camera: %s' % e)
            raise tornado.gen.Return(False)

        result = cursor.fetchall()
        logger.debug('got result %s saving camera' % result)
        raise tornado.gen.Return(result[0])


class Image:

    def __init__(self, ihash=None, description=None, album=None, moment=None, path=None, filename=None,
                 width=None, height=None, size=None, camera=None, orientation=None,
                 lat=None, lng=None, altitude=None, gps_ref=None, access=None):
    
        self.ihash = ihash
        self.description = description
        self.album = album
        self.moment = moment
        self.path = path
        self.filename = filename
        self.width = width
        self.height = height
        self.size = size
        self.camera = camera
        self.orientation = orientation
        # 1: 'Horizontal (normal)'
        # 2: 'Mirrored horizontal'
        # 3: 'Rotated 180'
        # 4: 'Mirrored vertical'
        # 5: 'Mirrored horizontal then rotated 90 CCW'
        # 6: 'Rotated 90 CW'
        # 7: 'Mirrored horizontal then rotated 90 CW'
        # 8: 'Rotated 90 CCW'
        self.lat = lat
        self.lng = lng
        self.altitude = altitude
        self.gps_ref = gps_ref
        self.access = access
        self.create_statement = '''
            CREATE TABLE image(
                id serial NOT NULL,
                ihash text NOT NULL,
                description text NOT NULL,
                album_id integer,
                moment timestamp without time zone NOT NULL,
                path text NOT NULL,
                filename text NOT NULL,
                width smallint NOT NULL,
                height smallint NOT NULL,
                size integer NOT NULL,
                camera_id integer,
                orientation smallint NOT NULL,
                lat double precision,
                lng double precision,
                altitude double precision,
                gps_ref text NOT NULL,
                access smallint NOT NULL,
                CONSTRAINT image_pkey PRIMARY KEY (id),
                CONSTRAINT image_album_id_fkey FOREIGN KEY (album_id) REFERENCES album(id),
                CONSTRAINT image_camera_id_fkey FOREIGN KEY (camera_id) REFERENCES camera(id)
            );
        CREATE INDEX image_album_id ON album_image USING btree(album_id);
        CREATE INDEX image_camera_id ON album_image USING btree(camera_id);
        CREATE INDEX image_altitude ON album_image USING btree(altitude);
        CREATE INDEX image_lat ON album_image USING btree(lat);
        CREATE INDEX image_lng ON album_image USING btree(lng);
        CREATE INDEX image_moment ON album_image USING btree(moment);
        CREATE INDEX image_access ON album_image USING btree(access);
        '''

    @tornado.gen.coroutine
    def save(self):
        if not self.ihash or not self.moment:
            raise Exception('cannot save image, ihash or moment missing')

        if not 0 < len(self.ihash) < 64 or not isinstance(self.moment, datetime.datetime):
            raise Exception('cannot save image, ihash or moment incorrect')

        if not self.filename:
            raise Exception('cannot save image, path or filename missing')

        if not 0 < len(self.filename) < 64:
            raise Exception('cannot save image, filename length incorrect')

        if self.album and not isinstance(self.album, int):
            raise Exception('cannot save image, album info incorrect')

        if self.camera and not isinstance(self.camera, int):
            raise Exception('cannot save image, camera info incorrect')

        if not self.width or not self.height:
            raise Exception('cannot save image, width x height info missing')

        if not isinstance(self.width, int) or not isinstance(self.height, int):
            raise Exception('cannot save image, width x height info incorrect')

        if not self.size or not self.orientation:
            raise Exception('cannot save image, size / orientation info missing')

        if not isinstance(self.size, int) or not isinstance(self.orientation, int):
            raise Exception('cannot save image, size / orientation info incorrect')

        if self.lat and not isinstance(self.lat, float):
            raise Exception('cannot save image, latitude info incorrect')

        if self.lng and not isinstance(self.lng, float):
            raise Exception('cannot save image, longitude info incorrect')

        if self.description and not 0 < len(self.description) < 8192:
            raise Exception('cannot save image, description info incorrect')

        if self.gps_ref and not 0 < len(self.gps_ref) < 8:
            raise Exception('cannot save image, gps_ref info incorrect')

        if self.access and not 0 < self.access < 16:
            raise Exception('cannot save image, access info incorrect')

        if self.altitude and not isinstance(self.altitude, float):
            raise Exception('cannot save image, altitude info incorrect')

        data = [
            self.ihash, self.description, self.album, self.moment, self.path, self.filename, self.width, self.height,
            self.size, self.camera, self.orientation, self.lat, self.lng, self.altitude, self.gps_ref, self.access
        ]
        if not hasattr(self, 'id'):
            query = '''INSERT INTO image(ihash, description, album_id, moment, path, filename, width, height, size, camera_id, orientation, 
            lat, lng, altitude, gps_ref, access) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id'''
        else:
            data.append(self.id)
            query = '''UPDATE image SET ihash=%s, description=%s, album_id=%s, moment=%s, path=%s, filename=%s, width=%s, height=%s, 
            size=%s, camera_id=%s, orientation=%s, lat=%s, lng=%s, altitude=%s, gps_ref=%s, access=%s WHERE id=%s RETURNING id'''

        try:
            cursor = yield _db.execute(query, data)
        except Exception as e:
            logger.error('cannot save image: %s' % e)
            raise tornado.gen.Return(False)

        result = cursor.fetchall()
        logger.debug('got result %s saving image' % result)
        raise tornado.gen.Return(result[0])

    @tornado.gen.coroutine
    def delete(self):
        if not hasattr(self, 'id'):
            raise Exception('cannot delete image without id field')

        query = 'DELETE FROM image WHERE id=%s'
        data = (self.id, )

        try:
            cursor = yield _db.execute(query, data)
        except Exception as e:
            logger.error('cannot delete image: %s' % e)
            raise tornado.gen.Return(False)

        result = cursor.fetchall()
        logger.debug('got result %s saving image' % result)
        raise tornado.gen.Return(result[0])


class Tag:
    """
    Tag class to manage tag db objects
    """

    def __init__(self, name=None, image=None):
        self.name = name
        self.image = image
        self.create_statement = '''CREATE TABLE album_tag(
              id serial NOT NULL,
              name text NOT NULL,
              image_id integer NOT NULL,
              CONSTRAINT tag_pkey PRIMARY KEY (id),
              CONSTRAINT tag_image_id_fkey FOREIGN KEY(image_id) REFERENCES image(id)
            );
        CREATE INDEX tag_image_id ON album_tag USING btree(image_id);
        CREATE INDEX tag_name ON album_tag USING btree(name);
        '''

    @tornado.gen.coroutine
    def save(self):
        if not self.tag or not self.image:
            raise Exception('cannot save tag, name or image missing')

        if not (0 < len(self.name) < 64) or not isinstance(self.image, int):
            raise Exception('cannot save tag, name or image info incorrect')

        data = [self.name, self.image]
        if not hasattr(self, 'id'):
            query = 'INSERT INTO tag(name, image_id) VALUES(%s, %s) RETURNING id'
        else:
            data.append(self.id)
            query = 'UPDATE tag SET name=%s, image_id=%s WHERE id=%s RETURNING id'

        try:
            cursor = yield _db.execute(query, data)
        except Exception as e:
            logger.error('cannot save tag: %s' % e)
            raise tornado.gen.Return(False)

        result = cursor.fetchall()
        logger.debug('got result %s saving tag' % result)
        raise tornado.gen.Return(result[0])

    @tornado.gen.coroutine
    def delete(self):
        if not hasattr(self, 'id'):
            raise Exception('cannot delete tag without id field')

        query = 'DELETE FROM tag WHERE id=%s'
        data = (self.id, )

        try:
            cursor = yield _db.execute(query, data)
        except Exception as e:
            logger.error('cannot delete tag: %s' % e)
            raise tornado.gen.Return(False)

        result = cursor.fetchall()
        logger.debug('got result %s saving tag' % result)
        raise tornado.gen.Return(result[0])
