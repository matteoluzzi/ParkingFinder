import thread
import boto
import Settings
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
		self.mysqsZone		=	(str)sqsZone
	
	
	def run(self):
		prevStatus	=	0
		conn = boto.sqs.connect_to_region(self.mySettings.settings[self.mysqsZone])
		queueName	=	"_SDCC_NOTIFICATION"+str(self.quadrant.getID())
		my_queue = conn.get_queue(queueName)
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
			print "destination queue"+str(dest_queue)
			m = Message()
			m.set_body(str(JsonRequest))
			dest_queue.write(m)
			sleep(frequency)
		
settingsHandler		=	settings.Settings("testimp.txt")
try:
	myQuadrantsRangeStart	= 	settingsHandler.settings['rangeStart']	
	myQuadrantsRangeEnd		=	settingsHandler.settings['rangeEnd']		
	notificationFreq		=	settingsHandler.settings['notificationFreq']
	SQSZ					=	settingsHandler.settings['SQSzone']
except:
	print "error while loading settings"
	return
	
st			=	int(myQuadrantsRangeStart)
end			=	int(myQuadrantsRangeEnd)
myCounter	=	st
fakelist	=	range(end-st)
for item in fakelist:
	print "creating threads"
	aNotManager	=	NotificationManager(myCounter,notificationFreq,SQSZ)
	aNotManager.start()
	myConter	=	myCounter+1
aNotManager.join()
