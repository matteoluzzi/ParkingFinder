//carica la lista dei quadranti in modo asincrono, eseguendo la callback a caricamento completato
function loadQuadrantsList(callback)
{
		$.ajax({
			type : "GET",
			url : "http://ec2-54-68-136-156.us-west-2.compute.amazonaws.com:8888/backend_server/parkings/listaquadranti.txt",
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
		//	strokeColor: "#FF0000",
		//	strokeOpacity: 0.5,
		//	strokeWeight: 1,
		//	fillColor: "#FF0000",
		//	fillOpacity: 0.20,
			map: window.map
		});
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
