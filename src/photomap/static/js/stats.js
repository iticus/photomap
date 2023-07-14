let images = [];
let imagesById = {};
let cameras = {};

google.load("visualization", "1.1", {packages:["table"]});

function initializeStats() {
	let url = new URL("/stats", window.location.origin);
	url.search = new URLSearchParams({"op": "get_stats"}).toString();
	fetch(url, {method: 'GET'})
		.then(response => response.json())
		.then(images => {
			imagesById = {};
			let tableData = new google.visualization.DataTable();
			tableData.addColumn('string', 'Camera');
			tableData.addColumn('number', 'Total');
			tableData.addColumn('number', 'Valid Position');
			tableData.addColumn('number', 'Percentage');
			tableData.addColumn('date', 'From');
			tableData.addColumn('date', 'To');
			tableData.addColumn('number', 'Size [MB]');
			for ( let i = 0; i < images.length; i++) {
				let image = images[i];
				imagesById[image.id] = image;
				let camera = image.make + ' ' + image.model;
				if (!(camera in cameras)) {
					cameras[camera] = {'total': 0, 'valid_pos': 0, 'start': 2000000000, 'stop': 0, 'size': 0};
				}
				cameras[camera]['total'] += 1;
				cameras[camera]['size'] += image.size / 1000000;
				if (image.lat && image.lng) {
					cameras[camera]['valid_pos'] += 1;
				};
				if (image.moment < cameras[camera]['start']) {
					cameras[camera]['start'] = image.moment;
				}
				if (image.moment > cameras[camera]['stop']) {
					cameras[camera]['stop'] = image.moment;
				}
			}

			for (const key in cameras) {
				let v = cameras[key];
				let p = v['valid_pos'] / v['total'] * 100;
				p = parseFloat(p.toFixed(2));
				let s = parseFloat(v['size'].toFixed(2));
				let d1 = new Date(v['start'] * 1000);
				let d2 = new Date(v['stop'] * 1000);
				tableData.addRow([key, v['total'], v['valid_pos'], p, d1, d2, s]);
			}
			tableData.sort([{column: 1, desc:true}]);
			let table = new google.visualization.Table(document.getElementById('tableChart'));
			table.draw(tableData, {showRowNumber: true, width: '100%', height: '100%'});
		});
}

window.addEventListener("load", function () {
    initializeStats();
})
