"""
Created on 2022-06-04

@author: iticus
"""

import datetime
import os
from io import BytesIO

import piexif
from PIL import Image as PilImage

import utils
from database import Photo


def parse_exif(file_body: bytes, image_file: PilImage) -> dict[str, str | float | int | datetime.datetime]:
    """
    Parse EXIF data from image bytes
    :param file_body: raw image data
    :param image_file: Pil image object
    :return: exif data
    """
    exif_data = piexif.load(file_body)
    width = exif_data.get("Exif", {}).get(piexif.ExifIFD.PixelXDimension, None) or image_file.width
    height = exif_data.get("Exif", {}).get(piexif.ExifIFD.PixelYDimension, None) or image_file.height
    gps_ref = ["N", "E", "0"]
    lat = None
    lng = None
    altitude = None

    if "GPS" in exif_data:
        lat = utils.exif2gps(exif_data["GPS"].get(piexif.GPSIFD.GPSLatitude))
        lng = utils.exif2gps(exif_data["GPS"].get(piexif.GPSIFD.GPSLongitude))
        altitude = exif_data["GPS"].get(piexif.GPSIFD.GPSAltitude)
        if isinstance(altitude, tuple):
            if altitude[1] == 0:  # avoid division by 0
                altitude = 0
            else:
                altitude = altitude[0] / altitude[1]
        if altitude and altitude > 12000:  # some cameras set a huge number for alt (like 4294967275)
            altitude = 0
        if piexif.GPSIFD.GPSLatitudeRef in exif_data["GPS"]:
            ref = exif_data["GPS"].get(piexif.GPSIFD.GPSLatitudeRef, b"").decode()
            if gps_ref[0] == "S":
                gps_ref[0] = ref
                lat = -1 * lat
        if piexif.GPSIFD.GPSLongitudeRef in exif_data["GPS"]:
            ref = exif_data["GPS"].get(piexif.GPSIFD.GPSLongitudeRef, b"").decode()
            if gps_ref[0] == "W":
                gps_ref[1] = ref
                lng = -1 * lng
        if piexif.GPSIFD.GPSAltitudeRef in exif_data["GPS"]:
            ref = str(exif_data["GPS"].get(piexif.GPSIFD.GPSAltitudeRef, ""))
            if ref != "\x00":
                gps_ref[2] = ref

    camera_make = exif_data["0th"].get(piexif.ImageIFD.Make, b"").decode().strip("\x00")
    camera_model = exif_data["0th"].get(piexif.ImageIFD.Model, b"").decode().strip("\x00")
    if camera_make in camera_model:
        camera_model = camera_model.replace(camera_make, "").strip()
    orientation = exif_data["0th"].get(piexif.ImageIFD.Orientation, 1)
    if orientation == 0:
        orientation = 1  # some panorama images have orientation = 0 which is invalid
    moment = exif_data["0th"].get(piexif.ImageIFD.DateTime, b"1970:01:01 00:00:00")
    if moment == b"0000:00:00 00:00:00":
        moment = b"1970:01:01 00:00:00"  # fix bad timestamp in EXIF data
    moment = datetime.datetime.strptime(moment.decode(), "%Y:%m:%d %H:%M:%S")
    return {
        "moment": moment,
        "camera_make": camera_make,
        "camera_model": camera_model,
        "lat": lat,
        "lng": lng,
        "orientation": orientation,
        "width": width,
        "height": height,
        "altitude": altitude,
        "gps_ref": gps_ref,
        "size": len(file_body),
    }


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


def load_image(file_body: bytes) -> PilImage:
    """
    Load the raw image data into a PIL image object
    :param file_body: raw image data
    :return: PIL image
    """
    image_file = PilImage.open(BytesIO(file_body))
    return image_file
