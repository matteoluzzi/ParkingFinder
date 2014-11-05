import thread
import boto
import Settings as settings
import boto.sqs
from boto.sqs.message import Message
import threading
import json
import JSONManager as jm
import time

#main code creates a thread for each quandrant managed, if the % of the
#occupation crosses a threshold sends a notification to the right queue

class NotificationManager(threading.Thread):
	__myQuadrantID	=	0
	__frequency		=	0
	__queueName		=	0
	__mysqsZone		=	0
	def __init__(self,anId,freq,sqsZone):
		threading.Thread.__init__(self)
		self.myQuadrantID	=	anId
		self.frequency		=	freq	
		myRegion			=	str(sqsZone)
		self.mysqsZone		=	myRegion[:-1] #mistero... backspace in fondo a stringa
	
	
	def run(self):
		prevStatus	=	0	#0% free parkings
		print "connecting to SQS service"
		conn = boto.sqs.connect_to_region(self.mysqsZone)
		if not conn:
			print "error while connecting at"+self.mysqsZone+"zone"
		queueName	=	"_SDCC_NOTIFICATION"+str(self.myQuadrantID)
		my_queue 	= 	conn.get_queue(queueName)
		notifQueue	=	conn.get_queue("notificationQueue")
		#print "pippo" + str(my_queue)
		while my_queue == None:
			print "creating SQS queue "+queueName
			my_queue = conn.create_queue(str(queueName))
			if my_queue==None:
				print "queue creation failed"
		print my_queue
		while True:
			print "Checking status notifications for the following quadrant"+str(self.myQuadrantID)
			aRequestId				=	int(time.time())
			JsonRequest				=	jm.createOverviewRequest(aRequestId,queueName,self.myQuadrantID)
			destinationQueueName	=	"_SDCC_"+str(self.myQuadrantID)
			dest_queue = conn.get_queue(destinationQueueName)
			while dest_queue == None:
				dest_queue = conn.create_queue(str(destinationQueueName))
				if dest_queue==None:
					print "queue creation failed"
			print "destination queue "+str(dest_queue)
			m = Message()
			m.set_body(str(JsonRequest))
			dest_queue.write(m)
			print "message sent on "+str(dest_queue)
			receivedAnswer	= False
			while not receivedAnswer:
				requests	=	my_queue.get_messages(wait_time_seconds=20)#tanto di default ne preleva solo 1
				print "queue "+str(queueName)+"pulled "+str(len(requests))+" messages"
				for item in requests:
					text		=	item.get_body()
					my_queue.delete_message(item)
					response	=	json.loads(text)
					response_id	=	response[0]
					print response[0]
					print response[0]["r_id"]
					responseID	=	int(response[0]["r_id"])
					if responseID==aRequestId:
						print "fetched response "+str(response_id)
						receivedAnswer	=	True
						newPercentage	=	response[0]["percentage"]
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
			time.sleep(float(self.frequency))
		
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
for item in fakelist:
	print "creating threads"
	aNotManager	=	NotificationManager(myCounter,notificationFreq,SQSZ)
	aNotManager.start()
	print "thread started"
	myCounter	=	myCounter+1
aNotManager.join()
