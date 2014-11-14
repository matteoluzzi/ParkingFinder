function create_connection() {
	return new WebSocket("ws://ec2-54-68-136-156.us-west-2.compute.amazonaws.com:8000/map");
}

function on_message(message, quadrants) {

	var data = JSON.parse(message.data);
	var type = data['type'];
	switch (type) {
		case "overview_response":
			console.log(data);
			colorPolygon(data, quadrants);
		default:
			console.log(data);
		//	colorPolygon(data, quadrants);

	};

	
};

function on_close(event, ws) {
	console.log("Websocket chiusa - riconnessione");
	ws = create_connection();
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
