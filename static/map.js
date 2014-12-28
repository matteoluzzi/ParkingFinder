function displayMap(quadrants, ws, my_center)
{
	console.log("displaing map...");
	var element = $("#map")[0];

	window.map = new google.maps.Map(element, {
		center : my_center,
		zoom : 16,
		mapTypeId : "OSM",
		mapTypeControl : false,
		streetViewControl : false
	});

	window.map.mapTypes.set("OSM", new google.maps.ImageMapType({
		getTileUrl : function(coord, zoom) {
			return "http://tile.openstreetmap.org/" + zoom + "/" + coord.x
					+ "/" + coord.y + ".png";
		},
		tileSize : new google.maps.Size(256, 256),
		name : "OpenStreetMap",
		maxZoom : 18
	}));

	var currentQuadrants = [];
		
	google.maps.event.addListener(map, 'idle', function()
	{

			var newBounds = window.map.getBounds();
			var newWindow = getWindowsFromBounds(newBounds);
			var newQuadrants = getCurrentQuadrants(newWindow, quadrants);

			var quadrantsToBeQuered = [];

			var i = newQuadrants.length;

			while(i--) {
				if(!contains(currentQuadrants, newQuadrants[i]) || window.map.getZoom() > 17) 
					quadrantsToBeQuered.push(newQuadrants[i]);
			}

		//	console.log("quadranti correnti: " + currentQuadrants + "\nNuovi quadranti: " + newQuadrants);


			console.log("quadranti da interrogare: " + quadrantsToBeQuered);

			if(quadrantsToBeQuered.length > 0)
			{
				currentQuadrants = newQuadrants;
				sendMapMessage(ws, quadrantsToBeQuered);
			}
			
	});
//	var centerControlDiv = document.createElement('div');
//	var centrerControl = new CenterControl(centerControlDiv, window.map);
	
	//centerControlDiv.index = 1;
	//window.map.controls[google.maps.ControlPosition.TOP_RIGHT].push(centerControlDiv);
};

function centerMap(center)
{
	window.map.setCenter(center);
	window.map.setZoom(16);
	var marker = new google.maps.Marker({
		map : window.map,
		position : center,
		visible : true
	});
}


function sendMapMessage(ws, quadrants) 
{

	var quadrants_str = quadrants.join("|");
    var zoom = map.getZoom();
    var bounds = map.getBounds();
    
	var neLat = bounds.getNorthEast().lat();
	var neLon = bounds.getNorthEast().lng();
	var swLat = bounds.getSouthWest().lat();
	var swLon = bounds.getSouthWest().lng();
	var id = generateUUID();

	var message = JSON.stringify({"id":id, "zoom_level" :zoom, "neLat": neLat, "neLon":neLon, "swLat":swLat, "swLon":swLon, "quadrants":quadrants_str});

	sendMessage(ws, message, true);

};

function sendSubscribedQuadrants(data, feAddress, fePort)
{
	if(data.length > 0)
	{
		json_data = $.param({quadrants : data, _xsrf : getCookie("_xsrf")}, true);
		console.log(json_data);
		$.ajax({
			type : "POST",
			url : "http://" +feAddress + ":" + fePort + "/subsquadrants" ,
			data : json_data,
			dataType: "json",
			success : function(result) {
				console.log("success");
				var div = $('<div class="form-control" style="margin-top: 8px;border:none;background-color: transparent" />');
				div.text("Richiesta inviata con successo, controllare l'email per la conferma");
				$('#pannelloUtente').append(div);

			},
			error : function(jqXHR, textStatus, errorThrown) {
				console.log("error");
				var div = $('<div class="form-control" style="margin-top: 8px;border:none" />');
				div.text("Errore durante il processamento della richiesta, riprovare");
				$('#pannelloUtente').append(div);
			}
		});
	}
}

function getCookie(name) {
var c = document.cookie.match("\\b" + name + "=([^;]*)\\b");
return c ? c[1] : undefined;
}


function colorPolygon(data, quadrants) 
{

	q_id = data['quadrantID'];
	quadrant = quadrants[q_id - 1];
	percentage = data['percentage'];
	if(percentage > 66)
	{
		setQuadrantColor(quadrant, "#00FF00");
	}
	else if(percentage > 33)
	{
		setQuadrantColor(quadrant, "#FF9900");
	}
	else
	{
		setQuadrantColor(quadrant, "#CC0000");
	}
	
}

function setQuadrantColor(quadrant, color)
{
	var polygon = quadrant.polygon;
	polygon.setOptions({fillColor: color, fillOpacity: 0.20, map: window.map, strokeColor : "#FFFFFF", strokeOpacity : 0, visible : true, editable : false, draggable : false});	
}

function displayParkingSpots(data)
{
	var parkingsArray = data.parkings;
	var i = parkingsArray.length;
//	console.log(parkingsArray);
	while(i--)
	{
		var coordinates = new google.maps.LatLng(parseFloat(parkingsArray[i].lat), parseFloat(parkingsArray[i].lon));
		console.log(coordinates);
		var marker = new google.maps.Marker({
			map : window.map,
			position : coordinates,
			visible : true
	});
	}
}
