let map = null;
let optionPaneState = 0;
let photosById = {};

function allowDrop(ev) {
	ev.preventDefault();
}

function drag(ev) {
	ev.dataTransfer.setData("id", ev.target.id);
	ev.dataTransfer.setData("hash", ev.target.dataset.hash);
}

function handleDrop(ev) {
	let photoId = ev.dataTransfer.getData("id");
	let hashId =  ev.dataTransfer.getData("hash");
	let coordinates = map.containerPointToLatLng(L.point([ev.clientX, ev.clientY]));
	let marker = L.marker(coordinates, {icon: L.icon({iconUrl: document.getElementById(photoId).src}), draggable: true});
	marker.addTo(map);
	let url = new URL("/geotag", window.location.origin);
	url.search = new URLSearchParams({"op": "update_location"}).toString();
	let postData = {"id": photoId, "hash": hashId, "lat": coordinates.lat, "lng": coordinates.lng};
	let headers = {"Content-Type": "application/json"};
	fetch(url, {method: 'POST', headers: headers, body: JSON.stringify(postData)})
	.then(response => response.json())
	.then(data => {
		if (data.status === "ok")
		    document.getElementById(photoId).remove();
		else
		    alert("Error: " + JSON.stringify(data));
	});
}

function filterPhotos(){
	let url = new URL("/geotag", window.location.origin);
	let data = {
		"op": "get_photo_list",
		"album_filter": document.getElementById("album").value,
		"start_filter": document.getElementById("fromDate").value,
		"stop_filter": document.getElementById("toDate").value
	}
	url.search = new URLSearchParams(data).toString();
	fetch(url, {method: "GET"})
	.then(response => response.json())
	.then(photos => {
		let photoList = document.getElementById("photoList");
		photoList.innerHTML = "";
		let content = "";
		for ( let i = 0; i < photos.length; i++) {
			let photo = photos[i];
			let img = document.createElement("img");
			img.classList.add("photo-list-item");
			img.draggable = true;
			img.onclick = function () {
				showImage(photo);
			};
			img.src = "/media/thumbnails/64px/" + photo.ihash[0] + "/" + photo.ihash[1] + "/" + photo.ihash;
			img.id = photo.id;
			img.ondragstart = function (event) {
				drag(event);
			}
			img.dataset.hash = photo.ihash;
			photoList.appendChild(img);
		}
	});
}

function initMap() {

	const esri_WorldImagery = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
		attribution: 'ESRI Satellite'
	});

	map = L.map("map", {
		layers: [esri_WorldImagery]
	}).setView([45.75, 21.25], 12);

	let baseMaps = {
		// "ESRI World": esri_WorldStreetMap,
		"ESRI Satellite": esri_WorldImagery
	};
	const popup = L.popup();
	function onMapClick(e) {
		popup.setLatLng(e.latlng).setContent(`You clicked the map at ${e.latlng.toString()}`).openOn(map);
	}

	document.getElementById("fromDate").value = "2020-01-01";
	document.getElementById("toDate").value = "2021-01-01";

	filterPhotos();
}

document.onkeydown = function(e) {
	if (e.shiftKey == true) {
	    if (e.code === "27") {
	    	closeOverlayContainer();
	    }
	    if (e.code === "79")
	    	toggleOptionsPane();
	}
};

window.addEventListener("load", (event) => {
	let mapdiv = document.getElementById("map")

	mapdiv.ondragover = function (e) {
		e.preventDefault();
		e.dataTransfer.dropEffect = "move";
	}

	mapdiv.ondrop = function (e) {
		e.preventDefault();
		handleDrop(e);
	}

	initMap();
});
