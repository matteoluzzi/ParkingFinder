#this class models the entity "quadrant", each quadrant has an ID and is bounded by 4 coordinates and a parklist
import copy
import json
import Parking as pk
import gc
import time as tm
import threading

class Quadrant:
	__qid	=	0
	__NW	=	0
	__NE	=	0
	__SW	=	0
	__SE	=	0
	__parklist	=	0
	updater	=	0
	overview_lock	=	0
	def __init__(self,myid,myNW,myNE,mySW,mySE,myupdater=0):
		self.qid	=	myid
		self.NW	=	myNW
		self.NE	=	myNE
		self.SW	=	mySW
		self.SE	=	mySE
		self.updater	=	myupdater
		self.parklist	=	list()
		self.overview_lock	=	threading.Lock()

	#def changeParkList(self,aList):
	#	self.parklist	=	aList

	def addToParkList(self,anItem):
		if self.parklist==0:
			self.parklist = list()
		coordinates = [anItem.getLatitude(),anItem.getLongitude()]
		if self.inside(coordinates):
			parkDict	=	anItem.getDictionary()
			myString	=	json.dumps(parkDict)
			self.parklist.append(myString)
		else:
			raise Exception("wrong inserting")

	def getID(self):
		return int(self.qid)
		
	def getNumberOfParkings(self):
		if self.parklist==0:
			return 0
		return len(self.parklist)
		
	def getParkList(self):
		aList	=	list()
		for item in self.parklist:
			aPark	=	pk.Parking(0) #nuovo parking con id fasullo verra aggiornato dopo
			aPark.loadFromJson(item,self.updater)
			aList.append(aPark)
		return aList
	
	def getPercentageFreeParkings(self):
		nparkings	=	self.getNumberOfParkings()
		if int(nparkings)==0:
			return 0
		startTime	=	float(tm.time())
		self.overview_lock.acquire()
		myTime	=	float(tm.time()) - float(startTime)
		print "Quadrant.py tempo sul lock: "+str(myTime)
		cacheRis	=	self.updater.getUtilizationPercentage(self)
		myTime	=	float(tm.time()) - float(startTime)
		if (int(cacheRis)>-1):
			#print "Quadrant.py: Cache hit percentage quadrant"+str(self.qid)+" cache time access "+str(myTime)
			self.overview_lock.release()
			return cacheRis
		else:
			try:
				free	=	0
				#print "Quadrant.py number of parkings in quadrant "+str(self.qid)+" = "+str(self.getNumberOfParkings())
				#print "Quadrant.py CACHE MISS"
				parkingList	=	self.getParkList() 
				self.updater.batchUpdate(parkingList)
				for item in parkingList:
					state	=	item.getStatus()
					#print "Quadrant.py state of parking "+str(item.getId())+" is "+str(state)+" timestamp "+str(item.timestamp)
					if str(state)=="E":
						free	=	free+1
				#print "Quadrant.py state of quadrant: free "+str(free)+" total "+str(nparkings)
				perc	=	((float(free))/(float(len(self.parklist))))*100
				self.updater.setUtilizationPercentage(self,perc)
				self.overview_lock.release()
			except:
				print "Quadrant.py: catch di un eccezione: "
				print traceback.format_exc()
				print "Quadrant.py: eccezione gestita effettuo unlock risorse: "
				self.overview_lock.release()
				perc	=	-1
			return perc
		
		
		
	#check if a coordinate pair belongs to this quadrant
	def inside(self,point):
		pointlatitude	=	float(point[0])
		pointlongitude	=	float(point[1])
		minlon		=	float(self.SW[1])
		maxlon		=	float(self.NE[1])
		minlat		=	float(self.SW[0])
		maxlat		=	float(self.NE[0])
		if pointlongitude>minlon:
			if	pointlongitude<=maxlon:
				if	pointlatitude>minlat:
					if	pointlatitude<=maxlat:
						#print "Punto appartenente al quadrante "+self.qid
						return True
		return False
		
	def getBoundaries(self):
		retVal			=	dict()
		retVal['NW']	=	copy.deepcopy(self.NW)
		retVal['NE']	=	copy.deepcopy(self.NE)
		retVal['SW']	=	copy.deepcopy(self.SW)
		retVal['SE']	=	copy.deepcopy(self.SE)
		return retVal
	
	def getCenter(self):
		minlon		=	float(self.NW[1])
		maxlon		=	float(self.SE[1])
		minlat		=	float(self.SE[0])
		maxlat		=	float(self.NW[0])
		centerlat	=	minlat + ((maxlat-minlat)/2)
		centerlon	=	minlon + ((maxlon-minlon)/2)
		result		=	dict()
		result['lat']	=	centerlat
		result['lon']	=	centerlon
		return result 
		
	def getSplitted(self,obsize): #return list of 4 quarters of quadrant
		minlon		=	float(self.NW[1])
		maxlon		=	float(self.SE[1])
		minlat		=	float(self.SE[0])
		maxlat		=	float(self.NW[0])
		centerlat	=	minlat + ((maxlat-minlat)/2)
		centerlon	=	minlon + ((maxlon-minlon)/2)
		q1			=	Quadrant(-1,self.NW,[maxlat,centerlon],[centerlat,minlon],[centerlat,centerlon])
		q2			=	Quadrant(-1,[maxlat,centerlon],self.NE,[centerlat,centerlon],[centerlat,maxlon])
		q3			=	Quadrant(-1,[centerlat,minlon],[centerlat,centerlon],self.SW,[minlat,centerlon])
		q4			=	Quadrant(-1,[centerlat,centerlon],[centerlat,maxlon],[minlat,centerlon],self.SE)
		parkingList	=	self.getParkList() 
		for item in parkingList:
			coordinates = [item.getLatitude(),item.getLongitude()]
			if q1.inside(coordinates):
				q1.addToParkList(item)
			elif q2.inside(coordinates):
				q2.addToParkList(item)
			elif q3.inside(coordinates):
				q3.addToParkList(item)	
			elif q4.inside(coordinates):
				q4.addToParkList(item)
			#else:
			#	raise Exception("error while splitting")
		total	=	int(len(q1.getParkList()))+int(len(q2.getParkList()))+int(len(q3.getParkList()))+int(len(q4.getParkList()))
		value1	=	len(self.parklist)
		print "check "+str(len(self.parklist))+" "+str(total)
		if not (total==value1):
			raise Exception("Wrong splitting error!")
		print "check2 "+str(len(q1.getParkList()))+" "+str(len(q2.getParkList()))+" "+str(len(q3.getParkList()))+" "+str(len(q4.getParkList()))
		returnlist	=	list()
		templist	=	[q1,q2,q3,q4]
		for item in templist:
			if (item.getNumberOfParkings()>obsize):
				templist2	=	item.getSplitted(obsize)
				for inneritem in templist2:
					returnlist.append(inneritem)
			else:
				returnlist.append(item)
		return returnlist
			
