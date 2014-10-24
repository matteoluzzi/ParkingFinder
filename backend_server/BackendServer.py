import ParkingDYDBLoader as DBloader
import QuadrantHandler as qh
import SearchQuadrant as searchquadrant
import QuadrantTextFileLoader as loader
import Settings as settings
import threading

settingsHandler		=	settings.Settings("testimp.txt")
expiretime			=	int(settingsHandler.settings['cacheexpire'])
myQuadrantsId		=	settingsHandler.settings['quadrants']
myQuadrantsRangeStart	=	-1
try:
	myQuadrantsRangeStart	= settingsHandler.settings['rangeStart']	#if defined range OVERRIDES quadrants setting
	myQuadrantsRangeEnd	= settingsHandler.settings['rangeEnd']			#end NOT included in range, finishes at rangeEnd-1
except:
	pass


#initialize the loader from DB and a quadrant list

myDBLoader		= DBloader.ParkingDYDBLoader('posti',True,str("sdcc.wpvbcm.cfg.usw2.cache.amazonaws.com:11211"),expiretime)
listaQuadranti 	= searchquadrant.SearchQuadrant(loader.QuadrantTextFileLoader.load('listaquadranti.txt',myDBLoader))
#print expiretime
threadList	=	list()
if (myQuadrantsRangeStart >-1):
	print "Range start: "+str(myQuadrantsRangeStart)+" Range end "+str(myQuadrantsRangeEnd);
	st			=	int(myQuadrantsRangeStart)
	end			=	int(myQuadrantsRangeEnd)
	myCounter	=	st
	fakelist	=	range(end-st)
	myQuadrantsId	=	list()
	for fakeitem in fakelist:
		myQuadrantsId.append(myCounter)
		myCounter=myCounter+1
	
for item in myQuadrantsId:
	aquadrant	=	listaQuadranti.getQuadrantInstance(int(item))
	loader.QuadrantTextFileLoader.loadQuadrantParkings(aquadrant,"parkings/listquadrant"+str(int(item))+".txt",myDBLoader)
	#print aquadrant.getParkList()
	#myDBLoader.batchUpdate(aquadrant.getParkList()) #inizializzo in stato consistente	
	try:
		anHandler	=	qh.QuadrantHandler(aquadrant,settingsHandler,myDBLoader)
		anHandler.start()
		threadList.append(anHandler)
	except: 
		print "error while starting threads"
for item in threadList:
	item.join()
	

