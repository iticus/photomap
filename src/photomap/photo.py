"""
Created on 2022-06-04

@author: iticus
"""

import datetime
import logging
import os
from io import BytesIO

import piexif
from PIL import Image as PilImage
from PIL import ImageOps

import utils
from database import Photo

logger = logging.getLogger(__name__)


def parse_location(exif: dict) -> dict:
    """
    Parse latitude, longitude from EXIF GPS data
    :param exif: exif details loaded from image
    :return: lat, lng, altitude
    """
    location = {"lat": None, "lng": None, "altitude": None}
    if "GPS" not in exif:
        return location
    location["lat"] = utils.exif2gps(exif["GPS"].get(piexif.GPSIFD.GPSLatitude))
    location["lng"] = utils.exif2gps(exif["GPS"].get(piexif.GPSIFD.GPSLongitude))
    location["altitude"] = exif["GPS"].get(piexif.GPSIFD.GPSAltitude)
    if isinstance(location["altitude"], tuple):
        # pylint: disable=unsubscriptable-object
        if location["altitude"][1] != 0:
            location["altitude"] = location["altitude"][0] / location["altitude"][1]
        else:
            logger.warning("invalid altitude value: %s", location["altitude"])
            location["altitude"] = 0
    # some cameras set a huge number for alt (like 4294967275)
    if location["altitude"] and location["altitude"] > 12000:
        location["altitude"] = 0
    if piexif.GPSIFD.GPSLatitudeRef in exif["GPS"]:
        ref = exif["GPS"].get(piexif.GPSIFD.GPSLatitudeRef, b"").decode()
        if ref == "S":  # south latitude
            assert isinstance(location["lat"], float)
            location["lat"] = -1 * location["lat"]
    if piexif.GPSIFD.GPSLongitudeRef in exif["GPS"]:
        ref = exif["GPS"].get(piexif.GPSIFD.GPSLongitudeRef, b"").decode()
        if ref == "W":  # west longitude
            assert isinstance(location["lng"], float)
            location["lng"] = -1 * location["lng"]
    if piexif.GPSIFD.GPSAltitudeRef in exif["GPS"]:
        ref = exif["GPS"].get(piexif.GPSIFD.GPSAltitudeRef, b"").decode()
        if ref == 1:  # below sea level
            assert isinstance(location["lat"], float)
            location["altitude"] = -1 * location["altitude"]
    return location


def parse_exif(file_body: bytes) -> dict:
    """
    Parse EXIF data from image bytes
    :param file_body: raw image data
    :return: exif data
    """
    exif_data = piexif.load(file_body)
    camera_make = exif_data["0th"].get(piexif.ImageIFD.Make, b"").decode().strip("\x00")
    camera_model = exif_data["0th"].get(piexif.ImageIFD.Model, b"").decode().strip("\x00")
    if camera_make in camera_model:
        camera_model = camera_model.replace(camera_make, "").strip()
    moment = exif_data["0th"].get(piexif.ImageIFD.DateTime, b"1970:01:01 00:00:00")
    if moment == b"0000:00:00 00:00:00":
        moment = b"1970:01:01 00:00:00"  # fix bad timestamp in EXIF data
    moment = datetime.datetime.strptime(moment.decode(), "%Y:%m:%d %H:%M:%S")
    data = {
        "moment": moment,
        "camera_make": camera_make,
        "camera_model": camera_model,
        "orientation": exif_data["0th"].get(piexif.ImageIFD.Orientation, 1) or 1,
        "width": exif_data.get("Exif", {}).get(piexif.ExifIFD.PixelXDimension, None),
        "height": exif_data.get("Exif", {}).get(piexif.ExifIFD.PixelYDimension, None),
        "size": len(file_body),
    }
    data.update(parse_location(exif_data))
    return data


def make_thumbnails(image_file: PilImage, photo: Photo, base_path: str, overwrite: bool = False) -> None:
    """
    Create thumbnails for provided image
    :param image_file: Pil Image object
    :param photo: database photo object
    :param base_path: base path to store the thumbnails in
    :param overwrite: flag to create a new thumbnail even if one already exists
    """
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    resolutions = [(64, 64), (192, 192), (960, 960)]
    for resolution in resolutions:
        directory = os.path.join(base_path, "thumbnails", f"{resolution[0]}px")
        directory = utils.generate_path(directory, photo.ihash)
        if not os.path.exists(directory):
            os.makedirs(directory)
        outfile = os.path.join(directory, photo.ihash)
        if not os.path.isfile(outfile) or overwrite:
            utils.make_thumbnail(image_file, outfile, resolution[0], resolution[1])


def load_image(file_body: bytes, photo: Photo) -> PilImage:
    """
    Load the raw image data into a PIL image object, optionally rotating it
    :param file_body: raw image data
    :param photo: photo object to check orientation
    :return: PIL image
    """
    image_file = PilImage.open(BytesIO(file_body))
    if photo.orientation != 1:
        image_file = ImageOps.exif_transpose(image_file)
    return image_file
