"""
Created on Nov 1, 2015

@author: iticus
"""

import datetime
import logging
from typing import Optional

from pydantic import Field
from pydantic.dataclasses import dataclass

import asyncpg

logger = logging.getLogger(__name__)


@dataclass
class Album:
    """
    Main album class
    """
    album_id: int
    start_moment: datetime.datetime = Field(None, title="Album earliest date")
    stop_moment: datetime.datetime = Field(None, title="Album latest date")
    name: str = Field(None, title="Album name", max_length=256)
    description: str = Field(None, title="Album name", max_length=8192)



@dataclass
class Camera:
    """
    Main camera class
    """
    camera_id: int
    make: str = Field(None, title="Camera make", max_length=256)
    model: str = Field(None, title="Camera model", max_length=256)


@dataclass
class Photo:
    """
    Main photo class
    """
    photo_id: int
    album: Optional[int]
    camera: Optional[int]
    moment: datetime.datetime
    ihash: str = Field(None, title="Photo ihash (sha256)", max_length=64)
    description: str = Field(None, title="Photo description", max_length=8192)
    path: str = Field(None, title="File path (folder)", max_length=1024)
    filename: str = Field(None, title="Original filename", max_length=64)
    width: int = Field(None, title="Photo width (px)", gt=0, lt=64000)
    height: int = Field(None, title="Photo height (px)", gt=0, lt=64000)
    size: int = Field(None, title="Photo size (bytes)", gt=0, lt=10**9)  # 1 GB limit
    orientation: int = Field(1, title="Photo orientation (code)", ge=1, le=8)
    # 1: Horizontal (normal),  2: Mirrored horizontal, 3: Rotated 180, 4: Mirrored vertical
    # 5: Mirrored horizontal then rotated 90 CCW, 6: Rotated 90 CW
    # 7: Mirrored horizontal then rotated 90 CW, 8: Rotated 90 CCW
    lat: float = Field(None, title="Latitude (deg)", ge=-90, le=90)
    lng: float = Field(None, title="Longitude (deg)", ge=-180, le=180)
    altitude: float = Field(None, title="Altitude (m)", ge=0, le=12000)
    gps_ref: str = Field(None, title="GPS reference (NE0)",  min_length=3, max_length=3)
    access: int = Field(None, title="Image permissions (rw)", gt=0, lt=16)


@dataclass
class Tag:
    """
    Main tag class
    """
    tag_id: int
    image_id: int
    name: str = Field(None, title="Tag text", max_length=64)



