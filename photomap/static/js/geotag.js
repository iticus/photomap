var map = null;
var markers = [];
var optionPaneState = 0;
var infoWindow = new google.maps.InfoWindow();
var mcOptions = {gridSize: 50, maxZoom: 18};
var imagesById = {};

function filterImages(){
	let data = {
		'op': "get_image_list",
		'album_filter': $('#album_filter').val(),
		'start_filter': $('#start_filter').val(),
		'stop_filter': $('#stop_filter').val()
	}
	
	$.ajax({
		  url: '/geotag',
		  type: 'GET',
		  data: data,
		  success: function(images) {
			    $('#imageList').html('');
			    imagesById = {};
				for ( let i = 0; i < images.length; i++) {
					var image = images[i];
					image['id'] = image[0];
	 				image['hash'] = image[1];
	 				image['moment'] = new Date(image[2] * 1000);
	 				image['filename'] = image[3];
	 				image['size'] = image[4];
	 				image['camera'] = image[5] + ' ' + image[6];
	 				image['orientation'] = image[7];
	 				image['path'] = image[8];
 				    image['width'] = image[9];
		            image['height'] = image[10];
	                image['description'] = image[11];
					imagesById[image[0]] = image;
					var imgSrc = "/media/thumbnails/64px/" + image[8] + "/" + image[1];
					var img =  $('<img class="image-list-item" draggable="true" onclick="showImage(' +  image[0] + ')" src=' + imgSrc +
							' id="' + image[0] + '" data-hash="' + image[1] + '">');
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
	overlay = new google.maps.OverlayView();
	overlay.draw = function() {};
	overlay.setMap(map); 
	
	$('#start_filter').val('2013-06-01');
	$('#stop_filter').val('2013-09-01');
	
	filterImages();
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
