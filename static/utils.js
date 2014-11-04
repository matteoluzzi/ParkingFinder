//carica la lista dei quadranti in modo asincrono, eseguendo la callback a caricamento completato
function loadQuadrantsList(callback)
{
		$.ajax({
			type : "GET",
			url : "http://localhost:8000/workspace/workspace_python/ParkingFinder/static/listaquadranti.txt",
			data : null,
			success : function(response) {
				callback(response);
			},
			error : function(jqXHR, textStatus, errorThrown) {
				console.log("errore nel caricare la lista");
				callback(-1);

			}
		});

}