class Database:
    """
    Database related functions for PG-based SQL data store
    """

    def __init__(self, dsn):
        self.dsn = dsn
        self.pool = None

    async def connect(self):
        """
        Initialize asyncpg Pool and connect to the database
        """
        self.pool = await asyncpg.create_pool(dsn=self.dsn, min_size=4, max_size=16)
        logger.info("successfully connected to database")

    async def save_album(self, album: Album) -> int:
        conn = await self.pool.acquire()
        data = [album.name, album.description, album.start_moment, album.stop_moment]
        if hasattr(album, "id"):
            data.append(self.id)
            query = "UPDATE album SET name=$1, description=$2, start_moment=$3, stop_moment=$4 WHERE id=$5 RETURNING id"
        else:
            query = "INSERT INTO album(name,description,start_moment,stop_moment) VALUES($1, $2, $3, $4) RETURNING id"
        try:
            album_id = await conn.fetchrow(query, *data)
        finally:
            await self.pool.release(conn)
        return album_id

    async def delete_album(self, album_id: int):
        conn = await self.pool.acquire()
        query = "DELETE FROM album WHERE id=$1"
        try:
            await conn.fetchrow(query, album_id)
        finally:
            await self.pool.release(conn)

    async def save_camera(self, camera: Camera) -> int:
        conn = await self.pool.acquire()
        data = [camera.make, camera.model]
        if hasattr(camera, "id"):
            data.append(camera.id)
            query = "UPDATE camera SET make=$1, model=$2 WHERE id=$3 RETURNING id"
        else:
            query = "INSERT INTO camera(make, model) VALUES($1, $2) RETURNING id"
        try:
            camera_id = await conn.fetchrow(query, *data)
        finally:
            await self.pool.release(conn)
        return camera_id

    async def delete_camera(self, camera_id: int):
        conn = await self.pool.acquire()
        query = "DELETE FROM camera WHERE id=$1"
        try:
            await conn.fetchrow(query, camera_id)
        finally:
            await self.pool.release(conn)

    async def save_image(self, image: Photo) -> int:
        conn = await self.pool.acquire()
        data = [
            image.ihash, image.description, image.album, image.moment, image.path, image.filename,
            image.width, image.height, image.size, image.camera, image.orientation,
            image.lat, image.lng, image.altitude, image.gps_ref, image.access
        ]
        if hasattr(image, "id"):
            data.append(image.id)
            query = """UPDATE image SET ihash=$1, description=$2, album_id=$3, moment=$4, path=$5, filename=$6,
                   width=$7, height=$8, size=$9, camera_id=$10, orientation=$11, lat=$12, lng=$13, altitude=$14, 
                   gps_ref=$15, access=$16 WHERE id=$17 RETURNING id"""
        else:
            query = """INSERT INTO image(ihash, description, album_id, moment, path, filename, width, height, size,
            camera_id, orientation, lat, lng, altitude, gps_ref, access)
            VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16) RETURNING id"""
        try:
            image_id = await conn.fetchrow(query, *data)
        finally:
            await self.pool.release(conn)
        return image_id

    async def delete_image(self, image_id: int):
        conn = await self.pool.acquire()
        query = "DELETE FROM image WHERE id=$1"
        try:
            await conn.fetchrow(query, image_id)
        finally:
            await self.pool.release(conn)

    async def get_geotagged_images(self):
        conn = await self.pool.acquire()
        query = """SELECT image.id, ihash, lat, lng, altitude, extract(epoch from moment) as moment,
                filename, size, make, model, orientation, path, width, height, image.description
                FROM image LEFT OUTER JOIN camera on image.camera_id = camera.id
                WHERE lat IS NOT NULL AND lng IS NOT NULL"""
        try:
            images = await conn.fetch(query)
        finally:
            await self.pool.release(conn)
        return images

    async def get_images_nogps(self, start_moment: datetime.datetime, stop_moment:datetime.datetime):
        conn = await self.pool.acquire()
        query = """SELECT image.id, ihash, extract(epoch from moment) as moment, filename, size,
                make, model, orientation, path, width, height, image.description
                FROM image LEFT OUTER JOIN camera on image.camera_id = camera.id
                WHERE (lat IS NULL OR lng IS NULL) AND moment BETWEEN $1 AND $2 ORDER BY moment ASC LIMIT 30"""
        try:
            images = await conn.fetch(query, start_moment, stop_moment)
        finally:
            await self.pool.release(conn)
        return images

    async def save_tag(self, tag: Tag) -> int:
        conn = await self.pool.acquire()
        data = [self.name, self.image]
        if not hasattr(tag, "id"):
            data.append(tag.id)
            query = "UPDATE tag SET name=$1, image_id=$2 WHERE id=$3 RETURNING id"
        else:
            query = "INSERT INTO tag(name, image_id) VALUES($1, $2) RETURNING id"
        try:
            tag_id = await conn.fetchrow(query, *data)
        finally:
            await self.pool.release(conn)
        return tag_id

    async def delete_tag(self, tag_id: int):
        conn = await self.pool.acquire()
        query = "DELETE FROM tag WHERE id=$1"
        try:
            await conn.fetchrow(query, tag_id)
        finally:
            await self.pool.release(conn)

    async def get_stats(self):
        conn = await self.pool.acquire()
        query = """SELECT image.id,extract(epoch from moment) as moment,lat,lng,size,make,model,
                width, height FROM image LEFT OUTER JOIN camera on image.camera_id = camera.id"""
        try:
            stats = await conn.fetch(query)
        finally:
            await self.pool.release(conn)
        return stats

    async def create_structure(self):
        queries = [
            """CREATE TABLE IF NOT EXISTS album(
                  id serial NOT NULL,
                  name text UNIQUE NOT NULL,
                  description text NOT NULL,
                  start_moment timestamp without time zone,
                  stop_moment timestamp without time zone,
                  CONSTRAINT album_pkey PRIMARY KEY (id)
            )""",
            """CREATE TABLE IF NOT EXISTS camera(
                  id serial NOT NULL,
                  make text NOT NULL,
                  model text NOT NULL,
                  CONSTRAINT camera_pkey PRIMARY KEY (id)
            )""",
            """CREATE TABLE IF NOT EXISTS image(
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
            """,
            """CREATE TABLE IF NOT EXISTS image_tag(
                  id serial NOT NULL,
                  name text NOT NULL,
                  image_id integer NOT NULL,
                  CONSTRAINT tag_pkey PRIMARY KEY (id),
                  CONSTRAINT tag_image_id_fkey FOREIGN KEY(image_id) REFERENCES image(id)
                );
                CREATE INDEX tag_image_id ON album_tag USING btree(image_id);
                CREATE INDEX tag_name ON album_tag USING btree(name);
            """
        ]

    # @property
    # def gear_level(self) -> int:
    #     return self._gear_level
    #
    # @gear_level.setter
    # def gear_level(self, value: int) -> None:
    #     self._gear_level = min(max(value, 0), 5)
