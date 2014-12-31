import boto
from boto.dynamodb2.table import Table
import Parking as parking
import memcache
import traceback
import CacheManager as cm
class ParkingDYDBLoader:
	__database		=	0
	__cache			=	0
	__cacheClient	=	0
	__cache2Client	=	0
	__cexpire		=	0
	__qexpire		=	0
	__tablename     =   0 #da aggiungere
	__qhit			=	0
	__qmiss			=	0
	__phit			=	0
	__pmiss			=	0

	
	def __init__(self,myTableName,enableCache=False,myCacheURL=0,percentageCacheURL=0,cacheExpireTime=180,queryCacheExpire=120):
		self.tablename	=	myTableName#da aggiungere
		self.cache		=	enableCache
		self.cexpire	=	cacheExpireTime
		self.qexpire	=	queryCacheExpire
		self.qhit			=	0
		self.qmiss			=	0
		self.phit			=	0
		self.pmiss			=	0
		if (enableCache==True):	#sdcc.wpvbcm.cfg.usw2.cache.amazonaws.com:11211
			urlstring	=	str(myCacheURL)
			self.cacheClient	=	cm.CacheManager(myCacheURL,cacheExpireTime) #timeout verra passato a chiamata di funzione
			urlstring	=	str(percentageCacheURL)
			self.cache2Client	=	cm.CacheManager(percentageCacheURL,queryCacheExpire) #timeout verra passato a chiamata di funzione
	
	def setCacheTimeout(self,cacheExp,queryExp):
		print "ParkinkDYDBLoader: Changing timeouts"
		self.cexpire	=	cacheExp
		self.qexpire	=	queryExp		
	
	def update(self,aParking):
		parkingId	=	aParking.getId()
		if(self.cache==True):
			unposto		=	self.cacheClient.getValue(str(parkingId))
		if(not unposto):	#if I have cache miss retreive from DYDB
			try:
				database	=	boto.connect_dynamodb()
				tablelist	=	database.list_tables()
				#print	"ParkingDYDBLoader.py list of available tables "+str(tablelist)
				tableconn		=	database.get_table(str(self.mytable))
				unposto	= tableconn.get_item(aParking.getId())
				#print "ParkingDYDBLoader.py POSTO CACHE MISS"
				self.pmiss	=	self.pmiss+1
				print "ParkingDYDBLoader.py pmiss "+str(self.pmiss)+" phit "+str(self.phit)+" qmiss "+str(self.qmiss)+" qhit "+str(self.qhit)
				if(self.cache==True):
					self.cacheClient.setValue(str(aParking.getId()),unposto,int(self.cexpire))
			except Exception:
				print "error with DYNAMO DB"
				return -1
		else: 
			#print "ParkingDYDBLoader.py POSTO CACHE HIT"
			self.phit	=	self.phit+1
			print "ParkingDYDBLoader.py pmiss "+str(self.pmiss)+" phit "+str(self.phit)+" qmiss "+str(self.qmiss)+" qhit "+str(self.qhit)
		myParking	=	aParking
		lat		=	unposto['latitudine']
		lon		=	unposto['longitudine']
		state	=	unposto['stato']
		extra	=	unposto['extra']
		print "ParkingDYDBLoader.py "+str(lat)+" "+str(lon)+" "+str(state)+" "+str(extra)
		myParking.updateStatus(lat,lon,state,extra)
		print "ParkingDYDBLoader.py parking updated"
		return 0
		
	def getUtilizationPercentage(self,aQuadrant):
		quadrantID	=	aQuadrant.getID()
		if (self.cache==True):
			unastat	=	self.cache2Client.getValue(str(quadrantID))
			if not unastat:
				#print "ParkingDYDBLoader.py: cache miss with ID "+"Q_"+str(quadrantID)
				self.qmiss	=	self.qmiss+1
				#print "ParkingDYDBLoader.py pmiss "+str(self.pmiss)+" phit "+str(self.phit)+" qmiss "+str(self.qmiss)+" qhit "+str(self.qhit)
				return -1
			else:
				self.qhit	=	self.qhit+1
				print "ParkingDYDBLoader.py pmiss "+str(self.pmiss)+" phit "+str(self.phit)+" qmiss "+str(self.qmiss)+" qhit "+str(self.qhit)
			if unastat==101:	#test, probabilmente a memcached non piace lo 0
				unastat = 0
			#print "ParkingDYDBLoader.py: cache hit with ID "+"Q_"+str(quadrantID)+" value "+str(unastat)
			return float(unastat)
		return -1
		
	def setUtilizationPercentage(self,aQuadrant,perc):
		quadrantID	=	aQuadrant.getID()
		if (self.cache==True):
			try:
				if perc<1:
					perc=101	#test, probabilmente a memcached non piace lo 0
				res	=	self.cache2Client.setValue(str(quadrantID),str(perc),int(self.qexpire))
				#print "ParkingDYDBLoader.py: written in cache with ID "+"Q_"+str(quadrantID)+" with result "+str(res)+" the following value "+str(perc) 
			except:
				print "ParkingDYDBLoader.py: failed to set values"
			
	def batchQuery(self,idlist,parkDict):
		parkingListDict	=	parkDict
		myIdList		=	idlist
		batch	=	database.new_batch_list()
		database	=	boto.connect_dynamodb()
		tablelist	=	database.list_tables()
		#print	"ParkingDYDBLoader.py list of available tables "+str(tablelist)
		tableconn		=	database.get_table(str(self.mytable))
		batch.add_batch(tableconn,idlist)
		try:
			res		=	batch.submit()
			#print "ParkingDYDBLoader.py: risposta grezza: "+str(res)
			#print "ParkingDYDBLoader.py: la Query ha restituito: "+str(len(res['Responses'][str(self.table.name)]['Items']))
			for item in res['Responses'][str(tableconn.name)]['Items']:
				idp	=	item['idposto']
				lat		=	item['latitudine']
				lon		=	item['longitudine']
				state	=	item['stato']
				extra	=	item['extra']
				if(self.cache==True):
					#print "ParkingDYDBLoader.py: aggiunto in cache: key "+str(idp)+" value "+str(item)+" timeout "+str(self.cexpire)
					self.cacheClient.setValue(str(idp),item,int(self.cexpire))
					parkingListDict[int(idp)].updateStatus(lat,lon,state,extra)
				#print "ParkingDYDBLoader.py batchquery "+str(idp)+" "+str(state)+" "+str(parkingListDict[int(idp)].getStatus())
		except:
			print "ParkingDYDBLoader.py: error while reading DB "+str(res)
			print traceback.format_exc()
			return myIdList 	#se qualcosa va storto faccio fare nuova elaborazione completa 
		return res['UnprocessedKeys']
			
		
	def batchUpdate(self,parkingList):
		parkingListDict = 	{}	#key-value dictionary
		idList			=	list()	#list of id to be submitted to DynamoDb
		counter		=	0
		for item in parkingList:
			parkId	=	item.getId()
			if (self.cache==True):
				unposto	= self.cacheClient.getValue(str(parkId))
				if not unposto:
					self.pmiss	=	self.pmiss+1
					#print "ParkingDYDBLoader.py pmiss "+str(self.pmiss)+" phit "+str(self.phit)+" qmiss "+str(self.qmiss)+" qhit "+str(self.qhit)
					parkingListDict[parkId]=item
					idList.append(parkId)	
				else:
					lat		=	unposto['latitudine']
					lon		=	unposto['longitudine']
					state	=	unposto['stato']
					extra	=	unposto['extra']
					#print "ParkingDYDBLoader.py batch update CACHE HIT "+str(lat)+" "+str(lon)+" "+str(state)+" "+str(extra)
					self.phit	=	self.phit+1
					#print "ParkingDYDBLoader.py pmiss "+str(self.pmiss)+" phit "+str(self.phit)+" qmiss "+str(self.qmiss)+" qhit "+str(self.qhit)
					item.updateStatus(lat,lon,state,extra)
					 
			else:
				parkingListDict[parkId]=item
				idList.append(parkId)
		if(len(idList)>0):
			hundreds	=	int(len(idList)/100)+1
			#print "ParkingDYDBLoader.py: preparo "+str(hundreds)+" liste" 
			iterations	=	range(hundreds)
			counter		=	0
			for item in iterations:
				#print "ParkingDYDBLoader.py: elaboro lista "+str(counter)
				if counter<=hundreds:	
					templist	=	idList[counter*100:(((counter+1)*100))]
					#print "ParkingDYDBLoader.py: lunghezza lista da elaborare: "+str(len(templist))
					res = self.batchQuery(templist,parkingListDict)
					while len(res) >0:
						print "failed, retry"
						templist2	=	list()
						for item in res[str(self.tablename)]['Keys']:
							templist2.append(item['HashKeyElement'])
						res	=	self.batchQuery(templist2,parkingListDict)
						#raise Exception("Error while inserting in DYDB "+str(len(templist))+" "+str(len(parkingList))+" "+str(len(res['posti']['Keys'])))
				elif counter==hundreds:
					#print "ultimo batch"
					res = batchQuery(idList[counter*100:],parkingListDict)
					while len(res) >0:
						print "failed, retry"
						templist2	=	list()
						for item in res[(self.tablename)]['Keys']:
							templist2.append(item['HashKeyElement'])
						res	=	self.batchQuery(templist2,parkingListDict)
						#raise Exception("Error while inserting in DYDB"+str(len(res))+" "+str(len(parkingList)))
				counter	=	counter+1
		#print "parkings updated"
		
	def updateFromSensor(self, listab):
			tr=Table("APPosto_posti")#da correggere
			with tr.batch_write() as batch:
	
				for item in listab:
					
					
					batch.put_item(data={
					'idposto': item[0],
					'extra': item[1],
					'latitudine': item[2],
					'longitudine': item[3],
					'stato' : item[1]})
					if(self.cache==True):
						dictio={'idposto': item[0],
						'extra': item[1],
						'latitudine': item[2],
						'longitudine': item[3],
						'stato' : item[1]}
						self.cacheClient.setValue(str(item[0]),dictio,time=self.cexpire)
						dictio={}
					
					#park = self.table.get_item(parkid = item[0])
					#park ['stato']= item[1]
					#park.save()
				
			
		
		
		
		
		

