import json
class Parking:
	__parkid	=	0
	__latitude	=	0
	__longitude	=	0
	__status	=	0
	__extra		=	0
	__parkingUpdater=	0

	def __init__(self,my_id,updater=0,parkLatitude=0,parkLongitude=0):
		self.parkid		=	my_id
		self.parkingUpdater	=	updater
		self.latitude		=	parkLatitude
		self.longitude		=	parkLongitude
		self.status			=	0
		self.extra		=	0
		
	#equivalent toString() on Java
	def __str__(self):
		return str(self.parkid)+" lat "+str(self.latitude)+" lon "+str(self.longitude)+" state "+str(self.status)+" extra "+str(self.extra) 
	
	def update(self):
		data = self.parkingUpdater.update(self)
	
	def getId(self):
		return int(self.parkid)
	
	def getLatitude(self):
		return float(self.latitude)
	
	def getLongitude(self):
		return float(self.longitude)
	
	def updateStatus(self,lat,lon,state,newextra):
		self.latitude	=	lat
		self.longitude	=	lon
		self.status		=	state
		self.extra		=	newextra
	
	def getStatus(self):
		return self.status
	
	def getExtra(self):
		return self.extra
	
	def getDictionary(self):
		data			=	{"id":self.parkid , "lat":self.latitude , "lon":self.longitude, "state":self.status, "extra":self.extra}
		return data	
	
	def loadFromJson(self,aString,aLoader):
		myDict	=	json.loads(aString)
		self.parkid		=	int(myDict["id"])
		self.latitude	=	float(myDict["lat"])
		self.longitude	=	float(myDict["lon"])
		self.status		=	str(myDict["state"])
		self.extra		=	str(myDict["extra"])
		self.parkingUpdater=aLoader
		
		
