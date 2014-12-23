import thread
import boto
import Settings as settings
import boto.sqs
from boto.sqs.message import Message
import threading
import json
import JSONManager as jm
import time
import NotificationServer as ns

class NotificationPoller (threading.Thread):
	__frequency		=	0
	__managerDict	=	0
	__rStart		=	0
	__rEnd			=	0
	__mysqsZone			=	0
	
	def __init__(self,frequency,aDict,rangeStart,rangeEnd,sqsZ):
		threading.Thread.__init__(self)
		self.frequency		=	frequency			#frequenza di polling
		self.managerDict	=	aDict
		self.mysqsZone		=	sqsZ
		self.rStart			=	rangeStart
		self.rEnd			=	rangeEnd	
	
	def run(self):
		#per ogni quadrante genera le richieste di overview ogni freqtime
		print "NotificationManager.py: connecting to SQS service in zone "+str(self.mysqsZone)
		conn = boto.sqs.connect_to_region(self.mysqsZone)
		if not conn:
			print "NotificationManager.py: error while connecting at"+self.mysqsZone+"zone"
		fakelist	=	range(int(self.rEnd)-int(self.rStart))
		while True:
			now	=	time.time()
			currentID	=	int(self.rStart)
			for item in fakelist:
				aRequestId				=	int(time.time())
				JsonRequest				=	jm.createOverviewRequest(aRequestId,"_APPosto_SDCC_notification_poller",currentID)
				destinationQueueName	=	"_APPosto_requests_queue"
				dest_queue = conn.get_queue(destinationQueueName)
				while dest_queue == None:
					dest_queue = conn.create_queue(str(destinationQueueName))
					if dest_queue==None:
						print "queue creation failed"
				m = Message()
				m.set_body(str(JsonRequest))
				dest_queue.write(m)
				currentID	=	currentID+1
			duration	=	time.time()-now
			print "NotificationManager: finito round richieste polling in "+str(duration)
			slack	=	int(self.frequency)-int(duration)
			if slack>0:
				print "NotificationManager: prossimo polling tra almeno "+str(slack)+" secondi"
				time.sleep(float(slack))	
				
class ResponseManager(threading.Thread):
	__managerDict	=	0
	__mysqsZone		=	0
	
	def __init__(self,aManagerDict,SQSzone):
		threading.Thread.__init__(self)
		self.managerDict	=	aManagerDict
		self.mysqsZone		=	SQSzone
		
	def run(self):
		#definisci coda su cui ricevere risposte e rimani in ascolto
		print "NotificationManager.py: connecting to SQS service in zone "+str(self.mysqsZone)
		conn = boto.sqs.connect_to_region(self.mysqsZone)
		if not conn:
			print "NotificationManager.py: error while connecting at"+self.mysqsZone+"zone"
		queueName	=	"_APPosto_SDCC_notification_poller"
		my_queue 	= 	conn.get_queue(queueName)
		while my_queue == None:
			print "NotificationManager.py: creating SQS queue "+queueName
			my_queue = conn.create_queue(str(queueName))
			if my_queue==None:
				print "NotificationManager.py: queue creation failed"
		while(1>0):
			#preleva i messaggi ed effettua il dispatch al manager corretto
			requests	=	my_queue.get_messages(wait_time_seconds=20)#tanto di default ne preleva solo 1
			#print "NotificationManager.py: queue "+str(queueName)+"pulled "+str(len(requests))+" messages"
			for item in requests:
				text		=	item.get_body()
				response	=	json.loads(text)
				response_id	=	response[0]
				quadrant_id	=	int(response[0]["quadrantID"])
				responseID	=	int(response[0]["r_id"])
				my_queue.delete_message(item)
				#print "NotificationManager.py: fetched response "+str(response_id)
				newPercentage	=	int(response[0]["percentage"])
				manager = self.managerDict[str(quadrant_id)]
				manager.manageEvent(newPercentage)
				print "NotificationManager.py: dispatched to "+str(manager)

class NotificationManager():
	__myQuadrantID	=	0
	__queueName		=	0
	__mysqsZone		=	0
	__prevStatus	=	0
	def __init__(self,anId,freq,sqsZone):
		self.myQuadrantID	=	anId			#quadrante da gestire
		self.mysqsZone		=	str(sqsZone)	#mistero... backspace in fondo a stringa
		self.prevStatus		=	0
	def manageEvent(self,newPercentage):
		#print "NotificationManager.py: connecting to SQS service in zone "+str(self.mysqsZone)
		conn = boto.sqs.connect_to_region(self.mysqsZone)
		if not conn:
			print "NotificationManager.py: error while connecting at"+self.mysqsZone+"zone"
		notifQueue	=	conn.get_queue("_APPosto_notificationQueue")
		while notifQueue == None:
			notifQueue = conn.create_queue("_APPosto_notificationQueue")
			if notifQueue==None:
				print "NotificationManager.py: queue creation failed"
		send	=	False
		delta	=	self.prevStatus	-	newPercentage
		if delta<0:
			delta=-delta
		if delta>10:
			send	=	True
		print "NotificationManager.py: delta on quadrant "+str(self.myQuadrantID)+" "+str(delta)
		if send==True:
			notifPayload	=	jm.sendNotificationForQuadrant(self.myQuadrantID,"New parkings available in quadrant "+str(self.myQuadrantID),"The available parkings are now "+str(newPercentage)+"%")
			m = Message()
			m.set_body(str(notifPayload))
			notifQueue.write(m)
		
settingsHandler		=	settings.Settings("testimp.txt")
try:
	myQuadrantsRangeStart	= 	settingsHandler.settings['rangeStart']	
	myQuadrantsRangeEnd		=	settingsHandler.settings['rangeEnd']		
	notificationFreq		=	settingsHandler.settings['notificationFreq']
	SQSZ					=	settingsHandler.settings['SQSzone']#mistero... backspace in fondo a stringa
	SQSZ					=	str(SQSZ)[:-1]
except:
	print "error while loading settings"
	
st			=	int(myQuadrantsRangeStart)
end			=	int(myQuadrantsRangeEnd)
myCounter	=	st
fakelist	=	range(end-st)
notifList	=	dict()
for item in fakelist:
	aNotManager	=	NotificationManager(myCounter,notificationFreq,SQSZ)
	notifList[str(myCounter)]	=	aNotManager
	myCounter	=	myCounter+1
poller		=	NotificationPoller(int(notificationFreq),notifList,st,end,SQSZ)
poller.start()
rManager	=	ResponseManager(notifList,SQSZ)
rManager.start()
testmio	=	ns.NotificationServer()
testmio.start()
testmio.join()
poller.join()


