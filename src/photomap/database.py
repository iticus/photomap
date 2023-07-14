"""
Created on Nov 1, 2015

@author: iticus
"""

import datetime
import json
import logging
from typing import Optional

import asyncpg
from pydantic import Field
from pydantic.dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Album:
    """
    Main album class
    """

    album_id: Optional[int]
    start_moment: datetime.datetime = Field(None, title="Album earliest date")
    stop_moment: datetime.datetime = Field(None, title="Album latest date")
    name: str = Field(None, title="Album name", max_length=256)
    description: str = Field(None, title="Album name", max_length=8192)


@dataclass
class Camera:
    """
    Main camera class
    """

    camera_id: Optional[int]
    make: str = Field(None, title="Camera make", max_length=256)
    model: str = Field(None, title="Camera model", max_length=256)


@dataclass
class Photo:
    """
    Main photo class
    """

    photo_id: Optional[int]
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
    gps_ref: str = Field(None, title="GPS reference (NE0)", min_length=3, max_length=3)
    access: int = Field(None, title="Photo permissions (rw)", gt=0, lt=16)


@dataclass
class Tag:
    """
    Main tag class
    """

    tag_id: int
    photo_id: int
    name: str = Field(None, title="Tag text", max_length=64)


class Database:
    """
    Database related functions for PG-based SQL data store
    """

    def __init__(self, username: str, password: str, host: str, port: int, db_name: str) -> None:
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.db_name = db_name
        self.dsn = f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.db_name}"
        self.pool = None

    async def connect(self) -> None:
        """
        Initialize asyncpg Pool and connect to the database
        """

        async def init_connection(conn):
            await conn.set_type_codec("jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")
            # await conn.set_type_codec("geometry", encoder=encode_geometry,decoder=decode_geometry, format="binary")

        self.pool = await asyncpg.create_pool(dsn=self.dsn, min_size=2, max_size=8, init=init_connection)
        logger.info("successfully connected to database %s on %s", self.db_name, self.host)

    async def disconnect(self) -> None:
        """
        Disconnect from PG and close pool
        """
        await self.pool.close()
        logger.info("successfully disconnected from database")

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

    async def get_cameras(self):
        conn = await self.pool.acquire()
        query = "SELECT id, make, model FROM camera"
        try:
            cameras = await conn.fetch(query)
        finally:
            await self.pool.release(conn)
        return cameras

    async def delete_camera(self, camera_id: int):
        conn = await self.pool.acquire()
        query = "DELETE FROM camera WHERE id=$1"
        try:
            await conn.fetchrow(query, camera_id)
        finally:
            await self.pool.release(conn)

    async def save_photo(self, photo: Photo) -> int:
        conn = await self.pool.acquire()
        data = [
            photo.ihash,
            photo.description,
            photo.album,
            photo.moment,
            photo.path,
            photo.filename,
            photo.width,
            photo.height,
            photo.size,
            photo.camera,
            photo.orientation,
            photo.lat,
            photo.lng,
            photo.altitude,
            photo.gps_ref,
            photo.access,
        ]
        if hasattr(photo, "id"):
            data.append(photo.id)
            query = """UPDATE photo SET ihash=$1, description=$2, album_id=$3, moment=$4, path=$5, filename=$6,
                   width=$7, height=$8, size=$9, camera_id=$10, orientation=$11, lat=$12, lng=$13, altitude=$14,
                   gps_ref=$15, access=$16 WHERE id=$17 RETURNING id"""
        else:
            query = """INSERT INTO photo(ihash, description, album_id, moment, path, filename, width, height, size,
            camera_id, orientation, lat, lng, altitude, gps_ref, access)
            VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16) RETURNING id"""
        try:
            photo_id = await conn.fetchrow(query, *data)
        finally:
            await self.pool.release(conn)
        return photo_id

    async def update_photo_location(self, photo_id: int, ihash: str, lat: float, lng: float) -> int:
        conn = await self.pool.acquire()
        query = "UPDATE photo set lat=$1, lng=$2 WHERE id=$3 and ihash=$4 RETURNING id"
        try:
            photo_id = await conn.fetchrow(query, lat, lng, photo_id, ihash)
        finally:
            await self.pool.release(conn)
        return photo_id

    async def delete_photo(self, photo_id: int):
        conn = await self.pool.acquire()
        query = "DELETE FROM photo WHERE id=$1"
        try:
            await conn.fetchrow(query, photo_id)
        finally:
            await self.pool.release(conn)

    async def get_all_ihash(self):
        conn = await self.pool.acquire()
        try:
            hashes = await conn.fetch("SELECT photo.ihash FROM photo")
        finally:
            await self.pool.release(conn)
        return hashes

    async def get_geotagged_photos(self):
        conn = await self.pool.acquire()
        query = """SELECT photo.id, ihash, lat, lng, altitude, extract(epoch from moment) as moment,
                filename, size, make, model, orientation, path, width, height, photo.description
                FROM photo LEFT OUTER JOIN camera on photo.camera_id = camera.id
                WHERE lat IS NOT NULL AND lng IS NOT NULL"""
        try:
            photos = await conn.fetch(query)
        finally:
            await self.pool.release(conn)
        return photos

    async def get_photos_nogps(self, start_moment: datetime.datetime, stop_moment: datetime.datetime):
        conn = await self.pool.acquire()
        query = """SELECT photo.id, ihash, extract(epoch from moment) as moment, filename, size,
                make, model, orientation, path, width, height, photo.description
                FROM photo LEFT OUTER JOIN camera on photo.camera_id = camera.id
                WHERE (lat IS NULL OR lng IS NULL) AND moment BETWEEN $1 AND $2 ORDER BY moment ASC LIMIT 30"""
        try:
            photos = await conn.fetch(query, start_moment, stop_moment)
        finally:
            await self.pool.release(conn)
        return photos

    async def save_tag(self, tag: Tag) -> int:
        conn = await self.pool.acquire()
        data = [tag.name, tag.photo]
        if not hasattr(tag, "id"):
            data.append(tag.id)
            query = "UPDATE tag SET name=$1, photo=$2 WHERE id=$3 RETURNING id"
        else:
            query = "INSERT INTO tag(name, photo_id) VALUES($1, $2) RETURNING id"
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
        query = """SELECT photo.id,extract(epoch from moment) as moment,lat,lng,size,make,model,
                width, height FROM photo LEFT OUTER JOIN camera on photo.camera_id = camera.id"""
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
            """CREATE TABLE IF NOT EXISTS photo(
                    id serial NOT NULL,
                    ihash text NOT NULL UNIQUE,
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
                    CONSTRAINT photo_pkey PRIMARY KEY (id),
                    CONSTRAINT photo_album_id_fkey FOREIGN KEY (album_id) REFERENCES album(id),
                    CONSTRAINT photo_camera_id_fkey FOREIGN KEY (camera_id) REFERENCES camera(id)
            )""",
            "CREATE INDEX IF NOT EXISTS photo_album_id_idx ON photo USING btree(album_id)",
            "CREATE INDEX IF NOT EXISTS photo_camera_id_idx ON photo USING btree(camera_id)",
            "CREATE INDEX IF NOT EXISTS photo_altitude_idx ON photo USING btree(altitude)",
            "CREATE INDEX IF NOT EXISTS photo_lat_idx ON photo USING btree(lat)",
            "CREATE INDEX IF NOT EXISTS photo_lng_idx ON photo USING btree(lng)",
            "CREATE INDEX IF NOT EXISTS photo_moment_idx ON photo USING btree(moment)",
            "CREATE INDEX IF NOT EXISTS photo_access_idx ON photo USING btree(access)",
            """CREATE TABLE IF NOT EXISTS photo_tag(
                  id serial NOT NULL,
                  name text NOT NULL,
                  photo_id integer NOT NULL,
                  CONSTRAINT tag_pkey PRIMARY KEY (id),
                  CONSTRAINT tag_photo_id_fkey FOREIGN KEY(photo_id) REFERENCES photo(id)
            )""",
            "CREATE INDEX IF NOT EXISTS tag_name_idx ON photo_tag USING btree(name)",
            "CREATE INDEX IF NOT EXISTS tag_photo_id_idx ON photo_tag USING btree(photo_id)",
        ]
        conn = await self.pool.acquire()
        for query in queries:
            try:
                await conn.fetch(query)
            except Exception as exc:
                logger.error("cannot run query: %s", exc)
        await self.pool.release(conn)

    # @property
    # def gear_level(self) -> int:
    #     return self._gear_level
    #
    # @gear_level.setter
    # def gear_level(self, value: int) -> None:
    #     self._gear_level = min(max(value, 0), 5)
