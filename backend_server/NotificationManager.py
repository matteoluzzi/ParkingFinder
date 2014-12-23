import thread
import boto
import Settings as settings
import boto.sqs
from boto.sqs.message import Message
import threading
import json
import JSONManager as jm
import time

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
		self.mysqsZone			=	sqsZ
	
	def run(self):
		#per ogni quadrante genera le richieste di overview ogni freqtime
		print "NotificationManager.py: connecting to SQS service in zone "+str(self.mysqsZone)
		conn = boto.sqs.connect_to_region(self.mysqsZone)
		if not conn:
			print "NotificationManager.py: error while connecting at"+self.mysqsZone+"zone"
		fakelist	=	range(int(self.rStart)-int(self.rStart))
		while True:
			now	=	time.time()
			currentID	=	int(self.rStart)
			for item in fakelist:
				aRequestId				=	int(time.time())
				JsonRequest				=	jm.createOverviewRequest(aRequestId,"_APPosto_SDCC_notification_poller",self.currentID)
				destinationQueueName	=	"_APPosto_requests_queue"
				dest_queue = conn.get_queue(destinationQueueName)
				while dest_queue == None:
					dest_queue = conn.create_queue(str(destinationQueueName))
					if dest_queue==None:
						print "queue creation failed"
				m = Message()
				m.set_body(str(JsonRequest))
				dest_queue.write(m)
			duration	=	time.time()-now
			print "NotificationManager: finito round richieste polling in "+str(duration)
			slack	=	int(frequency)-int(duration)
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
			print "NotificationManager.py: queue "+str(queueName)+"pulled "+str(len(requests))+" messages"
			for item in requests:
				text		=	item.get_body()
				response	=	json.loads(text)
				response_id	=	response[0]
				quadrant_id	=	int(response[0]["quadrantID"])
				responseID	=	int(response[0]["r_id"])
				my_queue.delete_message(item)
				print "NotificationManager.py: fetched response "+str(response_id)
				newPercentage	=	double(response[0]["percentage"])
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
		myRegion			=	str(sqsZone)	#regione SQS
		self.mysqsZone		=	myRegion[:-1] 	#mistero... backspace in fondo a stringa
	
	def manageEvent(self,newPercentage):
		print "connecting to SQS service in zone "+str(self.mysqsZone)
		conn = boto.sqs.connect_to_region(self.mysqsZone)
		if not conn:
			print "error while connecting at"+self.mysqsZone+"zone"
		notifQueue	=	conn.get_queue("notificationQueue")
		while notifQueue == None:
			notifQueue = conn.create_queue("notificationQueue")
			if notifQueue==None:
				print "queue creation failed"
		send	=	False
		if prevStatus>50:
			if newPercentage<=50:
				send	=	True
		elif prevStatus>25:
			if newPercentage<=25:
				send	=	True
		elif newPercentage>5:
				send	=	True
		if send==True:
			notifPayload	=	jm.sendNotificationForQuadrant(response[0]["quadrantID"],"New parkings available in quadrant "+str(response[0]["quadrantID"]),"The available parkings are now "+str(newPercentage))
			m = Message()
			m.set_body(str(notifPayload))
			notifQueue.write(m)
		
settingsHandler		=	settings.Settings("testimp.txt")
try:
	myQuadrantsRangeStart	= 	settingsHandler.settings['rangeStart']	
	myQuadrantsRangeEnd		=	settingsHandler.settings['rangeEnd']		
	notificationFreq		=	settingsHandler.settings['notificationFreq']
	SQSZ					=	settingsHandler.settings['SQSzone']
except:
	print "error while loading settings"
	
st			=	int(myQuadrantsRangeStart)
end			=	int(myQuadrantsRangeEnd)
myCounter	=	st
fakelist	=	range(end-st)
notifList	=	dict()
for item in fakelist:
	aNotManager	=	NotificationManager(myCounter,notificationFreq,SQSZ)
	notifList[str(myCounter)]	=	myCounter
	myCounter	=	myCounter+1
poller		=	NotificationPoller(int(notificationFreq),notifList,st,end,SQSZ)
poller.start()
rManager	=	ResponseManager(notifList,SQSZ)
rManager.start()
poller.join()


