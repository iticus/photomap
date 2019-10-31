"""
Created on Nov 1, 2015

@author: ionut
"""

import logging
import signal
import time
import tornado.ioloop
import tornado.web
from tornado import gen
from tornado.options import options, define

import handlers
import settings
from settings import STATUS as status

define("port", default=8001, help="listen port", type=int)
logging.basicConfig(level=settings.LOG_LEVEL, datefmt="%Y-%m-%d %H:%M:%S",
                    format="[%(asctime)s] - %(levelname)s - %(message)s")


@gen.engine
def app_exit():
    """
    Wait for tasks to finish and exit
    """
    i = 0
    while i < 9:  # supervisord waits 10 seconds before sending SIGKILL
        if status["busy"] <= 0:
            break
        i += 1
        logging.info("waiting %d seconds for tasks to finish", (9-i))
        yield gen.Task(tornado.ioloop.IOLoop.instance().add_timeout, time.time() + 1)

    if status["busy"] <= 0:
        logging.info("exited cleanly after %d iterations", i)
    else:
        logging.error("forced exit after %d iterations", i)

    logging.info("stopping IOloop...")
    tornado.ioloop.IOLoop.instance().stop()


def configure_signals():
    """
    Configure signal handling for exiting
    """

    def stopping_handler(signum, frame):
        logging.info("interrupt signal %s:%s received, shutting down", signum, frame)
        app_exit()

    signal.signal(signal.SIGINT, stopping_handler)
    signal.signal(signal.SIGTERM, stopping_handler)


def main():
    """
    start main Tornado application instance
    """
    configure_signals()
    options.parse_command_line()
    application = tornado.web.Application(
        [
            (r"/", handlers.BaseHandler),
            (r"/map/?", handlers.MapHandler),
            (r"/geotag/?([^/]+)?/?", handlers.GeoHandler),
            (r"/stats/?([^/]+)?/?", handlers.StatsHandler),
            (r"/upload/?", handlers.UploadHandler),
            (r"/media/(.*)", tornado.web.StaticFileHandler, {"path": settings.MEDIA_PATH}),
        ],
        debug=settings.DEBUG, gzip=True,
        template_path=settings.TEMPLATE_PATH,
        static_path=settings.STATIC_PATH
    )

    logging.info("starting photomap on port %d ...", options.port)

    application.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
