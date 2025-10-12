function formatDatetime(moment){
    let year = moment.getFullYear();
    let month = ('0' + (moment.getMonth()+1)).slice(-2);
    let day = ('0' + moment.getDate()).slice(-2);
    let hour = ('0' + moment.getHours()).slice(-2);
    let minute = ('0' + moment.getMinutes()).slice(-2);
    let second = ('0' + moment.getSeconds()).slice(-2);
    return year + '-' + month + '-' + day + ' ' + hour + ':' + minute + ':' + second;
}

function showImage(photo) {
	let title = `${photo.filename}, taken on ${formatDatetime(new Date(photo.moment * 1000))} with ${photo.make} ${photo.model}`;
	document.getElementById("photoModalTitle").innerHTML = title;
	let img = '<img id="dynamicImage" style="max-width: 100%; height: auto" src="/media/thumbnails/960px/'+
			photo.ihash[0] + '/' + photo.ihash[1] + '/' + photo.ihash + '">';
	document.getElementById("photoModalBody").innerHTML = img;
	// if (photo.orientation != 1)
	// 	document.getElementById("dynamicImage").style.transform = getRotation(photo.orientation);
	const myModal = new bootstrap.Modal(document.getElementById("photoModal"), {});
	myModal.show();
}

function generateInfoWindowContent(photo) {
	let content = '<div class="col-md-6">';
	content += '<table class="table table-sm table-striped table-hover" style="white-space:nowrap;">'
	content += '<tr><td><b>Filename</b></td><td>' + photo.filename + '</td></tr>';
	content += '<tr><td><b>Size</b></td><td>' + photo.size + ' bytes</td></tr>';
	content += '<tr><td><b>Description</b></td><td>' + photo.description + '</td></tr>';
	content += '<tr><td><b>Camera</b></td><td>' + photo.make + " " + photo.model + '</td></tr>';
	content += '<tr><td><b>W x H</b></td><td>' + photo.width + ' x ' + photo.height + 'px</td></tr>';
	let dt = new Date(photo.moment * 1000);
	content += '<tr><td><b><Date></Date></b></td><td>' + formatDatetime(dt) + '</td></tr>';
	content += '<tr><td><b>Actions</b></td><td><span id="actions"></span></td></tr>';
	content += '</table></div>'
	content += '<div class="col-md-6 d-flex justify-content-center" id="popupImg" ></div></div>';
    const el = document.createElement("div");
    el.classList.add("row");
    el.innerHTML = content;
    el.style.width = "480px";
	return el;
}

function closeOverlayContainer() {
	document.getElementById("imageOverlay").style.display = "none";
	if (typeof infoWindow !== "undefined") {
		infoWindow.close();
	}
}
