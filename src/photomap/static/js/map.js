let map;
let bounds;
let infoWindow;
let markers = [];
let optionPaneState = 0;
let mcOptions = {gridSize: 50, maxZoom: 18, imagePath: "/static/images/m"};
let markerCluster = null;
let photosById = {};

function enableClustering() {
	if (markerCluster == null)
		markerCluster = new MarkerClusterer(map, markers, mcOptions);
}

function disableClustering() {
	markerCluster.clearMarkers();
	markerCluster = null;
	for ( let i = 0; i < markers.length; i++) {
		markers[i].setMap(map);
	}
}

function initMap() {

	// const esri_WorldStreetMap = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
	// 	attribution: 'ESRI Streets'
	// });

	const esri_WorldImagery = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
		attribution: 'ESRI Satellite'
	});

	const map = L.map("mapCanvas", {
		layers: [esri_WorldImagery]
	}).setView([45.5, 25], 7);

	let baseMaps = {
		// "ESRI World": esri_WorldStreetMap,
		"ESRI Satellite": esri_WorldImagery
	};
	const popup = L.popup();
	function onMapClick(e) {
		popup.setLatLng(e.latlng).setContent(`You clicked the map at ${e.latlng.toString()}`).openOn(map);
	}

	map.on('click', onMapClick);
	markerCluster = L.markerClusterGroup({disableClusteringAtZoom: 17});
	bounds = L.latLngBounds();
	for ( let i=0; i<window.photos.length; i++){
		let photo = photos[i];
		photosById[photo["id"]] = photo;
		let point = L.latLng(photo['lat'], photo['lng']);
		let iconUrl= '/media/thumbnails/64px/' + photo.ihash[0] + '/' + photo.ihash[1] + '/' + photo.ihash;
		bounds.extend(point);
		let marker = L.marker(point, {
			title: photo['filename'],
			icon: L.icon({iconUrl: iconUrl}),
			image_id: photo['id']
		});
		let content = generateInfoWindowContent(photo);
		marker.bindPopup(content, {maxWidth : 540});
		markers.push(marker);
		markerCluster.addLayer(marker);
	}

	map.fitBounds(bounds);
	// enableClustering();
	map.addLayer(markerCluster);
	let overlayMaps = {
		"Photos": markerCluster
	};
	let layerControl = L.control.layers(baseMaps, overlayMaps).addTo(map);
}

document.onkeydown = function(e) {
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
