var response_map = {}
var messages_sent = 0;

function createTestConnection(feAddr, fePort)
{
	response_map = {};
	var ws = new WebSocket("ws://" + feAddr + ":" + fePort + "/map");
 
	var quadrants;
	ws.onmessage = function(event) 
	{ 
		var data_obj = JSON.parse(event.data);

		//console.log(data_obj);

		switch (data_obj['type']) {

			case "quadrant_list":
				quadrants = parseQuadrantList(data_obj['data']);
				startTest(quadrants, ws);
				break;

			default:
				on_message_(data_obj, quadrants);
				break;
		}
	}
	ws.onerror = function(event) { on_error(event); }
}

function on_message_(message, quadrants)
{
	var rID = message['r_id'];
	console.log("new message");
	var counter = response_map[rID];
	if(counter == null)
	{
		counter = 0;
	}

	response_map[rID] = counter + 1;
}


function startTest(quadrants, ws)
{
	messages_sent = 0;
	var maxSize = quadrants.length;
	var number_of_requests = 5;
	while (number_of_requests--)
	{
		setTimeout(function() {
			var number_of_quadrants = generate_random_number(maxSize);
			var request_arr = generate_request(number_of_quadrants);
			messages_sent += request_arr.length;
			console.log(request_arr);
			sendMapMessage(ws, request_arr);
		}, Math.random());

	}
}

function generate_random_number(maxSize)
{
	return Math.floor((Math.random() * maxSize) + 1);
}

function generate_request(num)
{
	console.log(num);
	return new Array(num).join().split(',').map(function(item, index){ return ++index;});

}

function evalutate_test()
{
	var message_received = 0;
	for (var key in response_map)
	{
		message_received += response_map[key]
	}

	console.log("Message sent: " + messages_sent + "- message received: " + message_received);
	messages_sent = 0;
}