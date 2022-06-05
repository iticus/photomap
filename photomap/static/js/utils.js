function generateRotateCss(degrees){
	var properties = ['-ms-transform', /* IE 9 */
	                  '-moz-transform', /* Firefox */
	                  '-webkit-transform', /* Safari and Chrome */
	                  '-o-transform']; /* Opera */
	var style = '';
	for (var i=0; i<properties.length; i++)	{
			style += properties[i] + ': rotate(' + degrees + 'deg);';
		}
	return style
}

function formatDatetime(moment){
    var year = moment.getFullYear();
    var month = ('0' + (moment.getMonth()+1)).substr(-2,2);
    var day = ('0' + moment.getDate()).substr(-2,2);
    var hour = ('0' + moment.getHours()).substr(-2,2);
    var minute = ('0' + moment.getMinutes()).substr(-2,2);
    var second = ('0' + moment.getSeconds()).substr(-2,2);
    return year + '-' + month + '-' + day + ' ' + hour + ':' + minute + ':' + second;
}

function showImage(image_id) {
	var image = imagesById[image_id];
	
	$('#imageOverlay').html('<div id="overlayContainer"></div>');
	var img = $('<img id="dynamicImage" style="max-width: 100%; max-height: 100%" src="/media/thumbnails/960px/'+ 
			image['path'] + '/' + image['hash'] + '">');

	var real_width, real_height, aux;
    $("<img/>") // Make in memory copy of image to avoid css issues
        .attr("src", $(img).attr("src"))
        .load(function() {
            real_width = this.width; 
            real_height = this.height;
            $('#overlayContainer').css({'width': real_width + 'px'});
            if ($(document).height() - 20 < real_height) {
            	aux = 20;
            	$('#overlayContainer').css({'height': ($(document).height() - 40) + 'px'});
            }
        	else {
        		aux = ($(document).height() - real_height) / 2;
        	}
            $('#imageOverlay').css({'display': 'block'});
            
            $('#overlayContainer').css({'margin-top': aux + 'px'});
            
            $('#overlayContainer').css('width', $('#dynamicImage').width());
            $('#overlayContainer').css('height', $('#dynamicImage').height());
            
        });
    
    $('#overlayContainer').html(img);
	
}

function openOptionsPane() {
	$('#optionsPane').css({'display': 'block'});	
}

function closeOptionsPane() {
	$('#optionsPane').css({'display': 'none'});	
}

function toggleOptionsPane() {
	if (optionPaneState == 1)
		closeOptionsPane();
	else 
		openOptionsPane();
	optionPaneState = 1 - optionPaneState;	
}

function generateInfoWindowContent(image) {
	var content = '<div style="width: 480px; height: 200px">';
	content += '<div style="display: inline-block; width: 280px">';
	content += '<table class="info-table">'
	content += '<tr><td><b>Filename</b></td><td>' + image['filename'] + '</td></tr>';
	content += '<tr><td><b>Description</b></td><td>' + image['description'] + '</td></tr>';
	content += '<tr><td><b>Camera</b></td><td>' + image['camera'] + '</td></tr>';
	content += '<tr><td><b>Date</b></td><td>' + formatDatetime(image['moment']) + '</td></tr>';
	content += '</table></div>'
	content += '<div style="display: inline-block; width: 120px">';
	
	content += '<img style="cursor: pointer" onClick="showImage(' + image['id'] + ')"' + 
		'src="/media/thumbnails/192px/'+ image['path'] + '/' + image['hash'] + '">';
	content += '</div></div>';
	return content;
}

function closeOverlayContainer() {
	$('#imageOverlay').css({'display': 'none'});
	infoWindow.close();
}