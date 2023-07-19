"""
Created on 2023-01-07

@author: iticus
"""
from aiohttp import web


async def test_homepage(photomap_app: web.Application) -> None:
    """Test that the homepage responds with 200 and contains the page title"""
    request = await photomap_app.get("/")
    assert request.status == 200
    response = await request.text()
    assert "<title>Photomap</title>" in response
    assert "bootstrap.bundle.min.js" in response


async def test_map(photomap_app: web.Application) -> None:
    """Test that the map page contains the expected elements"""
    request = await photomap_app.get("/map")
    assert request.status == 200
    response = await request.text()
    assert "<title>Main map - photomap</title>" in response
    assert "photos.push({" in response
    assert '<div id="mapCanvas" class="d-flex"></div>' in response
    assert '<script type="text/javascript" src="/static/js/leaflet.markercluster.js"></script>' in response
    assert "leaflet.js" in response
    assert "bootstrap.bundle.min.js" in response


async def test_geotag(photomap_app: web.Application) -> None:
    """Test that the geotagging page contains the expected elements"""
    request = await photomap_app.get("/geotag")
    assert request.status == 200
    response = await request.text()
    assert "<title>geotag photos - photomap</title>" in response
    assert "leaflet.js" in response
    assert '<div id="map" class="d-flex"></div>' in response
    assert '<div id="photoList">' in response
    assert '<button name="button" class="btn btn-success" onClick="filterPhotos()">Filter</button>' in response


async def test_geotag_ajax(photomap_app: web.Application) -> None:
    """Test that the geotag AJAX request returns non tagged images"""
    params = {"op": "get_photo_list", "start_filter": "2020-01-01", "stop_filter": "2021-01-01"}
    request = await photomap_app.get("/geotag", params=params)
    assert request.status == 200
    data = await request.json()
    assert isinstance(data, list)
    assert len(data) == 30
    photo = data[0]
    assert "height" in photo
    assert "width" in photo
    assert "lat" not in photo
    assert "lng" not in photo
    assert isinstance(photo["make"], str) or photo["make"] is None
    assert isinstance(photo["model"], str) or photo["model"] is None


async def test_stats(photomap_app: web.Application) -> None:
    """Test that the stats page renders the template correctly"""
    request = await photomap_app.get("/stats")
    response = await request.text()
    assert request.status == 200
    assert "<title>stats - photomap</title>" in response
    assert '<script type="text/javascript" src="https://www.google.com/jsapi"></script>' in response
    assert '<div id="tableChart">' in response
    assert "https://maps.googleapis.com/maps/api/js?key=" not in response


async def test_stats_ajax(photomap_app: web.Application) -> None:
    """Test that the stats AJAX request returns all photo details"""
    request = await photomap_app.get("/stats", params={"op": "get_stats"})
    assert request.status == 200
    data = await request.json()
    assert isinstance(data, list)
    assert 10000 < len(data) < 30000  # there are around 20k photos
    photo = data[0]
    assert "height" in photo
    assert "width" in photo
    assert "lat" in photo
    assert "lng" in photo
    assert isinstance(photo["moment"], int) or photo["moment"] is None
