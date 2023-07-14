"""
Created on Nov 1, 2015

@author: ionut
"""

import logging
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


# webapp settings
ADDRESS = "0.0.0.0"
PORT = 8000

# Database settings
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
POSTGRES_DB = os.getenv("POSTGRES_DB", "photomap")

# REDIS settings
REDIS_HOST = "127.0.0.1"
REDIS_PORT = 6379

TEMPLATE_PATH = "templates"
STATIC_PATH = "static"
MEDIA_PATH = "/media/data/work/photomap/media"

GOOGLE_MAPS_KEY = os.getenv("GOOGLE_MAPS_KEY", "")

SECRET = os.getenv("SECRET", "")
