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
		while(1>0):
			for qitem in self.idList:
				myQuadrant = self.quadrantlist.getQuadrantInstance(int(qitem))
				myQuadrant.getPercentageFreeParkings()
			tm.sleep(self.wtime)

class EndSlowStart(threading.Thread): 
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

settingsHandler		=	settings.Settings("testimp.txt")
expiretime			=	int(settingsHandler.settings['cacheexpire'])
queryexpire			=	int(settingsHandler.settings['queryexpire'])
slowstart			=	int(settingsHandler.settings['slowstart'])		#slowstart duration
myQuadrantsId		=	settingsHandler.settings['quadrants']
nThreads			=	int(settingsHandler.settings['poolsize'])
myQuadrantsRangeStart	=	-1
cacheUrl		=	-1
try:
	cacheUrl		=	str(settingsHandler.settings['cacheurl'])
	cache2Url		=	str(settingsHandler.settings['cache2url'])
	myQuadrantsRangeStart	= settingsHandler.settings['rangeStart']	#if defined range OVERRIDES quadrants setting
	myQuadrantsRangeEnd	= settingsHandler.settings['rangeEnd']			#end NOT included in range, finishes at rangeEnd-1
except:
	print "BackendServer.py: range not present, passing out"
enablecache	=	False
if (cacheUrl > -1):
	cacheUrl	=	cacheUrl[:-1]	#special characters at the end of string
	cache2Url	=	cache2Url[:-1]	#special characters at the end of string
	enablecache	=	True
else:
	print "BackendServer.py: cache disabled"
#initialize the loader from DB and a quadrant list

myDBLoader		= DBloader.ParkingDYDBLoader('APPosto_posti',enablecache,cacheUrl,cache2Url,slowstart,slowstart)
listaQuadranti 	= searchquadrant.SearchQuadrant(loader.QuadrantTextFileLoader.load('listaquadranti.txt',myDBLoader))
threadList	=	list()
if (myQuadrantsRangeStart >-1):
	st			=	int(myQuadrantsRangeStart)
	end			=	int(myQuadrantsRangeEnd)
	myCounter	=	st
	fakelist	=	range(end-st)
	myQuadrantsId	=	list()
	print "Backendserver.py: loading quadrants list"
	for fakeitem in fakelist:
		myQuadrantsId.append(myCounter)
		myCounter=myCounter+1
	print "Backendserver.py: quadrants list loaded"
	
for item in myQuadrantsId:
	aquadrant	=	listaQuadranti.getQuadrantInstance(int(item))
	print "Backendserver.py: loading quadrant instance "+str(int(item))
	loader.QuadrantTextFileLoader.loadQuadrantParkings(aquadrant,"parkings/listquadrant"+str(int(item))+".txt",myDBLoader)	
	
try:
	endSlow	=	EndSlowStart(myDBLoader,slowstart,expiretime,queryexpire)
	endSlow.start()
	fetcher		=	QuadrantPrefetching(listaQuadranti,myQuadrantsId,queryexpire)
	fetcher.start()
except: 
	print "BackendServer.py error while starting threads"
	print traceback.format_exc()
endCreation = False
threadCounter = 0
print "BackendServer.py starting serving threads"
while threadCounter<nThreads:
	try:
		anHandler	=	qh.QuadrantHandler(listaQuadranti,settingsHandler,myDBLoader,threadCounter)
		anHandler.start()
	except:
		endCreation = True
		break
	threadCounter =	threadCounter+1
	threadList.append(anHandler)
threadCounter = 0
while 1>0:
	try:
		for item in threadList:
			alive	=	item.isAlive()
			if alive==False:
				threadList.remove(item)
				anHandler	=	qh.QuadrantHandler(listaQuadranti,settingsHandler,myDBLoader,threadCounter)
				anHandler.start()
				threadList.append(anHandler)
				threadCounter	=	threadCounter+1
				print "BackendServer: effettuato recovery thread"
		tm.sleep(60)
	except:
		print traceback.format_exc()
		print "BackendServer.py: errore in check threads"
anHandler.join()
	

