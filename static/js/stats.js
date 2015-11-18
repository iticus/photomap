var images = [];
var imagesById = {};
var cameras = {};

google.load("visualization", "1.1", {packages:["table"]});

function initializeStats() {
	
	$.ajax({
		  url: '/stats/get_stats',
		  type: 'GET',
		  success: function(data) {
			    imagesById = {};
			    images = $.parseJSON(data);
			    var tableData = new google.visualization.DataTable();
			    tableData.addColumn('string', 'Camera');
			    tableData.addColumn('number', 'Total');
			    tableData.addColumn('number', 'Valid Position');
			    tableData.addColumn('number', 'Percentage');
			    tableData.addColumn('date', 'From');
			    tableData.addColumn('date', 'To');
			    tableData.addColumn('number', 'Size [MB]');
				for ( var i = 0; i < images.length; i++) {
					image = images[i];
					//image.id, extract(epoch from moment) as moment, lat, lng, size, make, model, width, height
					imagesById[image[0]] = image;
					var camera = image[5] + ' ' + image[6];
					if (!(camera in cameras)) {
						cameras[camera] = {'total': 0, 'valid_pos': 0, 'start': 2000000000, 'stop': 0, 'size': 0};
					}
					cameras[camera]['total'] += 1;
					cameras[camera]['size'] += image[4] / 1000000;
					if (image[2] && image[3]) {
						cameras[camera]['valid_pos'] += 1;
					};
					if (image[1] < cameras[camera]['start']) {
						cameras[camera]['start'] = image[1];
					}
					if (image[1] > cameras[camera]['stop']) {
						cameras[camera]['stop'] = image[1];
					}
				}
				
				for (key in cameras) {
					var v = cameras[key];
					var p = v['valid_pos'] / v['total'] * 100;
					p = parseFloat(p.toFixed(2));
					var s = parseFloat(v['size'].toFixed(2));
					var d1 = new Date(v['start'] * 1000);
					var d2 = new Date(v['stop'] * 1000);
					tableData.addRow([key, v['total'], v['valid_pos'], p, d1, d2, s]);
				}
				tableData.sort([{column: 1, desc:true}]);
		        var table = new google.visualization.Table(document.getElementById('tableChart'));
		        table.draw(tableData, {showRowNumber: true, width: '100%', height: '100%'});
		  }
	});
}

$(document).ready(function() {
	initializeStats();
});

