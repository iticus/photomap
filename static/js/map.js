var map = null;
var markers = [];
var optionPaneState = 0;
var bounds = new google.maps.LatLngBounds();
var infoWindow = new google.maps.InfoWindow();
var mcOptions = {gridSize: 50, maxZoom: 18};
var markerCluster = null;
var imagesById = {};

function enableClustering() {
	if (markerCluster == null)
		markerCluster = new MarkerClusterer(map, markers, mcOptions);
}

function disableClustering() {
	markerCluster.clearMarkers();
	markerCluster = null;
	for ( var i = 0; i < markers.length; i++) {
		markers[i].setMap(map);
	}
}

function initializeMap() {
	
	for ( var i=0; i<images.length; i++){
		imagesById[images[i]['id']] = images[i];
	}
	
	var mapOptions = {
		zoom : 7,
		scaleControl: true,
		center : new google.maps.LatLng(45.5, 25),
		mapTypeId : google.maps.MapTypeId.ROADMAP
	};

	map = new google.maps.Map(document.getElementById('mapCanvas'), mapOptions);
	
	for ( var i = 0; i < images.length; i++) {
		var image = images[i];
		var point = new google.maps.LatLng(image['lat'], image['lng']);

		bounds.extend(point);
		
		var marker = new google.maps.Marker({
			position : point,
			title : image['filename'],
			icon : new google.maps.MarkerImage('/media/thumbnails/64px/'+ 
					image['path'] + '/' + image['hash']),
			image_id: image['id']
		});
		
		
		
		marker.content = generateInfoWindowContent(image);
		
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

$(document).keyup(function(e){

    if(e.keyCode === 27) {
    	closeOverlayContainer();
    }

    if(e.keyCode === 90)
    	map.fitBounds(bounds);
   
    if(e.keyCode === 79)
    	toggleOptionsPane();
});

google.maps.event.addDomListener(window, 'load', initializeMap);

