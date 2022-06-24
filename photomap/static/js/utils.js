function generateRotateCss(degrees){
	let properties = ['-ms-transform', /* IE 9 */
	                  '-moz-transform', /* Firefox */
	                  '-webkit-transform', /* Safari and Chrome */
	                  '-o-transform']; /* Opera */
	let style = '';
	for (let i=0; i<properties.length; i++)	{
			style += properties[i] + ': rotate(' + degrees + 'deg);';
		}
	return style
}

function formatDatetime(moment){
    let year = moment.getFullYear();
    let month = ('0' + (moment.getMonth()+1)).substr(-2,2);
    let day = ('0' + moment.getDate()).substr(-2,2);
    let hour = ('0' + moment.getHours()).substr(-2,2);
    let minute = ('0' + moment.getMinutes()).substr(-2,2);
    let second = ('0' + moment.getSeconds()).substr(-2,2);
    return year + '-' + month + '-' + day + ' ' + hour + ':' + minute + ':' + second;
}

function showImage(image_id) {
	let photo = photosById[image_id];
	let img = '<img id="dynamicImage" style="max-width: 100%; max-height: 100%" src="/media/thumbnails/960px/'+
			photo.ihash[0] + '/' + photo.ihash[1] + '/' + photo.ihash + '">';
	document.getElementById("imageOverlay").innerHTML = img;
	document.getElementById("imageOverlay").style.display = "block";
}

function openOptionsPane() {
	document.getElementById("optionsPane").style.display = "block";
}

function closeOptionsPane() {
	document.getElementById("optionsPane").style.display = "none";
}

function toggleOptionsPane() {
	if (optionPaneState == 1)
		closeOptionsPane();
	else 
		openOptionsPane();
	optionPaneState = 1 - optionPaneState;	
}

function generateInfoWindowContent(photo) {
	let content = '<div style="width: 480px; height: 200px">';
	content += '<div style="display: inline-block; width: 280px">';
	content += '<table class="info-table">'
	content += '<tr><td><b>Filename</b></td><td>' + photo['filename'] + '</td></tr>';
	content += '<tr><td><b>Description</b></td><td>' + photo['description'] + '</td></tr>';
	content += '<tr><td><b>Camera</b></td><td>' + photo['camera'] + '</td></tr>';
	content += '<tr><td><b>Date</b></td><td>' + formatDatetime(photo['moment']) + '</td></tr>';
	content += '</table></div>'
	content += '<div style="display: inline-block; width: 120px">';
	content += '<img style="cursor: pointer" onClick="showImage(' + photo['id'] + ')"' +
		'src="/media/thumbnails/192px/'+ photo.ihash[0] + '/' + photo.ihash[1] + '/' + photo.ihash + '">';
	content += '</div></div>';
	return content;
}

function closeOverlayContainer() {
	document.getElementById("imageOverlay").style.display = "none";
	if (typeof infoWindow !== "undefined") {
		infoWindow.close();
	}
}
