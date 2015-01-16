function get_my_position(callback) {

			navigator.geolocation.getCurrentPosition(function (position){				
					callback(new google.maps.LatLng(position.coords.latitude,
	                position.coords.longitude));
				},
				function () {		
					var randomLat = Math.random() * (42.06 - 41.75) + 41.75;
					var randomLon = Math.random() * (12.74 - 12.25) + 12.25;

					//callback(new google.maps.LatLng(41.88976989299657, 12.514091491699224));
					callback(new google.maps.LatLng(randomLat, randomLon));
				});			
};

function create_connection(my_center, feAddr, fePort) {
	var ws = new WebSocket("ws://" + feAddr + ":" + fePort + "/map");

	var quadrants;

	ws.onopen = function(event)
	{
		console.log('websocket opened');
		setInterval(function()
		{
			var ping_message = JSON.stringify({"type" : "Heartbeat"});
			console.log("sending ping");
			sendMessage(ws, ping_message, false);
		}, 40000);
	} 

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
	ws.onclose = function(event) { on_close(event, ws, feAddr, fePort); };

}

function on_message(message, quadrants) {

	var type = message['type'];

	switch (type) {

		case "overview_response":
			console.log(message);
			colorPolygon(message, quadrants);
			break;

		default:
			console.log(message);
			displayParkingSpots(message);
			break;
	};

	
};

function on_close(event, ws, feAddr, fePort) {
/*	if($('#enable_selection').is(':checked'))
=======
	if($('#enable_selection').is(':checked'))
>>>>>>> 59705ed5a6438f7b799f5ccf08098dfd03096800
	{
		$('#enable_selection').click();
	}
	console.log("Websocket chiusa - riconnessione");
	var center = window.map.getCenter();
	ws = create_connection(center, feAddr, fePort);
	*/
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
