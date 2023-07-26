let map;
let bounds;
let infoWindow;
let markers = [];
let markerCluster = null;

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
		let point = L.latLng(photo.lat, photo.lng);
		let iconUrl= '/media/thumbnails/64px/' + photo.ihash[0] + '/' + photo.ihash[1] + '/' + photo.ihash;
		bounds.extend(point);
		let marker = L.marker(point, {
			title: photo['filename'],
			icon: L.icon({iconUrl: iconUrl}),
			image_id: photo.id
		});
		marker.bindPopup("content", {maxWidth : "auto"}).on("popupopen", function (layer) {
			fetch(`/photo?${new URLSearchParams({"photo_id": photo.id})}`, {method: "GET"})
			.then(response => response.json())
			.then(data => {
				if (data.status === "ok") {
					marker.setPopupContent(generateInfoWindowContent(data.photo));
					let img = document.createElement("img");
					img.classList.add("rounded");
					img.style.cursor = "pointer";
					img.onclick = function () {
						showImage(data.photo);
					};
					if (data.photo.orientation != 1)
						img.style.transform = getRotation(data.photo.orientation);
					img.src = "/media/thumbnails/192px/" + photo.ihash[0] + "/" + photo.ihash[1] + "/" + photo.ihash;
					let popupImg = document.getElementById("popupImg");
					popupImg.appendChild(img);
				}
				else
					alert("Error: " + JSON.stringify(data));
			});
		});
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
