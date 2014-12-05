import threading
import memcache
import boto

class TestW(threading.Thread): #precarica i dati in fase di slow start
	thid			=	0
	mycache			=	0
	def __init__(self,threadId,cmanager):
		threading.Thread.__init__(self)
		self.thid			=	threadId
		self.mycache		=	cmanager

	def run(self):
		value	=	mycache.getValue(str(thid))
		print "CacheManager.py read "+str(value)
		return 0
		
class TestR(threading.Thread): #precarica i dati in fase di slow start
	thid			=	0
	mycache			=	0
	def __init__(self,threadId,cmanager):
		threading.Thread.__init__(self)
		self.thid			=	threadId
		self.mycache		=	cmanager

	def run(self):
		mycache.setValue(str(thid),str(thid))
		return 0

class CacheManager:
	client		=	0
	lock		=	0
	myTimeout	=	0
	nRead		=	0
	eWrite		=	0
	
	def __init__(self,cacheURL,aTimeout):
		self.client		=	memcache.Client([str(cacheURL)])
		self.lock		=	threading.Lock()
		self.myTimeout	=	int(aTimeout)
		
	def setValue(self,aKey,aValue):
		self.lock.acquire()
		res 	= 	self.client.set(str(aKey),aValue,time=myTimeout)
		self.lock.release()
		
	def getValue(self,aKey): 
		self.lock.acquire()
		res 	= 	self.client.get(str(aKey))
		self.lock.release()
		return res
		
test = CacheManager('appostocache2.ndaqz6.cfg.euw1.cache.amazonaws.com:11211',999)
counter = 0
while (counter<1000):
	counter = counter+1
	tt		=	TestW(counter,test)
	tt.start()
	
while (counter<1000):
	counter = counter+1
	tt		=	TestR(counter,test)
	tt.start()
	
	
