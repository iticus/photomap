"""
Created on 2022-06-04

@author: iticus
"""

import piexif


def parse_exif(exif_data):
    width = -1
    height = -1
    gps_ref = ["N", "E", "0"]
    lat = None
    lng = None
    altitude = None

    if piexif.ExifIFD.PixelXDimension in exif_data.get("Exif", {}):
        width = exif_data["Exif"][piexif.ExifIFD.PixelXDimension]
    if piexif.ExifIFD.PixelYDimension in exif_data.get("Exif", {}):
        height = exif_data["Exif"][piexif.ExifIFD.PixelYDimension]

    if "GPS" in exif_data:
        lat = utils.exif2gps(exif_data["GPS"].get(piexif.GPSIFD.GPSLatitude))
        lng = utils.exif2gps(exif_data["GPS"].get(piexif.GPSIFD.GPSLongitude))
        altitude = exif_data["GPS"].get(piexif.GPSIFD.GPSAltitude)
        if isinstance(altitude, tuple):
            altitude = altitude[0] / altitude[1]

        if piexif.GPSIFD.GPSLatitudeRef in exif_data["GPS"]:
            gps_ref[0] = exif_data["GPS"].get(piexif.GPSIFD.GPSLatitudeRef, b"").decode()
            if gps_ref[0] == "S":
                lat = -1 * lat
        if piexif.GPSIFD.GPSLongitudeRef in exif_data["GPS"]:
            gps_ref[1] = exif_data["GPS"].get(piexif.GPSIFD.GPSLongitudeRef, b"").decode()
            if gps_ref[0] == "W":
                lng = -1 * lng
        if piexif.GPSIFD.GPSAltitudeRef in exif_data["GPS"]:
            gps_ref[2] = str(exif_data["GPS"].get(piexif.GPSIFD.GPSAltitudeRef, ""))

    camera_make = exif_data["0th"].get(piexif.ImageIFD.Make, b"").decode().strip("\x00")
    camera_model = exif_data["0th"].get(piexif.ImageIFD.Model, b"").decode().strip("\x00")
    if camera_make in camera_model:
        camera_model = camera_model.replace(camera_make, "").strip()
    orientation = exif_data["0th"].get(piexif.ImageIFD.Orientation, -1)
    moment = exif_data["0th"].get(piexif.ImageIFD.DateTime, b"1970:01:01 00:00:00")
    moment = datetime.datetime.strptime(moment.decode(), "%Y:%m:%d %H:%M:%S")
