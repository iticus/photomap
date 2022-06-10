"""
Created on May 24, 2016

@author: iticus
"""

import datetime
import hashlib
import logging

import aiohttp_jinja2
from aiohttp import web

from aiohttp.web_fileresponse import FileResponse
from aiohttp_session import get_session, new_session

import cache
import database
from photo import parse_exif

logger = logging.getLogger(__name__)


class BaseView(web.View):
    """Base View to be inherited / implemented by subsequent views"""

    def __init__(self, request):
        super().__init__(request)
        self.config = self.request.app.config
        self.database = self.request.app.database
        self.cache = self.request.app.redis

    @staticmethod
    def authenticated(func):
        async def wrapped(self, *args, **kwargs):
            self.session = await get_session(self.request)
            if "email" not in self.session:
                next_url = self.request.rel_url or "/"
                return web.HTTPFound(f"/login?next={next_url}")
            result = await func(self, *args, **kwargs)
            return result
        return wrapped


class Home(BaseView):
    """
    Main view for /
    """

    async def get(self):
        return aiohttp_jinja2.render_template("home.html", self.request, context={})


class Login(BaseView):

    async def get(self):
        message = self.request.query.get("message")
        next_url = self.request.query.get("next", "/")
        context = {"message": message, "next_url": next_url}
        return aiohttp_jinja2.render_template("login.html", self.request, context=context)

    async def post(self):
        data = await self.request.post()
        if not data.get("email") or not data.get("password"):
            return web.HTTPFound(location="/login?message=provide email and password")
        user = self.database.get_user_by_email(data["email"])
        if not user:
            return web.HTTPFound(location="/login?message=no such user found")
        if not security.compare_pwhash(user["password"], data["password"]):
            return web.HTTPFound(location="/login?message=invalid password")
        session = await new_session(self.request)
        session["email"] = user["email"]
        next_url = self.request.query.get("next", "/")
        return web.HTTPFound(next_url)


class Logout(BaseView):

    @BaseView.authenticated
    async def post(self):
        session = await get_session(self.request)
        session.invalidate()
        return web.HTTPFound(location="/")


class Map(BaseView):
    """
    Main view for /map (main map)
    """

    async def get(self):
        images = await cache.get_value(self.cache, "geotagged_images")
        if not images:
            images = await self.database.get_geotagged_images()
            images = [dict(photo) for photo in images]
            await cache.set_value(self.cache, "geotagged_images", images)
        # "session": self.session
        context = {"images": images, "google_maps_key": self.config.GOOGLE_MAPS_KEY}
        return aiohttp_jinja2.render_template("map.html", self.request, context=context)


class Geo(BaseView):
    """
    View for manually geotagging photos (/geotag)
    """

    async def get(self):
        op = self.request.query.get("op")
        if op == "get_image_list":
            start_dt = datetime.datetime.strptime(self.request.query.get("start_filter", "2018-12-01"), "%Y-%m-%d")
            stop_dt = datetime.datetime.strptime(self.request.query.get("stop_filter", "2021-12-01"), "%Y-%m-%d")
            images = await self.database.get_images_nogps(start_dt, stop_dt)
            return web.json_response([dict(image) for image in images])
        context = {"google_maps_key": self.config.GOOGLE_MAPS_KEY}
        return aiohttp_jinja2.render_template("geotag.html", self.request, context=context)

    async def post(self, op):
        if op == "update_location":
            ihash = self.get_argument("hash", "unknown")
            iid = self.get_argument("id", 0)
            lat = self.get_argument("lat")
            lng = self.get_argument("lng")
            try:
                lat = float(lat)
                lng = float(lng)
            except ValueError:
                return self.finish("lat and/or lng invalid")

            query = """UPDATE image set lat=%s, lng=%s WHERE id=%s and ihash=%s RETURNING id"""
            data = (lat, lng, iid, ihash)
            response = await self.database.raw_query(query, data)
            if response:
                cache.del_value(self.cache, "geotagged_images")
                cache.del_value(self.cache, "stats")
                self.finish("image location updated successfully")
            else:
                self.set_status(400, "image location not updated")
                self.finish()

        else:
            self.finish("unknown op")


class Upload(BaseView):
    """
    Handler for uploading pictures (manually or via import script)
    """

    async def get(self):
        return aiohttp_jinja2.render_template("upload.html", self.request, context={})

    async def post(self):
        secret = self.request.headers.get("Authentication", "")
        if secret != self.config.SECRET:
            return web.json_response({"status": "error", "details": "invalid secret value"}, status=403)

        # TODO: use local cache for photo data
        geotagged_images = await self.database.get_geotagged_images()
        nogps_images = await self.database.get_images_nogps(datetime. datetime(1000, 1, 1), datetime.datetime(3000, 1, 1))
        hashes = set()
        for photo in geotagged_images + nogps_images:
            hashes.add(photo["ihash"])

        data = await self.request.post()
        fileinfo = data["image"]
        filename = fileinfo.filename
        file_body = fileinfo.file.read()
        sha1 = hashlib.sha1()
        sha1.update(file_body)
        ihash = sha1.hexdigest()

        if ihash in hashes:
            logger.info("image %s already imported", ihash)
            return web.json_response({"status": "error", "details": "invalid secret value"}, status=403)

        exif_data = parse_exif(file_body)
        size = len(file_body)
        photo = database.Photo(
            photo_id=None, camera=None, ihash=ihash, description="", album=None,
            moment=exif_data["moment"], width=exif_data["width"], height=exif_data["height"],
            orientation=exif_data["orientation"],filename=filename, size=size, path="",
            lat=exif_data["lat"], lng=exif_data["lng"], altitude=exif_data["altitude"],
            gps_ref="".join(exif_data["gps_ref"]), access=1
        )

        cameras = await self.database.get_cameras()
        camera_dict = {}
        for camera in cameras:
            camera_dict[camera[1] + "_" + camera[2]] = camera

        if exif_data["camera_make"] or exif_data["camera_model"]:
            key = exif_data["camera_make"] + "_" + exif_data["camera_model"]
            if key in camera_dict:
                photo.camera = camera_dict[key][0]
            else:
                camera = database.Camera(make=exif_data["camera_make"], model=exif_data["camera_model"])
                result = await camera.save()
                photo.camera = result["id"]
        else:
            photo.camera = None

        result = await photo.save()
        image_id = int(result["id"])
        path = "pic" + str(int(image_id/1000))
        photo.path = path
        path = "original/" + path

        database.raw_query("UPDATE image SET path=%s WHERE id=%s RETURNING id",
                           (photo.path, image_id))
        await cache.del_value(self.cache, "geotagged_images")
        await cache.del_value(self.cache, "stats")
        self.finish("image saved, id %d" % image_id)


class Stats(BaseView):
    """
    Handler for rendering image stats
    """

    async def get(self):
        op = self.request.query.get("op")
        if op == "get_stats":
            stats = await cache.get_value(self.cache, "stats")
            if not stats:
                stats = await self.database.get_stats()
                stats = [dict(stat) for stat in stats]
                await cache.set_value(self.cache, "stats", stats)
            return web.json_response(stats)
        return aiohttp_jinja2.render_template("stats.html", self.request, context={})


class About(BaseView):

    @BaseView.authenticated
    async def get(self):
        context = {"session": self.session}
        return aiohttp_jinja2.render_template("about.html", self.request, context=context)


class Favicon(BaseView):

    async def get(self):
        return FileResponse("static/favicon.png")
