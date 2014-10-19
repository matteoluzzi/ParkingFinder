var map;
function initialize() {
                var element = $("#map")[0];
 
                window.map = new google.maps.Map(element, {
                center: new google.maps.LatLng(41.88976989299657, 12.514091491699224),
                zoom: 12,
                mapTypeId: "OSM",
                mapTypeControl: false,
                streetViewControl: false
            });
                
 
            //Define OSM map type pointing at the OpenStreetMap tile server
                window.map.mapTypes.set("OSM", new google.maps.ImageMapType({
                getTileUrl: function(coord, zoom) {
                    return "http://tile.openstreetmap.org/" + zoom + "/" + coord.x + "/" + coord.y + ".png";
                },
                tileSize: new google.maps.Size(256, 256),
                name: "OpenStreetMap",
                maxZoom: 18
            }));

            google.maps.event.addListener(map, 'zoom_changed', function() {
                //alert(window.map.getZoom() + "\n" + window.map.getBounds());
                sendZoomLevel(map.getZoom(), map.getBounds());


            });

            google.maps.event.addListener(map, 'bounds_changed', function() {
                //evento che cattura i cambiamenti di confine della mappa visualizzati, può essere oneroso
            })

            }

function checkMapInfo() 
{
    zoom = window.map.getZoom();
    center = window.map.getCenter().toString();
    alert("zoom:" + zoom + "center: " + center);
}

function sendZoomLevel(zoom, bounds) {

    //var xmlhttp;
    //if (window.XMLHttpRequest)
    //{// code for IE7+, Firefox, Chrome, Opera, Safari
//        xmlhttp = new XMLHttpRequest();
//    }
//    else
//    {// code for IE6, IE5
//        xmlhttp = new ActiveXObject("Microsoft.XMLHTTP");
//    }

    //xmlhttp.open("POST","http://localhost:8080/map",true);
    //xmlhttp.setRequestHeader("Content-type","application/x-www-form-urlencoded");


    var neLat = bounds.getNorthEast().lat();
    var neLon = bounds.getNorthEast().lng();
    var swLat = bounds.getSouthWest().lat();
    var swLon = bounds.getSouthWest().lng();
    var id = generateUUID();
    
	var data = "id=" + id + "&zoom_level=" + zoom + "&neLat=" + neLat + "&neLon=" + neLon + "&swLat=" + swLat + "&swLon=" + swLon;

	$.ajax({
		type : "POST",
		url : "http://localhost:8080/map",
		data : data,
		contentType : "application/x-www-form-urlencoded",
		success : function (result) {
			var response = JSON.parse(result);
			console.log(response, typeof response);
			parseAndDrow(response);
		},
		error: function (jqXHR, textStatus, errorThrown)
	    {
			jsonValue = $.parseJSON( jqXHR.responseText );
			console.log(jsonValue.Message);
	    } 
		
	});

    //xmlhttp.send("id=" + id + "&zoom_level=" + zoom + "&neLat=" + neLat + "&neLon=" + neLon + "&swLat=" + swLat + "&swLon=" + swLon);

//    xmlhttp.onreadystatechange = function () {
//        if (this.readyState == 4 && this.status == 200) {
//            var JSONresponse = this.responseText;
//            var response = JSON.parse(JSONresponse);
//            console.log(response, typeof response);
//            parseAndDrow(response);
//        }
//    }
}

function generateUUID() {
    var d = new Date().getTime();
    var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = (d + Math.random()*16)%16 | 0;
        d = Math.floor(d/16);
        return (c=='x' ? r : (r&0x7|0x8)).toString(16);
    });
    return uuid;
};

function parseAndDrow(msg) {
	
    if(msg.length > 0) {
        for (var i = 0; i < msg.length; i++) {
            var zoom = msg[i].zoom;
            var int_zoom = parseInt(zoom, 10);
            console.log(zoom + " " + window.map.getZoom());

            if(int_zoom >= 15 && zoom == window.map.getZoom()) {
                var image = 'http://icons.iconarchive.com/icons/e-young/gur-project/32/map-pointer-icon.png';
                console.log(image);
                var latLng = window.map.getCenter()
                var marker = new google.maps.Marker({
                    position: latLng,
                    map: window.map,
                    icon: image
                });
            }
            else {
                break;
            }
        }

    }

    

}
