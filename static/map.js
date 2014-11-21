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
				if(!contains(currentQuadrants, newQuadrants[i])) 
					quadrantsToBeQuered.push(newQuadrants[i]);
			}

			console.log("quadranti correnti: " + currentQuadrants + "\nNuovi quadranti: " + newQuadrants);


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



function CenterControl(div, map) 
{

	var controlUI = document.createElement('div');
	controlUI.style.backgroundColor = 'white';
	controlUI.style.borderStyle = 'solid';
	controlUI.style.borderWidth = '2px';
	controlUI.style.cursor = 'pointer';
	controlUI.style.textAlign = 'center';
	controlUI.title = 'Click to set the map to Home';
	div.appendChild(controlUI);

	
	var controlText = document.createElement('div');
	controlText.style.fontFamily = 'Arial,sans-serif';
	controlText.style.fontSize = '12px';
	controlText.style.paddingLeft = '4px';
	controlText.style.paddingRight = '4px';
	controlText.innerHTML = '<b>My position</b>';
	controlUI.appendChild(controlText);

	google.maps.event.addDomListener(controlUI, 'click', get_my_position());
};

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
	polygon.setOptions({fillColor: color, fillOpacity: 0.20, map: window.map, strokeColor : "#FFFFFF", strokeOpacity : 0});
	polygon.setEditable(true);
	polygon.setVisible(true);
	
}
