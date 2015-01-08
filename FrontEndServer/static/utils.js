function parseQuadrantList(list)
{

	lines = list.split("\n");
	quadrants = new Array();
	window.polygonArray = [];

	for (var index = 0; index < lines.length; index++)
	{
		var quadrant = {};
		if (lines[index].length > 0)
		{
			var line_arr = lines[index].split("#");
			var id = parseInt(line_arr.splice(0, 1)[0]);
			quadrant.id = id;
			var NW, NE, SW, SE;
			var coordinates = new google.maps.LatLngBounds();
			for(var i = 0; i < line_arr.length; i++)
			{
				var point_arr = line_arr[i].split("|");
				switch (i) {
					case 0:
						NW = new google.maps.LatLng(parseFloat(point_arr[0]), parseFloat(point_arr[1]));
						coordinates.extend(NW);
						break;
					case 1:
						NE = new google.maps.LatLng(parseFloat(point_arr[0]), parseFloat(point_arr[1]));
						coordinates.extend(NE);
						break;
					case 2:
						SW = new google.maps.LatLng(parseFloat(point_arr[0]), parseFloat(point_arr[1]));
						coordinates.extend(SW);
						break;
					case 3:
						SE = new google.maps.LatLng(parseFloat(point_arr[0]), parseFloat(point_arr[1]));
						coordinates.extend(SE);
						break;
				}
			}
			quadrant.polygon = new google.maps.Rectangle({
			bounds: coordinates,
			});
			quadrant.polygon.ID = id; 
			window.polygonArray.push(quadrant);
			quadrants.push(quadrant);
		}
		
	}
	return quadrants;
};

//funzione che data la finestra corrente sulla mappa, resistuisce quali quadranti sono inclusi in essa
function getCurrentQuadrants(currentWindow, quadrants) {

	var result_list = [];
	for (var i = 0; i < quadrants.length ; i++) {

		var quadrantCoordinates = quadrants[i].polygon.getBounds();
		
		if (quadrantCoordinates.intersects(currentWindow.getBounds()))
		{
			result_list.push(quadrants[i].id);
		}

	}
	return result_list;
};

function getQuadrants(point, quadrants)
{
	var j = quadrants.length;
	while(j--)
	{
		var currentQuadrant = quadrants[j].polygon
		if (currentQuadrant.getBounds().contains(point))
		{
			console.log("punto " + JSON.stringify(point) + " appartiene al quadrante " + quadrants[j].id);
			return;
		}
	}
	console.log("punto " + JSON.stringify(point) + " non ha quadranti!");
	
}

//funzione che dati i bounds di una finestra, ritorna un ogetto di tipo quadrante

function getWindowsFromBounds(bounds) {

	var neLat = bounds.getNorthEast().lat();
	var neLon = bounds.getNorthEast().lng();
	var swLat = bounds.getSouthWest().lat();
	var swLon = bounds.getSouthWest().lng();

	var bounds = new google.maps.LatLngBounds();
	bounds.extend(new google.maps.LatLng(swLat, neLon));
	bounds.extend(new google.maps.LatLng(neLat, neLon));
	bounds.extend(new google.maps.LatLng(swLat, swLon));
	bounds.extend(new google.maps.LatLng(neLat, swLon));

	return new google.maps.Rectangle({
		bounds : bounds
	});
};


function contains(a, obj) {
    var i = a.length;
    while (i--) {
       if (a[i] === obj) {
           return true;
       }
    }
    return false;
};

function generateUUID() {
	var d = new Date().getTime();
	var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g,
			function(c) {
				var r = (d + Math.random() * 16) % 16 | 0;
				d = Math.floor(d / 16);
				return (c == 'x' ? r : (r & 0x7 | 0x8)).toString(16);
			});
	return uuid;
};
