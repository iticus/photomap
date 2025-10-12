let map;
let bounds;
let popup = null;
let loadedImages = new Set();

function createMarker(feature) {
    const el = document.createElement("div");
    el.className = "marker";
    el.style.backgroundImage = `url(${feature.properties.icon})`;
    el.style.width = "64px";
    el.style.height = "64px";
    el.addEventListener("click", () => {
        window.alert(marker.properties);
    });
    const marker = new maplibregl.Marker({element: el})
        .setLngLat(feature.geometry.coordinates)
        .addTo(map);
    return marker;
}

function loadPhotos() {
    bounds = new maplibregl.LngLatBounds();
    fetch("/map?op=photos").then(function (response) {
        return response.json()
    }).then(function (photos) {
        let geoData = {"type": "FeatureCollection", "features": []};
        photos.forEach((photo) => {
            let iconUrl = "/media/thumbnails/64px/" + photo.ihash[0] + "/" + photo.ihash[1] + "/" + photo.ihash;
            bounds.extend([photo.lng, photo.lat]);
            geoData.features.push({
                "type": "Feature",
                "properties": {"id": photo.id, "title": photo.filename, "icon": iconUrl},
                "geometry": {"type": "Point", "coordinates": [ photo.lng, photo.lat]}
            });
        });
        map.addSource("photos", {
            type: "geojson",
            data: geoData,
            cluster: true,
            clusterMaxZoom: 16, // Max zoom to cluster points on
            clusterRadius: 50 // Radius of each cluster when clustering points (defaults to 50)
        });
        map.addLayer({
            id: "photos",
            type: "circle",
            source: "photos",
            filter: ["has", "point_count"],
            paint: {
                // Use step expressions (https://maplibre.org/maplibre-style-spec/#expressions-step)
                // with three steps to implement three types of circles:
                //   * Blue, 20px circles when point count is less than 100
                //   * Yellow, 30px circles when point count is between 100 and 750
                //   * Pink, 40px circles when point count is greater than or equal to 750
                "circle-color": [
                    "step",
                    ["get", "point_count"],
                    "#51bbd6",
                    100,
                    "#f1f075",
                    750,
                    "#f28cb1"
                ],
                "circle-radius": [
                    "step",
                    ["get", "point_count"],
                    20,
                    100,
                    30,
                    750,
                    40
                ]
            }
        });

        map.addLayer({
            id: "unclustered-point",
            type: "symbol",
            source: "photos",
            filter: ["!", ["has", "point_count"]],
            layout: {
              "icon-image": ["get", "icon"], // the name of that image that you added
              "icon-size": 0.5, // Size of the icon
              "icon-allow-overlap": true,
            },
        });

        map.addLayer({
            id: "cluster-count",
            type: "symbol",
            source: "photos",
            filter: ["has", "point_count"],
            layout: {
                "text-field": "{point_count_abbreviated}",
                "text-font": ["Noto Sans Regular"],
                "text-size": 12
            }
        });
//        for (const feature of geoData.features) {
//            marker = createMarker(feature);
//            let marker = new maplibregl.Marker([feature.geometry.coordinates[0], feature.geometry.coordinates[1]], {
//                title: feature.properties.title,
////                icon: L.icon({iconUrl: iconUrl}),
//                image_id: feature.properties.id,
//                // draggable: true
//            });
//            marker.on("click", function (layer) {
//                fetch(`/photo?${new URLSearchParams({"photo_id": photo.id})}`, {method: "GET"})
//                    .then(response => response.json())
//                    .then(data => {
//                        if (data.status === "ok") {
//                            popup.setLatLng(point).setContent(generateInfoWindowContent(data.photo));
//                            let img = document.createElement("img");
//                            img.classList.add("rounded");
//                            img.style.cursor = "pointer";
//                            img.onclick = function () {
//                                showImage(data.photo);
//                            };
//                            // if (data.photo.orientation != 1)
//                            // 	img.style.transform = getRotation(data.photo.orientation);
//                            img.src = "/media/thumbnails/192px/" + photo.ihash[0] + "/" + photo.ihash[1] + "/" + photo.ihash;
//                            popup.openOn(map);
//                            let popupImg = document.getElementById("popupImg");
//                            popupImg.appendChild(img);
//                            let sw = document.createElement("div");
//                            sw.innerHTML = "<div class="form-check form-switch">\n" +
//                                "  <input class="form-check-input" type="checkbox" role="switch" id="flexSwitchCheckDefault" />\n" +
//                                "  <label class="form-check-label" for="flexSwitchCheckDefault">Move</label>\n" +
//                                "</div>";
//                            if (marker.dragging.enabled())
//                                sw.getElementsByTagName("input")[0].checked = true;
//                            sw.onclick = function () {
//                                if (marker.dragging.enabled())
//                                    marker.dragging.disable();
//                                else
//                                    marker.dragging.enable();
//                            }
//                            let actionsSpan = document.getElementById("actions");
//                            actionsSpan.appendChild(sw);
//                        } else
//                            alert("Error: " + JSON.stringify(data));
//                    })
//                });
//                marker.on("dragend", function (e) {
//                    let position = marker.getLatLng();
//                    marker.setLatLng(position);
//                    popup.setLatLng(position);
//                    let postData = {"id": photo.id, "hash": photo.ihash, "lat": position.lat, "lng": position.lng};
//                    let headers = {"Content-Type": "application/json"};
//                    let url = new URL("/geotag", window.location.origin);
//                    url.search = new URLSearchParams({"op": "update_location"}).toString();
//                    fetch(url, {method: "POST", headers: headers, body: JSON.stringify(postData)})
//                        .then(response => response.json())
//                        .then(data => {
//                            if (data.status !== "ok")
//                                alert("Cannot update position: " + JSON.stringify(data));
//                        });
//                });
//            });
//            markers.push(marker);
//            markerCluster.addLayer(marker);
//        };
        map.on("styleimagemissing", async(e) => {
//            const response = await fetch(e.id);
//            const imgData = await response.blob();
            if (loadedImages.has(e.id))
                return;
            loadedImages.add(e.id);
            const image = await map.loadImage(e.id);
            map.addImage(e.id, image.data);
        });
        map.fitBounds(bounds);
//        map.addLayer(markerCluster);
//        layerControl.addOverlay(markerCluster, "Photos");
        // enableClustering();
    });

}

