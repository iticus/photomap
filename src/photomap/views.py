"""
Created on May 24, 2016

@author: iticus
"""

import asyncio
import datetime
import hashlib
import logging
from functools import partial
from typing import Any, Callable

import aiohttp_jinja2
from aiohttp import web
from aiohttp.web_fileresponse import FileResponse
from aiohttp_session import get_session, new_session

import cache
import database
import security
from photo import load_image, make_thumbnails, parse_exif

logger = logging.getLogger(__name__)


class BaseView(web.View):
    """Base View to be inherited / implemented by subsequent views"""

    def __init__(self, request: web.Request) -> None:
        super().__init__(request)
        self.config = self.request.app.config
        self.database = self.request.app.database
        self.cache = self.request.app.cache

    @staticmethod
    def authenticated(func: Callable) -> Callable:
        """
        Decorator for checking authentication for requests
        :param func: function to decorate
        :return: decorator
        """

        async def wrapped(self: web.Request, *args: Any, **kwargs: Any) -> Any:
            self.session = await get_session(self.request)
            if "email" not in self.session:
                next_url = self.request.rel_url or "/"
                return web.HTTPFound(f"/login?next={next_url}")
            result = await func(self, *args, **kwargs)
            return result

        return wrapped

    async def get(self) -> web.Response:
        """Implement GET request in this function"""

    async def post(self) -> web.Response:
        """Implement POST request in this function"""


class Home(BaseView):
    """
    Main view for /
    """

    async def get(self) -> web.Response:
        return aiohttp_jinja2.render_template("home.html", self.request, context={})


class Login(BaseView):
    """Handle login page and POST request"""

    async def get(self) -> web.Response:
        message = self.request.query.get("message")
        next_url = self.request.query.get("next", "/")
        context = {"message": message, "next_url": next_url}
        return aiohttp_jinja2.render_template("login.html", self.request, context=context)

    async def post(self) -> web.Response:
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
    """Logout user"""

    @BaseView.authenticated
    async def post(self) -> web.Response:
        session = await get_session(self.request)
        session.invalidate()
        return web.HTTPFound(location="/")


class Map(BaseView):
    """
    Main view for /map (main map)
    """

    async def get(self) -> web.Response:
        if self.request.query.get("op") == "photos":
            photos = await cache.get_value(self.cache, "geotagged_photos")
            if not photos:
                photos = await self.database.get_geotagged_photos()
                photos = [dict(photo) for photo in photos]
                await cache.set_value(self.cache, "geotagged_photos", photos)
            return web.json_response(photos)
        # "session": self.session
        return aiohttp_jinja2.render_template("map.html", self.request, context={})


class Geo(BaseView):
    """
    View for manually geotagging photos (/geotag)
    """

    async def get(self) -> web.Response:
        op = self.request.query.get("op")
        if op == "get_photo_list":
            start_dt = datetime.datetime.strptime(self.request.query.get("start_filter", "2020-12-01"), "%Y-%m-%d")
            stop_dt = datetime.datetime.strptime(self.request.query.get("stop_filter", "2021-12-01"), "%Y-%m-%d")
            photos = await self.database.get_photos_nogps(start_dt, stop_dt)
            return web.json_response([dict(photo) for photo in photos])
        return aiohttp_jinja2.render_template("geotag.html", self.request, context={})

    async def post(self) -> web.Response:
        op = self.request.query.get("op")
        if op == "update_location":
            data = await self.request.json()
            ihash = data.get("hash", "unknown")
            try:
                photo_id = int(data.get("id", ""))
                lat = float(data.get("lat", ""))
                lng = float(data.get("lng", ""))
            except ValueError:
                return web.json_response({"status": "error", "details": "lat and/or lng invalid"}, status=400)
            response = await self.database.update_photo_location(photo_id, ihash, lat, lng)
            if response:
                await cache.del_value(self.cache, "geotagged_photos")
                await cache.del_value(self.cache, "stats")
                return web.json_response({"status": "ok", "details": "photo location updated successfully"})
            return web.json_response({"status": "error", "details": "photo location not updated"}, status=400)
        return web.json_response({"status": "error", "details": "unknown operation"}, status=400)


