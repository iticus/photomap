"""
Created on Nov 1, 2015

@author: iticus
"""

import datetime
import json
import logging

import asyncpg
from pydantic import Field
from pydantic.dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Album:
    """
    Main album class
    """

    album_id: int | None
    start_moment: datetime.datetime = Field(title="Album earliest date")
    stop_moment: datetime.datetime = Field(title="Album latest date")
    name: str = Field(title="Album name", max_length=256)
    description: str = Field(title="Album name", max_length=8192)


@dataclass
class Camera:
    """
    Main camera class
    """

    camera_id: int | None
    make: str = Field(title="Camera make", max_length=256)
    model: str = Field(title="Camera model", max_length=256)


@dataclass
class Photo:  # pylint: disable=too-many-instance-attributes
    """
    Main photo class
    """

    photo_id: int | None
    album: int | None
    camera: int | None
    moment: datetime.datetime
    ihash: str = Field(title="Photo ihash (sha256)", max_length=64)
    description: str = Field(title="Photo description", max_length=8192)
    filename: str = Field(title="Original filename", max_length=64)
    width: int = Field(title="Photo width (px)", gt=0, lt=64000)
    height: int = Field(title="Photo height (px)", gt=0, lt=64000)
    size: int = Field(title="Photo size (bytes)", gt=0, lt=10**9)  # 1 GB limit
    lat: float | None = Field(None, title="Latitude (deg)", ge=-90, le=90)
    lng: float | None = Field(None, title="Longitude (deg)", ge=-180, le=180)
    altitude: float | None = Field(None, title="Altitude (m)", ge=0, le=12000)
    gps_ref: str = Field(title="GPS reference (NE0)", min_length=3, max_length=3)
    access: int = Field(title="Photo permissions (rw)", gt=0, lt=16)
    orientation: int = Field(1, title="Photo orientation (code)", ge=1, le=8)


@dataclass
class Tag:
    """
    Main tag class
    """

    tag_id: int
    name: str = Field(title="Tag text", max_length=64)


