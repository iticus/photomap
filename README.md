## photomap

### About

The aim of this project is to provide a way for users to view / manage their photos and albums on a map. I decided to create it while traveling in my home country (Romania). The project development started using [Django](https://www.djangoproject.com/) but has been recently ported to [Tornado](http://www.tornadoweb.org/en/stable/) and then to [aiohttp](https://docs.aiohttp.org/en/stable/).
Some functions (check screenshots below):

- show all geo-tagged photos from the database on the map
- manually tag photos (drag the un-tagged photos on the map to update the location)
- support for albums, cameras and tags (to be completed)
- helper scripts: multicore import script (for bulk uploading), various "fixing" scripts
- position auto-detection algorithms (based on timestamp, uploaded tracks etc.) - to be added
- stats page - to be completed

### Demo

I will try to get a running version of this software on my home Raspberry PI.
You can view some screenshots of the development version running on my laptop [here](http://iticus.ro/projects/photomap_screenshots).

### Requirements

This web application is written in [Python](https://www.python.org/) and uses the following packages:

- [Tornado](http://www.tornadoweb.org/en/stable/) for the webserver part
- [momoko](https://github.com/FSX/momoko) for the database part
- [pillow](https://python-pillow.github.io/) for image resizing
- [pyexiv2](http://tilloy.net/dev/pyexiv2/) for EXIF data handling
- other APIs used: [Google Maps Javascript](https://developers.google.com/maps/documentation/javascript/), [jQuery](https://jquery.com/), MarkerClusterer

### Installation

- install the above packages
- copy the settings file (`cp settings_default.py settings.py`)
- edit the settings (mainly `DSN`, `SECRET` and **_paths_**)
- make sure you have [PostgreSQL](http://www.postgresql.org/) running and the database is created (you can use the create statements from the database.py file)
- start the application `python -u photomap.py &>> photomap.log &` or use the provided `supervisor.ini` file
