"""
Created on Nov 1, 2015

@author: iticus
"""

import asyncio
import logging
import os
from concurrent.futures import ProcessPoolExecutor

import aiohttp_jinja2
import jinja2
from aiohttp import web
from aiohttp_session import setup
from aiohttp_session.redis_storage import RedisStorage
from redis import asyncio as aioredis

import settings
import views
from database import Database
from middlewares import error_middleware

logger = logging.getLogger(__name__)


async def startup(app: web.Application) -> None:
    """
    Establish database and cache connections
    :param app: application instance
    """
    logger.info("connecting to database")
    await app.database.connect()
    await app.database.create_structure()
    logger.info("connecting to REDIS instance")
    redis_address = f"redis://{app.config.REDIS_HOST}:{app.config.REDIS_PORT}"
    app.redis = await aioredis.from_url(redis_address)
    storage = RedisStorage(app.redis, max_age=86400)
    setup(app, storage)


async def shutdown(app: web.Application) -> None:
    """
    Gracefully disconnect from database and cache servers
    :param app: application instance
    """
    logger.info("disconnecting from database")
    await app.database.disconnect()
    logger.info("disconnecting from redis")
    await app.redis.close()
    for task in asyncio.all_tasks():
        task.cancel()
    await asyncio.sleep(0.1)


def make_app() -> web.Application:
    """
    Main function to create the web application object
    :return: web application
    """
    app = web.Application(client_max_size=64 * 1000 * 1000)
    app.router.add_view("/", views.Home)
    app.router.add_view("/map{tail:.*?}", views.Map)
    app.router.add_view("/login{tail:.*?}", views.Login)
    app.router.add_view("/logout{tail:.*?}", views.Logout)
    app.router.add_view("/geotag{tail:.*?}", views.Geo)
    app.router.add_view("/stats{tail:.*?}", views.Stats)
    app.router.add_view("/upload{tail:.*?}", views.Upload)
    path = os.path.join(os.getcwd(), "static")
    app.router.add_static("/static", path)
    app.router.add_static("/media", settings.MEDIA_PATH)
    app.router.add_view("/favicon.ico", views.Favicon)
    app.middlewares.append(error_middleware)
    app.executor = ProcessPoolExecutor(max_workers=12)
    app.config = settings
    app.database = Database(
        settings.POSTGRES_USER,
        settings.POSTGRES_PASSWORD,
        settings.POSTGRES_HOST,
        settings.POSTGRES_PORT,
        settings.POSTGRES_DB,
    )
    path = os.path.join(os.getcwd(), "templates")
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(path))
    app.on_startup.append(startup)
    app.on_shutdown.append(shutdown)
    return app


def main() -> None:
    """Start aiohttp server application instance"""
    application = make_app()
    logger.info("starting photomap on %s:%s ...", application.config.ADDRESS, application.config.PORT)
    web.run_app(application, host=application.config.ADDRESS, port=application.config.PORT, access_log=None)


if __name__ == "__main__":
    main()
