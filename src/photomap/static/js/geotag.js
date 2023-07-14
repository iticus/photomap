let map = null;
let overlay;
let optionPaneState = 0;
let photosById = {};

function allowDrop(ev) {
	ev.preventDefault();
}

function drag(ev) {
	ev.dataTransfer.setData("id", ev.target.id);
	ev.dataTransfer.setData("hash", ev.target.dataset.hash);
}

function drop(ev) {
	ev.preventDefault();
	let photoId = ev.dataTransfer.getData("id");
	let hashId =  ev.dataTransfer.getData("hash");
	let point = new google.maps.Point(ev.pageX, ev.pageY);
	let latLng = overlay.getProjection().fromContainerPixelToLatLng(point);
	let marker = new google.maps.Marker({
		position: latLng,
		map: map,
		icon: document.getElementById(photoId).src
	});
	//alert($(this).attr('data-hash'));
	let lat = marker.getPosition().lat();
	let lng = marker.getPosition().lng();
	let url = new URL("/geotag", window.location.origin);
	url.search = new URLSearchParams({"op": "update_location"}).toString();
	let postData = {'id': photoId, 'hash': hashId, 'lat': lat, 'lng': lng};
	let headers = {"Content-Type": "application/json"};
	fetch(url, {method: 'POST', headers: headers, body: JSON.stringify(postData)})
	.then(response => response.json())
	.then(data => {
		if (data.status === "ok")
		    console.log("Geotag success: " + data);
		else
		    alert("Error: " + JSON.stringify(data));
	});
}

function filterPhotos(){
	let url = new URL("/geotag", window.location.origin);
	let data = {
		"op": "get_photo_list",
		"album_filter": document.getElementById("album_filter").innerText,
		"start_filter": document.getElementById("start_filter").innerText,
		"stop_filter": document.getElementById("stop_filter").innerText
	}
	url.search = new URLSearchParams(data).toString();
	fetch(url, {method: "GET"})
	.then(response => response.json())
	.then(photos => {
		let imageList = document.getElementById("imageList");
		imageList.innerHTML = "";
		photosById = {};
		let content = "";
		for ( let i = 0; i < photos.length; i++) {
			let photo = photos[i];
			photosById[photo.id] = photo;
			let imgSrc = "/media/thumbnails/64px/" + photo.ihash[0] + "/" + photo.ihash[1] + "/" + photo.ihash;
			content += '<img class="photo-list-item" draggable="true" ondragstart="drag(event)" onclick="showImage(' +  photo.id + ')" src=' + imgSrc +
					' id="' + photo.id + '" data-hash="' + photo.ihash + '">';
		}
		imageList.innerHTML = content;
	});
}

function initMap() {

	for ( let i=0; i<window.photos.length; i++){
		photosById[photos[i]['id']] = photos[i];
	}

	let mapOptions = {
		zoom : 7,
		scaleControl: true,
		center : new google.maps.LatLng(45.5, 25),
		mapTypeId : google.maps.MapTypeId.ROADMAP
	};

	map = new google.maps.Map(document.getElementById('mapCanvas'), mapOptions);
	overlay = new google.maps.OverlayView();
	overlay.draw = function() {};
	overlay.setMap(map);

	document.getElementById("start_filter").innerHTML = "2020-01-01";
	document.getElementById("stop_filter").innerHTML = "2021-01-01";

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

window.initMap = initMap;