class Database:
    """
    Database related functions for PG-based SQL data store
    """

    def __init__(  # pylint: disable=too-many-arguments
        self, username: str, password: str, host: str, port: int, db_name: str
    ) -> None:
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.db_name = db_name
        self.dsn = f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.db_name}"
        # self.pool

    async def connect(self) -> None:
        """
        Initialize asyncpg Pool and connect to the database
        """

        async def init_connection(conn: asyncpg.Connection) -> None:
            await conn.set_type_codec("jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")
            # await conn.set_type_codec("geometry", encoder=encode_geometry,decoder=decode_geometry, format="binary")

        self.pool = await asyncpg.create_pool(  # pylint: disable=attribute-defined-outside-init
            dsn=self.dsn, min_size=2, max_size=8, init=init_connection
        )
        logger.info("successfully connected to database %s on %s", self.db_name, self.host)

    async def disconnect(self) -> None:
        """
        Disconnect from PG and close pool
        """
        await self.pool.close()
        logger.info("successfully disconnected from database")

    async def save_album(self, album: Album) -> int:
        """
        Upsert album data to database
        :param album: album object to add or update
        :return: album ID
        """
        conn = await self.pool.acquire()
        data = [album.name, album.description, album.start_moment, album.stop_moment]
        if album.album_id:
            data.append(album.album_id)
            query = "UPDATE album SET name=$1, description=$2, start_moment=$3, stop_moment=$4 WHERE id=$5 RETURNING id"
        else:
            query = "INSERT INTO album(name,description,start_moment,stop_moment) VALUES($1, $2, $3, $4) RETURNING id"
        try:
            album_id = await conn.fetchrow(query, *data)
        finally:
            await self.pool.release(conn)
        return album_id

    async def delete_album(self, album_id: int) -> None:
        """
        Delete album object from database
        :param album_id: album ID to delete
        """
        conn = await self.pool.acquire()
        query = "DELETE FROM album WHERE id=$1"
        try:
            await conn.fetchrow(query, album_id)
        finally:
            await self.pool.release(conn)

    async def save_camera(self, camera: Camera) -> int:
        """
        Upsert camera data to database
        :param camera: camera object to add or update
        :return: camera ID
        """
        conn = await self.pool.acquire()
        data: list[str | int] = [camera.make, camera.model]
        if camera.camera_id:
            data.append(camera.camera_id)
            query = "UPDATE camera SET make=$1, model=$2 WHERE id=$3 RETURNING id"
        else:
            query = "INSERT INTO camera(make, model) VALUES($1, $2) RETURNING id"
        try:
            camera_id = await conn.fetchrow(query, *data)
        finally:
            await self.pool.release(conn)
        return camera_id

    async def get_cameras(self) -> list[Camera]:
        """
        Retrieve all cameras from database
        :return: list of cameras
        """
        conn = await self.pool.acquire()
        query = "SELECT id, make, model FROM camera"
        try:
            cameras = await conn.fetch(query)
        finally:
            await self.pool.release(conn)
        return cameras

    async def delete_camera(self, camera_id: int) -> None:
        """
        Delete camera object from database
        :param camera_id: camera ID to delete
        """
        conn = await self.pool.acquire()
        query = "DELETE FROM camera WHERE id=$1"
        try:
            await conn.fetchrow(query, camera_id)
        finally:
            await self.pool.release(conn)

    async def save_photo(self, photo: Photo) -> int:
        """
        Upsert photo data to database
        :param photo: photo object to add or update
        :return: photo ID
        """
        conn = await self.pool.acquire()
        data = [
            photo.ihash,
            photo.description,
            photo.album,
            photo.moment,
            photo.filename,
            photo.width,
            photo.height,
            photo.size,
            photo.camera,
            photo.lat,
            photo.lng,
            photo.altitude,
            photo.gps_ref,
            photo.access,
        ]
        if photo.photo_id:
            data.append(photo.photo_id)
            query = """UPDATE photo SET ihash=$1, description=$2, album_id=$3, moment=$4, filename=$5,
                   width=$6, height=$7, size=$8, camera_id=$9, lat=$10, lng=$11, altitude=$12,
                   gps_ref=$13, access=$14 WHERE id=$15 RETURNING id"""
        else:
            query = """INSERT INTO photo(ihash, description, album_id, moment, filename, width, height, size,
            camera_id, lat, lng, altitude, gps_ref, access)
            VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14) RETURNING id"""
        try:
            photo_id = await conn.fetchrow(query, *data)
        # except asyncpg.exceptions.PostgresError as exc:
        #     logger.error("cannot save image: %s", exc)
        finally:
            await self.pool.release(conn)
        return photo_id

    async def update_photo_location(self, photo_id: int, ihash: str, lat: float, lng: float) -> int:
        """
        Update location data for existing photo
        :param photo_id: object ID to update the location for
        :param ihash: photo hash to double-check
        :param lat: latitude to save
        :param lng: longitude to save
        :return: photo ID
        """
        conn = await self.pool.acquire()
        query = "UPDATE photo set lat=$1, lng=$2 WHERE id=$3 and ihash=$4 RETURNING id"
        try:
            photo_id = await conn.fetchrow(query, lat, lng, photo_id, ihash)
        finally:
            await self.pool.release(conn)
        return photo_id

    async def delete_photo(self, photo_id: int) -> None:
        """
        Delete photo from database
        :param photo_id: ID of the photo to remove
        """
        conn = await self.pool.acquire()
        query = "DELETE FROM photo WHERE id=$1"
        try:
            await conn.fetchrow(query, photo_id)
        finally:
            await self.pool.release(conn)

    async def get_all_ihash(self) -> list[str]:
        """
        Retrieve all existing i-hashes from the database
        :return: list of i-hashes
        """
        conn = await self.pool.acquire()
        try:
            hashes = await conn.fetch("SELECT photo.ihash FROM photo")
        finally:
            await self.pool.release(conn)
        return hashes

    async def get_photo(self, photo_id: int) -> Photo:
        """
        Retrieve photo details
        :param photo_id: id of the photo to retrieve
        :return: photo details
        """
        conn = await self.pool.acquire()
        query = """SELECT photo.id, ihash, extract(epoch from moment)::bigint as moment, filename, size,
                make, model, width, height, photo.description
                FROM photo LEFT OUTER JOIN camera on photo.camera_id = camera.id
                WHERE photo.id=$1"""
        try:
            photo = await conn.fetchrow(query, photo_id)
        finally:
            await self.pool.release(conn)
        return photo

    async def get_geotagged_photos(self, start: datetime.date, stop: datetime.date) -> list[Photo]:
        """
        Retrieve all existing photos from the database that have location information
        :return: list of photos
        """
        conn = await self.pool.acquire()
        query = """SELECT photo.id, ihash, lat, lng, altitude, extract(epoch from moment)::bigint as moment
                FROM photo LEFT OUTER JOIN camera on photo.camera_id = camera.id
                WHERE moment > $1 AND moment < $2 AND lat IS NOT NULL AND lng IS NOT NULL"""
        try:
            photos = await conn.fetch(query, start, stop)
        finally:
            await self.pool.release(conn)
        return photos

    async def get_photos_nogps(self, start_moment: datetime.datetime, stop_moment: datetime.datetime) -> list[Photo]:
        """
        Retrieve first 30 photos from the database without location information
        :return: list of photos
        """
        conn = await self.pool.acquire()
        query = """SELECT photo.id, ihash, extract(epoch from moment)::bigint as moment, filename, size,
                make, model, width, height, photo.description
                FROM photo LEFT OUTER JOIN camera on photo.camera_id = camera.id
                WHERE (lat IS NULL OR lng IS NULL) AND moment BETWEEN $1 AND $2 ORDER BY moment ASC LIMIT 25"""
        try:
            photos = await conn.fetch(query, start_moment, stop_moment)
        finally:
            await self.pool.release(conn)
        return photos

    async def save_tag(self, tag: Tag) -> int:
        """
        Upsert tag to database
        :param tag: tag object to add or update
        :return: tag ID
        """
        conn = await self.pool.acquire()
        data: list[str | int] = [tag.name]
        if tag.tag_id:
            data.append(tag.tag_id)
            query = "UPDATE tag SET name=$1, photo=$2 WHERE id=$3 RETURNING id"
        else:
            query = "INSERT INTO tag(name, photo_id) VALUES($1, $2) RETURNING id"
        try:
            tag_id = await conn.fetchrow(query, *data)
        finally:
            await self.pool.release(conn)
        return tag_id

    async def delete_tag(self, tag_id: int) -> None:
        """
        Delete tag from database
        :param tag_id: ID of the tag to remove
        """
        conn = await self.pool.acquire()
        query = "DELETE FROM tag WHERE id=$1"
        try:
            await conn.fetchrow(query, tag_id)
        finally:
            await self.pool.release(conn)

    async def get_stats(self) -> list:
        """
        Retrieve photo and camera stats from database
        :return: stats
        """
        conn = await self.pool.acquire()
        query = """SELECT photo.id,extract(epoch from moment)::bigint as moment,lat,lng,size,make,model,
                width, height FROM photo LEFT OUTER JOIN camera on photo.camera_id = camera.id"""
        try:
            stats = await conn.fetch(query)
        finally:
            await self.pool.release(conn)
        return stats

    async def get_user_by_key(self, key: str, source: str) -> dict | None:
        """
        Return first user matching username
        :param key: user key to search for
        :param source: source to filter by (local, google)
        :return user
        """
        conn = await self.pool.acquire()
        query = "SELECT key,name,username,password FROM users WHERE key=$1 AND source=$2"
        try:
            user = await conn.fetchrow(query, key, source)
        finally:
            await self.pool.release(conn)
        return user

    async def add_user(self, key: str, source: str, name: str, email: str, username: str, password: str) -> None:
        """
        Add new user to database
        :param key: user key (id for Google accounts, username for local account)
        :param source: source to filter by (local, google)
        :param name: full name for the new user
        :param email: email address
        :param username: username (email for Google accounts)
        :param password: user password (empty for Google accounts)
        """
        conn = await self.pool.acquire()
        query = "INSERT INTO users(key,source,name,email,username,password,level) VALUES($1,$2,$3,$4,$5,$6,$7)"
        try:
            await conn.fetchrow(query, key, source, name, email, username, password, 1)
        finally:
            await self.pool.release(conn)

    async def create_structure(self) -> None:
        """
        Ensure table and index structure exists
        """
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
                    filename text NOT NULL,
                    width smallint NOT NULL,
                    height smallint NOT NULL,
                    size integer NOT NULL,
                    camera_id integer,
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
            """CREATE TABLE IF NOT EXISTS tag(
                    id serial NOT NULL,
                    name text NOT NULL UNIQUE
            )""",
            "CREATE INDEX IF NOT EXISTS tag_name_idx ON tag USING btree(name)",
            """CREATE TABLE IF NOT EXISTS photo_tags(
                  id serial NOT NULL,
                  tag_id integer REFERENCES tag(id),
                  photo_id integer REFERENCES photo(id)
            )""",
            "CREATE INDEX IF NOT EXISTS tag_id_idx ON photo_tags USING btree(tag_id)",
            "CREATE INDEX IF NOT EXISTS tag_photo_id_idx ON photo_tags USING btree(photo_id)",
            """CREATE TABLE IF NOT EXISTS users(
                id serial PRIMARY KEY,
                key text UNIQUE NOT NULL,
                source text NOT NULL,
                name text NOT NULL,
                email text UNIQUE NOT NULL,
                username text UNIQUE NOT NULL,
                password text,
                level smallint NOT NULL
            )""",
            "CREATE INDEX IF NOT EXISTS user_key_idx ON users USING btree(key);",
        ]
        conn = await self.pool.acquire()
        for query in queries:
            try:
                await conn.fetch(query)
            except asyncpg.PostgresError as exc:
                logger.error("cannot run query: %s", exc)
        await self.pool.release(conn)

    # @property
    # def gear_level(self) -> int:
    #     return self._gear_level
    #
    # @gear_level.setter
    # def gear_level(self, value: int) -> None:
    #     self._gear_level = min(max(value, 0), 5)
