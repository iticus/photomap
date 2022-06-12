var map = null;
var optionPaneState = 0;
var infoWindow = new google.maps.InfoWindow();
var photosById = {};

function filterPhotos(){
	let data = {
		'op': "get_photo_list",
		'album_filter': $('#album_filter').val(),
		'start_filter': $('#start_filter').val(),
		'stop_filter': $('#stop_filter').val()
	}
	
	$.ajax({
		  url: '/geotag',
		  type: 'GET',
		  data: data,
		  success: function(photos) {
			    $('#imageList').html('');
			    photosById = {};
				for ( let i = 0; i < photos.length; i++) {
					let photo = photos[i];
	 				//photo['moment'] = new Date(photo[2] * 1000);
					photosById[photo.id] = photo;
					let imgSrc = "/media/thumbnails/64px/" + photo.ihash[0] + "/" + photo.ihash[1] + "/" + photo.ihash;
					let img =  $('<img class="photo-list-item" draggable="true" onclick="showImage(' +  photo.id + ')" src=' + imgSrc +
							' id="' + photo.id + '" data-hash="' + photo.ihash + '">');
					$('#imageList').append(img);
				}
				$('.image-list-item').draggable({helper: 'clone',
					appendTo: 'body',
					stop: function(e, ui) {
						var point=new google.maps.Point(e.pageX, e.pageY);
						var latLng=overlay.getProjection().fromContainerPixelToLatLng(point);
						var marker = new google.maps.Marker({
							position: latLng, 
							map: map,
							icon: this.src
						});
						//alert($(this).attr('data-hash'));
						lat = marker.getPosition().lat();
						lng = marker.getPosition().lng();
						post_data = {'id': $(this).attr('id'), 'hash': $(this).attr('data-hash'), 'lat': lat, 'lng': lng};
						$.ajax({
							  url: '/geotag/update_location',
							  type: 'POST',
							  data: post_data,
							  success: function(data) {
								  //alert("Success: " + data);
								  },
						      fail: function() { 
						    	  alert("Error: " + data); 
						    	  }
							  });
						
						$(this).remove();
					}
				});
		  }
		});
}

function initializeMap() {
	
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
	
	$('#start_filter').val('2020-01-01');
	$('#stop_filter').val('2021-01-01');
	
	filterPhotos();
}

$(document).keyup(function(e){

	if (e.shiftKey == true) {
	    if(e.keyCode === 27) {
	    	closeOverlayContainer();
	    }
	
	    if(e.keyCode === 79)
	    	toggleOptionsPane();
	}
});

google.maps.event.addDomListener(window, 'load', initializeMap);
