function displayMap(quadrants, ws, my_center)
{
	window.markers = [];
	window.parking_markers = [];
	window.zoom = 0;
	console.log("displaing map...");
	var element = $("#map")[0];
	window.count = -1;

	window.map = new google.maps.Map(element, {
		center : my_center,
		zoom : 15,
		minZoom : 14,
		mapTypeId : "OSM",
		mapTypeControl : false,
		streetViewControl : false
	});

	var my_position_icon = 'imgs/map_pointer.png';

	var marker = new google.maps.Marker({
		map : window.map,
		position : my_center,
		visible : true,
		icon : my_position_icon
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
	
	map.controls[google.maps.ControlPosition.TOP_RIGHT].push(document.getElementById('custom_legend').cloneNode(true));
	
	var currentQuadrants = [];
		
	google.maps.event.addListener(map, 'idle', function()
	{

			var current_zoom = window.map.getZoom();

			if(current_zoom < 18 && window.zoom == 18) //cancella i markers dei parcheggi dalla mappa
			{
				deleteMarkers(window.parking_markers);
			}

			var newBounds = window.map.getBounds();
			var newWindow = getWindowsFromBounds(newBounds);
			var newQuadrants = getCurrentQuadrants(newWindow, quadrants);

			var quadrantsToBeQuered = [];

			var i = newQuadrants.length;

			while(i--) {
				if(!contains(currentQuadrants, newQuadrants[i]) || current_zoom > 17 || (current_zoom < 18 && window.zoom == 18)) 
					quadrantsToBeQuered.push(newQuadrants[i]);
			}

		//	console.log("quadranti correnti: " + currentQuadrants + "\nNuovi quadranti: " + newQuadrants);


			console.log("quadranti da interrogare: " + quadrantsToBeQuered);

			if(quadrantsToBeQuered.length > 0)
			{
				currentQuadrants = newQuadrants;
				sendMapMessage(ws, quadrantsToBeQuered, current_zoom, newBounds);
				window.count = quadrantsToBeQuered.length;
			}
			window.zoom = window.map.getZoom();
			
	});
};

function centerMap(center, start)
{
	deleteMarkers(window.markers);
	window.map.setCenter(center);
	window.map.setZoom(16);
	if(start)
	{	
		var marker = new google.maps.Marker({
			map : window.map,
			position : center,
			visible : true
		});
		window.markers.push(marker);
	}
}

function deleteMarkers(array)
{
	var i = array.length;
	while(i--)
	{
		var marker = array.pop();
		marker.setMap(null);
		marker = null;
	}
}


function sendMapMessage(ws, quadrants, zoom, bounds) 
{
	if(zoom == null)
		zoom = 14;
	if(bounds == null)
		bounds = window.map.getBounds();

	var quadrants_str = quadrants.join("|");  
	var neLat = bounds.getNorthEast().lat();
	var neLon = bounds.getNorthEast().lng();
	var swLat = bounds.getSouthWest().lat();
	var swLon = bounds.getSouthWest().lng();
	var id = generateUUID();

	var message = JSON.stringify({"type":"normal", "id":id, "zoom_level" :zoom, "neLat": neLat, "neLon":neLon, "swLat":swLat, "swLon":swLon, "quadrants":quadrants_str});

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
			url : "http://" +feAddress + "/subsquadrants" ,
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
	if(percentage == -1)
	{
		setQuadrantColor(quadrant, "#C0C0C0");
	}
	else if(percentage > 66)
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
	window.count = window.count -1;
}

function displayParkingSpots(data)
{
	var parkingsArray = data.parkings;
	var i = parkingsArray.length;
	var my_parking_icon = 'imgs/parking_icon.png';
//	console.log(parkingsArray);
	while(i--)
	{
		if(parkingsArray[i].state == parseInt("0"))
		{
			var coordinates = new google.maps.LatLng(parseFloat(parkingsArray[i].lat), parseFloat(parkingsArray[i].lon));
			console.log(coordinates);
			var marker = new google.maps.Marker({
				map : window.map,
				position : coordinates,
				visible : true,
				icon : my_parking_icon,
			});
			parking_markers.push(marker);
		}		
	}
}
