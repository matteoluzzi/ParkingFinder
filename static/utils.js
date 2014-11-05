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


	for (var index = 0; index < lines.length -1; index++)
	{
		var quadrant = {};
		var line_arr = lines[index].split("#");
		quadrant.id = parseInt(line_arr.splice(0, 1)[0]);
		for(var i = 0; i < line_arr.length; i++)
		{
			var point_arr = line_arr[i].split("|");
			switch (i) {
				case 0:
					quadrant.NW = {lat : parseFloat(point_arr[0]), lon : parseFloat(point_arr[1])};
					break;
				case 1:
					quadrant.NE = {lat : parseFloat(point_arr[0]), lon : parseFloat(point_arr[1])};
					break;
				case 2:
					quadrant.SW = {lat : parseFloat(point_arr[0]), lon : parseFloat(point_arr[1])};
					break;
				case 3:
					quadrant.SE = {lat : parseFloat(point_arr[0]), lon : parseFloat(point_arr[1])};
					break;
			}
		}
		quadrants.push(quadrant);
	}

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

		if(isInside(currentWindow, quadrants[i].NW) || isInside(currentWindow, quadrants[i].NE) || isInside(currentWindow, quadrants[i].SE) || isInside(currentWindow, quadrants[i].SW)) 
				result_list.push(quadrants[i].id);
	};
	return result_list;

};

//funzione che dati i bounds di una finestra, ritorna un ogetto di tipo quadrante

function getWindowsFromBounds(bounds) {

	var neLat = bounds.getNorthEast().lat();
	var neLon = bounds.getNorthEast().lng();
	var swLat = bounds.getSouthWest().lat();
	var swLon = bounds.getSouthWest().lng();
	return {SE : {lat : swLat, lon : neLon}, NE : {lat : neLat, lon : neLon}, SW : {lat : swLat, lon : swLon}, NW : {lat : neLat, lon : swLon}};

};