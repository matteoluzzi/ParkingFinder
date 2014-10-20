import Settings as settings
import ParkingDYDBLoader as DBloader
import QuadrantHandler as qh
import SearchQuadrant as searchquadrant
import QuadrantTextFileLoader as loader
import threading

settingsHandler		=	settings.Settings("testimp.txt")
expiretime			=	int(settingsHandler.settings['cacheexpire'])
myQuadrantsId		=	settingsHandler.settings['quadrants']

#initialize the loader from DB and a quadrant list

myDBLoader		= DBloader.ParkingDYDBLoader('posti',True,str("sdcc.wpvbcm.cfg.usw2.cache.amazonaws.com:11211"),expiretime)
listaQuadranti 	= searchquadrant.SearchQuadrant(loader.QuadrantTextFileLoader.load('listaquadranti.txt',myDBLoader))
#print expiretime
threadList	=	list()
for item in myQuadrantsId:
	aquadrant	=	listaQuadranti.getQuadrantInstance(int(item))
	loader.QuadrantTextFileLoader.loadQuadrantParkings(aquadrant,"parkings/listquadrant"+str(int(item))+".txt",myDBLoader)
	#print aquadrant.getParkList()
	myDBLoader.batchUpdate(aquadrant.getParkList()) #inizializzo in stato consistente
	
	
		#test
	aquadrant.getSplitted(20)
	
	
	
	try:
		anHandler	=	qh.QuadrantHandler(aquadrant,settingsHandler,myDBLoader)
		anHandler.start()
		threadList.append(anHandler)
	except: 
		print "error while starting threads"
for item in threadList:
	item.join()
	

