#this class models the entity "quadrant", each quadrant has an ID and is bounded by 4 coordinates and a parklist
import copy
import json
import Parking as pk
import gc

class Quadrant:
	__qid	=	0
	__NW	=	0
	__NE	=	0
	__SW	=	0
	__SE	=	0
	__parklist	=	0
	updater	=	0
	
	def __init__(self,myid,myNW,myNE,mySW,mySE,myupdater=0):
		self.qid	=	myid
		self.NW	=	myNW
		self.NE	=	myNE
		self.SW	=	mySW
		self.SE	=	mySE
		self.updater	=	myupdater
		self.parklist	=	list()

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
		if int(self.getNumberOfParkings())==0:
			return 0
		cacheRis	=	self.updater.getUtilizationPercentage(self)
		if (int(cacheRis)>-1):
			print "Quadrant.py: Cache hit percentage quadrant"+str(self.qid)
			return cacheRis
		free	=	0
		print "Quadrant.py number of parkings in quadrant "+str(self.qid)+" = "+str(self.getNumberOfParkings())
		parkingList	=	self.getParkList() 
		self.updater.batchUpdate(parkingList)
		for item in parkingList:
			state	=	item.getStatus()
			#print "Quadrant.py state of parking "+str(item.getId())+" is "+str(state)
			if str(state)=="E":
				free	=	free+1
		perc	=	(free/len(self.parklist))*100
		self.updater.setUtilizationPercentage(self,perc)
		del parkingList
		gc.collect()
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
			