class Photo(BaseView):
    """
    View for retrieving photo details
    """

    async def get(self) -> web.Response:
        photo_id = self.request.query.get("photo_id")
        if not photo_id or not photo_id.isdigit():
            return web.json_response({"status": "error", "details": "provide photo_id"}, status=400)
        photo = await self.database.get_photo(int(photo_id))
        if not photo:
            return web.json_response({"status": "error", "details": "no photo found for this ID"}, status=404)
        return web.json_response({"status": "ok", "photo": dict(photo)})


class Upload(BaseView):
    """
    Handler for uploading pictures (manually or via import script)
    """

    async def get(self) -> web.Response:
        return aiohttp_jinja2.render_template("upload.html", self.request, context={})

    async def post(self) -> web.Response:
        secret = self.request.headers.get("Authentication", "")
        if secret != self.config.SECRET:
            return web.json_response({"status": "error", "details": "invalid secret value"}, status=403)
        # TODO: use local cache for photo data
        all_photo_ihash = await self.database.get_all_ihash()
        hashes = {photo["ihash"] for photo in all_photo_ihash}
        data = await self.request.post()
        fileinfo = data["photo"]
        filename = data["filename"]
        file_body = fileinfo.file.read()
        sha1 = hashlib.sha1()
        sha1.update(file_body)
        ihash = sha1.hexdigest()
        if ihash in hashes:
            logger.debug("photo %s, %s already imported", ihash, filename)
            return web.json_response({"status": "error", "details": "photo hash already exists"}, status=409)
        loop = asyncio.get_running_loop()
        executor = self.request.app.executor
        exif_data = await loop.run_in_executor(executor, partial(parse_exif, file_body))
        photo = database.Photo(
            photo_id=None,
            camera=None,
            ihash=ihash,
            description="",
            album=None,
            moment=exif_data["moment"],
            width=exif_data["width"],
            height=exif_data["height"],
            filename=filename,
            size=exif_data["size"],
            lat=exif_data["lat"],
            lng=exif_data["lng"],
            altitude=exif_data["altitude"],
            gps_ref=exif_data["gps_ref"],
            access=1,
            orientation=exif_data["orientation"],
        )
        image_file = await loop.run_in_executor(executor, partial(load_image, file_body, photo))
        if photo.width is None:
            photo.width = image_file.width
        if photo.height is None:
            photo.height = image_file.height
        cameras = await self.database.get_cameras()
        camera_dict = {}
        for camera in cameras:
            camera_dict[camera[1] + "_" + camera[2]] = camera
        if exif_data["camera_make"] or exif_data["camera_model"]:
            key = exif_data["camera_make"] + "_" + exif_data["camera_model"]
            if key in camera_dict:
                photo.camera = camera_dict[key]["id"]
            else:
                camera = database.Camera(camera_id=None, make=exif_data["camera_make"], model=exif_data["camera_model"])
                result = await self.database.save_camera(camera)
                photo.camera = result["id"]
        else:
            photo.camera = None
        result = await self.database.save_photo(photo)
        photo_id = int(result["id"])
        await loop.run_in_executor(executor, partial(make_thumbnails, image_file, photo, self.config.MEDIA_PATH))
        await cache.del_value(self.cache, "geotagged_photos")
        await cache.del_value(self.cache, "stats")
        return web.json_response({"status": "ok", "message": f"photo saved, id {photo_id}"})


class Stats(BaseView):
    """
    Handler for rendering photo stats
    """

    async def get(self) -> web.Response:
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
    """Render about page"""

    @BaseView.authenticated
    async def get(self) -> web.Response:
        context = {"session": self.session}
        return aiohttp_jinja2.render_template("about.html", self.request, context=context)


class Favicon(BaseView):
    """Render static favicon file"""

    async def get(self) -> web.Response:
        return FileResponse("static/favicon.png")