function initMap() {

//    ""
//    attribution: "ESRI Streets"
//    ", {
//    attribution: "ESRI Satellite"

    map = new maplibregl.Map({
        container: "map",
        center: [25, 45.5],
        zoom: 2,
        minZoom: 2,
        style: {
            "version": 8,
            "projection": {
                "type": "globe"
            },
            "glyphs": "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
            "sources": {
                "satellite": {
                    "tiles": ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"],
                    "type": "raster"
                },
//                "streets": {
//                    "tiles": ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}"],
//                    "type": "raster"
//                },
            },
            "layers": [
//                {
//                    "id": "ESRI Streets",
//                    "type": "raster",
//                    "source": "streets",
//                },
                {
                    "id": "ESRI Satellite",
                    "type": "raster",
                    "source": "satellite",
                },
            ],
            "sky": {
                "atmosphere-blend": [
                    "interpolate",
                    ["linear"],
                    ["zoom"],
                    0, 1,
                    5, 1,
                    7, 0
                ]
            },
            "light": {
                "anchor": "map",
                "position": [1.5, 90, 80]
            }
        }
    });
    map.on("style.load", () => {
        map.setProjection({
            type: "globe", // Set projection to globe
        });
    });
    map.addControl(new maplibregl.GlobeControl(), "top-right");
    map.addControl(new maplibregl.NavigationControl());
    function onMapClick(e) {
        popup.setLatLng(e.latlng).setContent(`click:${e.latlng.lat.toFixed(6)},${e.latlng.lng.toFixed(6)}`).openOn(map);
    }
    map.on("click", onMapClick);
    loadPhotos();
}

document.onkeydown = function (e) {
    if (e.code === "27") {
        closeOverlayContainer();
    }
    if (e.code === "90")
        map.fitBounds(bounds);
    if (e.code === "79")
        toggleOptionsPane();
};

window.addEventListener("load", (event) => {
    initMap();
});
