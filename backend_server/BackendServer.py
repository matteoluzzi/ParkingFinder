import ParkingDYDBLoader as DBloader
import QuadrantHandler as qh
import SearchQuadrant as searchquadrant
import QuadrantTextFileLoader as loader
import Settings as settings
import threading
import traceback
import time as tm
import random

class QuadrantPrefetching(threading.Thread): #precarica i dati in fase di slow start
	quadrant	=	0
	wtime		=	0
	def __init__(self,aquadrant,time):
		threading.Thread.__init__(self)
		wtime			=	random.randint(0,time)
		self.quadrant	=	aquadrant

	def run(self):
		tm.sleep(self.wtime)
		print "Backendserver.py: prefetching"
		self.quadrant.getPercentageFreeParkings()
		return 0
		

print "starting server"
settingsHandler		=	settings.Settings("testimp.txt")
expiretime			=	int(settingsHandler.settings['cacheexpire'])
queryexpire			=	int(settingsHandler.settings['queryexpire'])
slowstart			=	int(settingsHandler.settings['slowstart'])		#slowstart duration
myQuadrantsId		=	settingsHandler.settings['quadrants']
myQuadrantsRangeStart	=	-1
cacheUrl		=	-1
try:
	cacheUrl		=	str(settingsHandler.settings['cacheurl'])
	myQuadrantsRangeStart	= settingsHandler.settings['rangeStart']	#if defined range OVERRIDES quadrants setting
	myQuadrantsRangeEnd	= settingsHandler.settings['rangeEnd']			#end NOT included in range, finishes at rangeEnd-1
except:
	print "BackendServer.py: range not present, passing out"
enablecache	=	False
if (cacheUrl > -1):
	print "BackendServer.py: cache url: "+cacheUrl+"---"
	cacheUrl	=	cacheUrl[:-1]	#special characters at the end of string
	enablecache	=	True
else:
	print "BackendServer.py: cache disabled"
#initialize the loader from DB and a quadrant list

myDBLoader		= DBloader.ParkingDYDBLoader('APPosto_posti',enablecache,cacheUrl,slowstart,slowstart)
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
		fetcher		=	QuadrantPrefetching(aquadrant,slowstart)
		fetcher.start()
		threadList.append(anHandler)
	except: 
		print "error while starting threads"
		print traceback.format_exc()
tm.sleep(slowstart)
while 1:
	for item in threadList:
		alive	=	item.isAlive()
		if alive==False:
			threadList.remove(item)
			aQuadrant	=	item.quadrant
			anHandler	=	qh.QuadrantHandler(aquadrant,settingsHandler,myDBLoader)
			anHandler.start()
			threadList.append(anHandler)
			print "BackendServer: effettuato recovery thread quadrante "+str(aQuadrant.getID())
	time.sleep(60)
			
myDBLoader.setCacheTimeout(expiretime,queryexpire)
anHandler.join()
print "non devo stampare questo messaggio..."

	

