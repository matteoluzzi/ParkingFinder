function get_my_position(callback) {

			navigator.geolocation.getCurrentPosition(function (position){
				
					callback(new google.maps.LatLng(position.coords.latitude,
	                position.coords.longitude));
				},
				function () {
				
					callback(new google.maps.LatLng(41.88976989299657,
					12.514091491699224));
				});			
};

function initialize(my_center) {
	var element = $("#map")[0];
	
	init = true;

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

	loadQuadrantsList(function(quadranList) {

		var quadrants = parseQuadrantList(quadranList);

		var currentQuadrants = new Array();

		google.maps.event.addListenerOnce(map, 'bounds_changed', function() {
			
			var currentBounds = window.map.getBounds();
			var currentWindow = getWindowsFromBounds(currentBounds);

			currentQuadrants.push.apply(currentQuadrants, getCurrentQuadrants(currentWindow, quadrants));

			console.log(currentQuadrants);
			sendZoomLevel(currentQuadrants);	
		});

/*
		google.maps.event.addListener(map, 'zoom_changed', function() {
			
			sendZoomLevel();
		});
*/
			
		google.maps.event.addListener(map, 'idle', function(){
			
			if(init) init = false;
			else
			{
				var newBounds = window.map.getBounds();
				var newWindow = getWindowsFromBounds(newBounds);
				var newQuadrants = getCurrentQuadrants(newWindow, quadrants);

				var quadrantsToBeQuered = new Array();

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
					sendZoomLevel(quadrantsToBeQuered);
				}
					


			}		
		});
	});

	
	
	
//	var centerControlDiv = document.createElement('div');
//	var centrerControl = new CenterControl(centerControlDiv, window.map);
	
	//centerControlDiv.index = 1;
	//window.map.controls[google.maps.ControlPosition.TOP_RIGHT].push(centerControlDiv);
};

function CenterControl(div, map) {

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



function checkMapInfo(msg) {
	zoom = window.map.getZoom();
	center = window.map.getCenter().toString();
	bounds = window.map.getBounds().toString();
	alert("msg: " + msg + "\nzoom:" + zoom + "\ncenter: " + center+ "\nbounds: " + bounds);
};

function sendZoomLevel(quadrants) {

	var quadrants_str = quadrants.join("|");
    var zoom = map.getZoom();
    var bounds = map.getBounds();
    
	var neLat = bounds.getNorthEast().lat();
	var neLon = bounds.getNorthEast().lng();
	var swLat = bounds.getSouthWest().lat();
	var swLon = bounds.getSouthWest().lng();
	var id = generateUUID();

	var data = "id=" + id + "&zoom_level=" + zoom + "&neLat=" + neLat
			+ "&neLon=" + neLon + "&swLat=" + swLat + "&swLon=" + swLon + "&quadrants=" + quadrants_str ;

	$.ajax({
		type : "POST",
		url : "http://localhost:8080/map",
		data : data,
		contentType : "application/x-www-form-urlencoded",
		success : function(result) {
			var response = JSON.parse(result);
			parseAndDrow(response);
		},
		error : function(jqXHR, textStatus, errorThrown) {
			jsonValue = $.parseJSON(jqXHR.responseText);
			console.log(jsonValue.Message);
		}

	});

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

function parseAndDrow(msg) {

	if (msg.length > 0) {
//		for (var i = 0; i < msg.length; i++) {
//			var zoom = msg[i].zoom;
//			var int_zoom = parseInt(zoom, 10);
//			console.log(zoom + " " + window.map.getZoom());
//
//			if (int_zoom >= 15 && zoom == window.map.getZoom()) {
//				var image = 'http://icons.iconarchive.com/icons/e-young/gur-project/32/map-pointer-icon.png';
//				console.log(image);
//				var latLng = window.map.getCenter()
//				var marker = new google.maps.Marker({
//					position : latLng,
//					map : window.map,
//					icon : image
//				});
//			}
//		}

		appendText(msg);

	}

};

function appendText(response) {
	var messageContainer = $("#logArea");
	console.log(response);
	var entry = $("<div id='entriesDiv'>");
	var i;
	for (i = 0; i < response.length; i++)
		{
			entry.append(document.createTextNode(JSON.stringify(response[i][0])));		
			messageContainer.append(entry);
		}
		
	
};

function setQuadrantColor(quadrant, color)
{
	var polygon = quadrant.polygon;
	polygon.setEditable(true);
	polygon.setVisible(true);
	

}