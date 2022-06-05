"""
Created on May 24, 2016

@author: iticus
"""

import datetime
import hashlib
import json
import logging
import os
from io import BytesIO

import aiohttp_jinja2
from aiohttp import web

from PIL import Image as PilImage
from aiohttp.web_fileresponse import FileResponse
from aiohttp_session import get_session

import cache
import database
import utils
import settings


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
        context = {"images": images}
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
        return aiohttp_jinja2.render_template("geotag.html", self.request, context={})

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
            response = await database.raw_query(query, data)
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
        self.render("upload.html")

    async def post(self):
        secret = self.get_argument("secret", "")
        if secret != settings.SECRET:
            self.finish("wrong secret")
            return

        images = await database.raw_query("SELECT ihash FROM image", ())
        hashes = set()
        for image in images:
            hashes.add(image[0])

        fileinfo = self.request.files["image"][0]
        sha1 = hashlib.sha1()
        sha1.update(fileinfo["body"])
        ihash = sha1.hexdigest()

        if ihash in hashes:
            logging.info("image %s already imported", ihash)
            self.finish("already imported")
            return

        exif_data = parse_exif(fileinfo["body"])
        size = len(fileinfo["body"])
        image = database.Image(
            ihash=ihash, description="", album=None,
            moment=moment, width=width, height=height, orientation=orientation,
            filename=fileinfo["filename"], size=size, path="",
            lat=lat, lng=lng, altitude=altitude, gps_ref="".join(gps_ref), access=0
        )

        cameras = yield database.raw_query("SELECT id, make, model FROM camera", ())
        camera_dict = {}
        for camera in cameras:
            camera_dict[camera[1] + "_" + camera[2]] = camera

        if camera_make or camera_model:
            key = camera_make + "_" + camera_model
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
        path = "pic" + str(int(image_id/1000))
        image.path = path
        path = "original/" + path

        image_file = PilImage.open(BytesIO(fileinfo["body"]))
        directory = settings.MEDIA_PATH + "/" + path
        if not os.path.exists(directory):
            os.makedirs(directory)

        output_file = open(directory + "/" + image.ihash, "wb")
        output_file.write(fileinfo["body"])
        output_file.close()

        resolutions = [(64, 64), (192, 192), (960, 960)]
        for resolution in resolutions:
            directory = settings.MEDIA_PATH + "/thumbnails/" + str(resolution[0])
            directory += "px/pic" + str(int(image_id)/1000)
            if not os.path.exists(directory):
                os.makedirs(directory)
            outfile = directory + "/" + image.ihash
            utils.make_thumbnail(image_file, outfile, resolution[0], resolution[1])

        database.raw_query("UPDATE image SET path=%s WHERE id=%s RETURNING id",
                           (image.path, image_id))
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
