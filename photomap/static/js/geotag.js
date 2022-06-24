let map = null;
let optionPaneState = 0;
let photosById = {};

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
			content += '<img class="photo-list-item" draggable="true" onclick="showImage(' +  photo.id + ')" src=' + imgSrc +
					' id="' + photo.id + '" data-hash="' + photo.ihash + '">';
		}
		imageList.innerHTML = content;
		// document.getElementsByClassName(".image-list-item").draggable({helper: 'clone',
		// 	appendTo: 'body',
		// 	stop: function(e, ui) {
		// 		let point=new google.maps.Point(e.pageX, e.pageY);
		// 		let latLng=overlay.getProjection().fromContainerPixelToLatLng(point);
		// 		let marker = new google.maps.Marker({
		// 			position: latLng,
		// 			map: map,
		// 			icon: this.src
		// 		});
		// 		//alert($(this).attr('data-hash'));
		// 		let lat = marker.getPosition().lat();
		// 		let lng = marker.getPosition().lng();
		// 		let post_data = {'id': $(this).attr('id'), 'hash': $(this).attr('data-hash'), 'lat': lat, 'lng': lng};
		// 		$.ajax({
		// 			  url: '/geotag/update_location',
		// 			  type: 'POST',
		// 			  data: post_data,
		// 			  success: function(data) {
		// 				  console.log("Geotag success: " + data);
		// 				  },
		// 			  fail: function() {
		// 				  alert("Error: " + data);
		// 				  }
		// 			  });
		//
		// 		$(this).remove();
		// 	}
		// });
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
	let overlay = new google.maps.OverlayView();
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
