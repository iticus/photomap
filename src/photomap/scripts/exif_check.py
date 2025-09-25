"""
Created on Sep 19, 2012

@author: ionut
"""

import asyncio
import os

import piexif

import database
from settings import MEDIA_PATH
from utils import exif2gps


async def main() -> None:
    """
    Main loop to check exif data against already imported photos
    """
    images = await database.raw_query("SELECT id, ihash, lat, lng, altitude, path, filename from image", ())
    base_dir = os.path.join(MEDIA_PATH, "original")
    for image in images:
        if not image[3]:
            continue
        file_path = os.path.join(base_dir, image[5], image[1])
        if not os.path.isfile(file_path):
            print(f"missing file {file_path}, filename {image[6]}")
            continue
        input_file = open(file_path, "rb")
        try:
            file_content = input_file.read()
            exif_data = piexif.load(file_content)
            # size = input_file.tell()
            lat = 0
            lng = 0
            altitude = 0
            if exif_data.get("GPS", {}).get(piexif.GPSIFD.GPSLatitude):
                lat = exif2gps(exif_data.get("GPS", {}).get(piexif.GPSIFD.GPSLatitude))
            if exif_data.get("GPS", {}).get(piexif.GPSIFD.GPSLongitude):
                lng = exif2gps(exif_data.get("GPS", {}).get(piexif.GPSIFD.GPSLongitude))
            if exif_data.get("GPS", {}).get(piexif.GPSIFD.GPSAltitude):
                altitude = exif_data.get("GPS", {}).get(piexif.GPSIFD.GPSAltitude)
                if isinstance(altitude, tuple):
                    altitude = altitude[0] / altitude[1]
            if not lat:
                continue
            if image[2] - lat > 0.00001 or image[3] - lng > 0.00001 or image[4] - altitude > 0.00001:
                print(f"coordinate mismatch for {image[6]}, path {image[5]}, {lat}:{lng}")
                # image.save()
        except Exception as exc:  # pylint: disable=broad-exception-caught
            print(exc)
        input_file.close()


if __name__ == "__main__":
    asyncio.run(main())
