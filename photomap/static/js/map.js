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
	bounds = new google.maps.LatLngBounds();
	infoWindow = new google.maps.InfoWindow();
	for ( let i=0; i<window.photos.length; i++){
		photosById[photos[i]["id"]] = photos[i];
	}
	let mapOptions = {
		zoom : 7,
		scaleControl: true,
		center : new google.maps.LatLng(45.5, 25),
		mapTypeId : google.maps.MapTypeId.ROADMAP
	};
	map = new google.maps.Map(document.getElementById('mapCanvas'), mapOptions);
	for ( let i = 0; i < window.photos.length; i++) {
		let photo = photos[i];
		let point = new google.maps.LatLng(photo['lat'], photo['lng']);
		bounds.extend(point);
		let marker = new google.maps.Marker({
			position : point,
			title : photo['filename'],
			icon : new google.maps.MarkerImage('/media/thumbnails/64px/'+ 
					photo.ihash[0] + '/' + photo.ihash[1] + '/'+ photo.ihash),
			image_id: photo['id']
		});
		marker.content = generateInfoWindowContent(photo);
		google.maps.event.addListener(marker, 'click', function () {
            infoWindow.setContent(this.content);
            infoWindow.open(this.getMap(), this);
        });
		//marker.setMap(map);
		markers.push(marker);
	}
	
	map.fitBounds(bounds);
	enableClustering();
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

window.initMap = initMap;
