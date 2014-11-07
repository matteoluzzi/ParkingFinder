//carica la lista dei quadranti in modo asincrono, eseguendo la callback a caricamento completato
function loadQuadrantsList(callback)
{
		$.ajax({
			type : "GET",
			url : "http://localhost:8888/backend_server/listaquadranti.txt",
			data : null,
			success : function(response) {
				callback(response);
			},
			error : function(jqXHR, textStatus, errorThrown) {
				console.log("errore nel caricare la lista");
				callback(-1);

			}
		});

};

/*
* funzione che parsa la stringa contenente la lista totale dei quadranti e ritorna un array di oggetti quadrante
*/
function parseQuadrantList(list)
{

	lines = list.split("\n");
	quadrants = new Array();


	for (var index = 0; index < lines.length; index++)
	{
		var quadrant = {};
		var line_arr = lines[index].split("#");
		quadrant.id = parseInt(line_arr.splice(0, 1)[0]);
		var NW, NE, SW, SE;
		coordinates = new Array();
		for(var i = 0; i < line_arr.length; i++)
		{
			var point_arr = line_arr[i].split("|");
			switch (i) {
				case 0:
					NW = new google.maps.LatLng(parseFloat(point_arr[0]), parseFloat(point_arr[1]));
					coordinates.push(NW);
					break;
				case 1:
					NE = new google.maps.LatLng(parseFloat(point_arr[0]), parseFloat(point_arr[1]));
					coordinates.push(NE);
					break;
				case 2:
					SW = new google.maps.LatLng(parseFloat(point_arr[0]), parseFloat(point_arr[1]));
					coordinates.push(SW);
					break;
				case 3:
					SE = new google.maps.LatLng(parseFloat(point_arr[0]), parseFloat(point_arr[1]));
					coordinates.push(SE);
					break;
			}
		}
		/*
		quadrant.polygon = new google.maps.Polygon({
			path: coordinates,
			strokeColor: "#FF0000",
			strokeOpacity: 0.5,
			strokeWeight: 1,
			fillColor: "#FF0000",
			fillOpacity: 0.20,
			map: window.map
		});
*/
		quadrants.push(quadrant);
	}
	console.log(quadrants);
	return quadrants;
};

//funzione che verifica l'appartenenza di un punto ad un quadrante
function isInside(quadrant, point) {

	var lat = point.lat;
	var lon = point.lon;

	return (lat <= quadrant.NW.lat && lat >= quadrant.SW.lat && lon >= quadrant.NW.lon && lon <= quadrant.NE.lon);

};

//funzione che data la finestra corrente sulla mappa, resistuisce quali quadranti sono inclusi in essa
function getCurrentQuadrants(currentWindow, quadrants) {

	var result_list = new Array();
	for (var i = 0; i < quadrants.length ; i++) {

		var quadrantCoordinates = quadrants[i].polygon.getPath().getArray();
		var j = quadrantCoordinates.length;
		while(j--) {
			if (google.maps.geometry.poly.containsLocation(quadrantCoordinates[j], currentWindow))
			{
				result_list.push(quadrants[i].id);
				break;
			}
		}
	}
	return result_list;

};

//funzione che dati i bounds di una finestra, ritorna un ogetto di tipo quadrante

function getWindowsFromBounds(bounds) {

	var neLat = bounds.getNorthEast().lat();
	var neLon = bounds.getNorthEast().lng();
	var swLat = bounds.getSouthWest().lat();
	var swLon = bounds.getSouthWest().lng();
	return new google.maps.Polygon({
		path: [
			new google.maps.LatLng(swLat, neLon),
			new google.maps.LatLng(neLat, neLon),
			new google.maps.LatLng(swLat, swLon),
			new google.maps.LatLng(neLat, swLon)
		]		
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
