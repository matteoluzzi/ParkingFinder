import threading
import memcache
import boto

class TestR(threading.Thread): #precarica i dati in fase di slow start
	thid                    =       0
	mycache                 =       0
	def __init__(self,threadId,cmanager):
			threading.Thread.__init__(self)
			self.thid                       =       threadId
			self.mycache            =       cmanager

	def run(self):
			value   =       self.mycache.getValue("Q_"+str(self.thid))
			#print "CacheManager.py read "+str(value)
			return 0

class TestW(threading.Thread):
	thid                    =       0
	mycache                 =       0
	def __init__(self,threadId,cmanager):
			threading.Thread.__init__(self)
			self.thid                       =       threadId
			self.mycache            =       cmanager

	def run(self):
			#print "scrivo"
			self.mycache.setValue("Q_"+str(self.thid),str(self.thid))
			return 0

class CacheManager:
	client          =       0
	lock            =       0
	myTimeout       =       0
	nRead           =       0
	eWrite          =       0

	def __init__(self,cacheURL,aTimeout):
		self.client             =       memcache.Client([str(cacheURL)])
		self.lock               =       threading.Lock()
		self.myTimeout  =       int(aTimeout)
		
	def setValue(self,aKey,aValue,timeout=-1):
		aTimeout = self.myTimeout
		if(timeout>-1):
			aTimeout	=	int(timeout)
		self.lock.acquire()
		res     =       self.client.set(str(aKey),aValue,time=aTimeout)
		self.lock.release()

	def getValue(self,aKey):
		self.lock.acquire()
		res     =       self.client.get(str(aKey))
		self.lock.release()
		return res

#test = CacheManager('appostocache2.ndaqz6.cfg.euw1.cache.amazonaws.com:11211',999)
#counter = 0
#while (counter<1000):
#       counter = counter+1
#       tt              =       TestW(counter,test)
#       tt.start()

#counter = 0
#while (counter<1000):
#        counter = counter+1
#        tt              =       TestR(counter,test)
#        tt.start()







	
