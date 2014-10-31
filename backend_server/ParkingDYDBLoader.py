import boto
from boto.dynamodb2.table import Table
import Parking as parking
import memcache

class ParkingDYDBLoader:
	__table			=	0
	__database		=	0
	__cache			=	0
	__cacheClient	=	0
	__cexpire		=	0
	__qexpire		=	0
	
	def __init__(self,myTableName,enableCache=False,myCacheURL=0,cacheExpireTime=60,queryCacheExpire=30):
		self.database	=	boto.connect_dynamodb()
		self.table		=	self.database.get_table(str(myTableName))
		self.cache		=	enableCache
		self.cexpire	=	cacheExpireTime
		self.qexpire	=	queryCacheExpire
		if (enableCache==True):	#sdcc.wpvbcm.cfg.usw2.cache.amazonaws.com:11211
			urlstring	=	str(myCacheURL)
			self.cacheClient	=	memcache.Client([urlstring])
	
	def update(self,aParking):
		parkingId	=	aParking.getId()
		if(self.cache==True):
			unposto		=	self.cacheClient.get(str(parkingId))
		if(not unposto):	#if I have cache miss retreive from DYDB
			try:
				unposto	= self.table.get_item(aParking.getId())
				#print "CACHE MISS"
				if(self.cache==True):
					self.cacheClient.set(str(aParking.getId()),unposto,time=self.cexpire)
			except Exception:
				print "error with DYNAMO DB"
				return -1
		#else: 
			#print "CACHE HIT"
		myParking	=	aParking
		lat		=	unposto['latitudine']
		lon		=	unposto['longitudine']
		state	=	unposto['stato']
		extra	=	unposto['extra']
		#print str(lat)+" "+str(lon)+" "+str(state)+" "+str(extra)
		myParking.updateStatus(lat,lon,state,extra)
		#print "parking updated"
		return 0
		
	def getUtilizationPercentage(aQuadrant):
		quadrantID	=	aQuadrant.getID()
		if (enableCache==True):
			unastat	=	self.cacheClient.get("Q_"+str(parkingId))
			return unastat
		return -1
		
	def setUtilizationPercentage(aQuadrant,perc):
		quadrantID	=	aQuadrant.getID()
		if (enableCache==True):
			self.cacheClient.set("Q_"+str(parkingId),perc,time=self.qexpire)
			
	def batchQuery(self,idlist,parkDict):
		parkingListDict	=	parkDict
		batch	=	self.database.new_batch_list()
		batch.add_batch(self.table,idlist)
		res		=	batch.submit()
		for item in res['Responses']['posti']['Items']:
			idp	=	item['idposto']
			lat		=	item['latitudine']
			lon		=	item['longitudine']
			state	=	item['stato']
			extra	=	item['extra']
			if(self.cache==True):
				self.cacheClient.set(str(idp),item,time=self.cexpire)
			parkingListDict[idp].updateStatus(lat,lon,state,extra)
		return res['UnprocessedKeys']
			
		
	def batchUpdate(self,parkingList):
		parkingListDict = 	{}	#key-value dictionary
		idList			=	list()	#list of id to be submitted to DynamoDb
		counter		=	0
		for item in parkingList:
			parkId	=	item.getId()
			if (self.cache==True):
				unposto	= self.cacheClient.get(str(parkId))
				if not unposto:
					#print "CACHE MISS"
					parkingListDict[parkId]=item
					idList.append(parkId)	
				else:
					lat		=	unposto['latitudine']
					lon		=	unposto['longitudine']
					state	=	unposto['stato']
					extra	=	unposto['extra']
					#print "CACHE HIT "+str(lat)+" "+str(lon)+" "+str(state)+" "+str(extra)
					item.updateStatus(lat,lon,state,extra)
					 
			else:
				parkingListDict[parkId]=item
				idList.append(parkId)
		if(len(idList)>0):
			hundreds	=	int(len(idList)/100)+1
			#print "preparo "+str(hundreds)+" liste" 
			iterations	=	range(hundreds)
			counter		=	0
			for item in iterations:
				#print "elaboro lista "+str(counter)
				if counter<=hundreds:	
					templist	=	idList[counter*100:(((counter+1)*100))]
					res = self.batchQuery(templist,parkingListDict)
					while len(res) >0:
						templist2	=	list()
						for item in res['posti']['Keys']:
							templist2.append(item['HashKeyElement'])
						res	=	self.batchQuery(templist2,parkingListDict)
						print "failed, retry"
						#raise Exception("Error while inserting in DYDB "+str(len(templist))+" "+str(len(parkingList))+" "+str(len(res['posti']['Keys'])))
				elif counter==hundreds:
					#print "ultimo batch"
					res = batchQuery(idList[counter*100:],parkingListDict)
					while len(res) >0:
						templist2	=	list()
						for item in res['posti']['Keys']:
							templist2.append(item['HashKeyElement'])
						res	=	self.batchQuery(templist2,parkingListDict)
						print "failed, retry"
						#raise Exception("Error while inserting in DYDB"+str(len(res))+" "+str(len(parkingList)))
				counter	=	counter+1
		#print "parkings updated"
		
		
		
		

