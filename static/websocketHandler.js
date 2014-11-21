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

function create_connection(my_center) {
	var ws = new WebSocket("ws://ec2-54-148-10-29.us-west-2.compute.amazonaws.com:8000/map");

	var quadrants;

	ws.onmessage = function(event) 
	{ 
		var data_obj = JSON.parse(event.data);

		//console.log(data_obj);

		switch (data_obj['type']) {

			case "quadrant_list":
				quadrants = parseQuadrantList(data_obj['data']);
				displayMap(quadrants, ws, my_center);
				break;

			default:
				on_message(data_obj, quadrants);
				break;
		}
	}
	ws.onerror = function(event) { on_error(event); }
	ws.onclose = function(event) { on_close(event, ws); };

}

function on_message(message, quadrants) {

	var type = message['type'];

	switch (type) {

		case "overview_response":
			console.log(message);
			colorPolygon(message, quadrants);
			break;

		default:
			//console.log(message);
			break;
	};

	
};

function on_close(event, ws) {
	console.log("Websocket chiusa - riconnessione");
	var center = window.map.getCenter();
	ws = create_connection(center);
};

function on_error(even) {
	console.log("Errore sulla websocket");
};

function sendMessage(ws, message, init) {
	if(init)
	{
		waitForInit(ws, function() {
			ws.send(message);
		});
	}
	else
		ws.send(message);
};

function waitForInit(ws, callback) {
	setTimeout(
		function() {
			if(ws.readyState === 1)
				callback();
			else
				waitForInit(ws, callback);
		}, 5);
}
