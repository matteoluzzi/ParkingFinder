var map;
function initialize() {
	var element = $("#map")[0];

	window.map = new google.maps.Map(element, {
		center : new google.maps.LatLng(41.88976989299657, 12.514091491699224),
		zoom : 12,
		mapTypeId : "OSM",
		mapTypeControl : false,
		streetViewControl : false
	});

	// Define OSM map type pointing at the OpenStreetMap tile server
	window.map.mapTypes.set("OSM", new google.maps.ImageMapType({
		getTileUrl : function(coord, zoom) {
			return "http://tile.openstreetmap.org/" + zoom + "/" + coord.x
					+ "/" + coord.y + ".png";
		},
		tileSize : new google.maps.Size(256, 256),
		name : "OpenStreetMap",
		maxZoom : 18
	}));

	google.maps.event.addListener(map, 'zoom_changed', function() {
		// alert(window.map.getZoom() + "\n" + window.map.getBounds());
		sendZoomLevel(map.getZoom(), map.getBounds());

	});

	google.maps.event.addListener(map, 'bounds_changed', function() {
		// evento che cattura i cambiamenti di confine della mappa visualizzati,
		// può essere oneroso
	});

	var centerControlDiv = document.createElement('div');
	var centrerControl = new CenterControl(centerControlDiv, window.map);
	
	//centerControlDiv.index = 1;
	window.map.controls[google.maps.ControlPosition.TOP_RIGHT].push(centerControlDiv);


}

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

	google.maps.event.addDomListener(controlUI, 'click', function() {

		if (navigator.geolocation) {
			navigator.geolocation.getCurrentPosition(displayPosition);
		} else {
			var defaultPosition = new google.maps.LatLng(41.88976989299657,
					12.514091491699224);
			window.map.setCenter(defaultPosition);
		}

		function displayPosition(position) {
			console.log(position.coords.latitude, position.coords.longitude);
			var currentPosition = new google.maps.LatLng(position.coords.latitude, position.coords.longitude);
			window.map.setCenter(currentPosition);
			window.map.setZoom(15);
		}
	});
}

function checkMapInfo() {
	zoom = window.map.getZoom();
	center = window.map.getCenter().toString();
	alert("zoom:" + zoom + "center: " + center);
}

function sendZoomLevel(zoom, bounds) {

	// var xmlhttp;
	// if (window.XMLHttpRequest)
	// {// code for IE7+, Firefox, Chrome, Opera, Safari
	// xmlhttp = new XMLHttpRequest();
	// }
	// else
	// {// code for IE6, IE5
	// xmlhttp = new ActiveXObject("Microsoft.XMLHTTP");
	// }

	// xmlhttp.open("POST","http://localhost:8080/map",true);
	// xmlhttp.setRequestHeader("Content-type","application/x-www-form-urlencoded");

	var neLat = bounds.getNorthEast().lat();
	var neLon = bounds.getNorthEast().lng();
	var swLat = bounds.getSouthWest().lat();
	var swLon = bounds.getSouthWest().lng();
	var id = generateUUID();

	var data = "id=" + id + "&zoom_level=" + zoom + "&neLat=" + neLat
			+ "&neLon=" + neLon + "&swLat=" + swLat + "&swLon=" + swLon;

	$.ajax({
		type : "POST",
		url : "http://localhost:8080/map",
		data : data,
		contentType : "application/x-www-form-urlencoded",
		success : function(result) {
			var response = JSON.parse(result);
			console.log(response, typeof response);
			parseAndDrow(response);
		},
		error : function(jqXHR, textStatus, errorThrown) {
			jsonValue = $.parseJSON(jqXHR.responseText);
			console.log(jsonValue.Message);
		}

	});

	// xmlhttp.send("id=" + id + "&zoom_level=" + zoom + "&neLat=" + neLat +
	// "&neLon=" + neLon + "&swLat=" + swLat + "&swLon=" + swLon);

	// xmlhttp.onreadystatechange = function () {
	// if (this.readyState == 4 && this.status == 200) {
	// var JSONresponse = this.responseText;
	// var response = JSON.parse(JSONresponse);
	// console.log(response, typeof response);
	// parseAndDrow(response);
	// }
	// }
}

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
		for (var i = 0; i < msg.length; i++) {
			var zoom = msg[i].zoom;
			var int_zoom = parseInt(zoom, 10);
			console.log(zoom + " " + window.map.getZoom());

			if (int_zoom >= 15 && zoom == window.map.getZoom()) {
				var image = 'http://icons.iconarchive.com/icons/e-young/gur-project/32/map-pointer-icon.png';
				console.log(image);
				var latLng = window.map.getCenter()
				var marker = new google.maps.Marker({
					position : latLng,
					map : window.map,
					icon : image
				});
			}
		}

	}

}
