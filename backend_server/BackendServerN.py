import ParkingDYDBLoader as DBloader
import QuadrantHandlerN as qh
import SearchQuadrant as searchquadrant
import QuadrantTextFileLoader as loader
import Settings as settings
import threading
import traceback
import time as tm
import random

class QuadrantPrefetching(threading.Thread): #precarica i dati in fase di slow start
	quadrantlist	=	0
	wtime			=	0
	idList			=	0
	def __init__(self,aquadrantlist,myidList,atime):
		threading.Thread.__init__(self)
		self.wtime			=	atime
		self.quadrantlist	=	aquadrantlist
		self.idList			=	myidList

	def run(self):
		for qitem in self.idList:
			myQuadrant = self.quadrantlist.getQuadrantInstance(int(qitem))
			print "Backendserver.py: prefetching quadrant "+str(myQuadrant.getID())
			myQuadrant.getPercentageFreeParkings()
			tm.sleep(self.wtime)
		return 0

class EndSlowStart(threading.Thread): #precarica i dati in fase di slow start
	wtime		=	0
	myloader	=	0
	myexpire	=	0
	myqexpire	=	0			
	def __init__(self,loader,time,expire,queryexpire):
		threading.Thread.__init__(self)
		self.myloader	=	loader
		self.wtime		=	time
		self.myexpire		=	expire
		self.myqexpire		=	queryexpire
	def run(self):
		tm.sleep(self.wtime)
		self.myloader.setCacheTimeout(self.myexpire,self.myqexpire)

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
	#anHandler	=	qh.QuadrantHandler(aquadrant,settingsHandler,myDBLoader)
	#anHandler.start()
	endSlow	=	EndSlowStart(myDBLoader,slowstart,expiretime,queryexpire)
	endSlow.start()
	fetcher		=	QuadrantPrefetching(listaQuadranti,myQuadrantsId,int(0))
	fetcher.start()
except: 
	print "BackendServer.py error while starting threads"
	print traceback.format_exc()
endCreation = False
threadCounter = 0
while endCreation==False:
	try:
		anHandler	=	qh.QuadrantHandler(listaQuadranti,settingsHandler,myDBLoader)
		anHandler.start()
	except:
		print "BackendServer.py no more threads allowed, number of threads created "+str(threadCounter)
		endCreation = True
		break
	threadCounter =	threadCounter+1
	threadList.append(anHandler)
	
while 1>0:
	for item in threadList:
		alive	=	item.isAlive()
		if alive==False:
			threadList.remove(item)
			anHandler	=	qh.QuadrantHandler(listaQuadranti,settingsHandler,myDBLoader)
			anHandler.start()
			threadList.append(anHandler)
			print "BackendServer: effettuato recovery thread"
	tm.sleep(60)
anHandler.join()
print "non devo stampare questo messaggio..."

	

