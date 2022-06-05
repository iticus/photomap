"""
Created on Nov 1, 2015

@author: ionut
"""

import logging

# Logging config
logging.basicConfig(
    level=logging.INFO, datefmt="%Y-%m-%d %H:%M:%S",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# webapp settings
ADDRESS = "0.0.0.0"
PORT = 8000

# Database settings
DSN = "dbname=photomap user=postgres password=pwd host=127.0.0.1 port=5432"

# REDIS settings
REDIS_HOST = "127.0.0.1"
REDIS_PORT = 6379

GOOGLE_MAPS_KEY = "change me"

MEDIA_PATH = "/home/iticus/nginx/media"
SECRET = "some_secret"
