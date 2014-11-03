import thread
import boto
import Settings
import boto.sqs
from boto.sqs.message import Message
import threading
import json

class NotificationManager(threading.Thread):
	__myQuadrantID	=	0
	__frequency		=	0
	__queueName		=	0
	__mysqsZone		=	0
	def __init__(self,anId,freq,sqsZone):
		threading.Thread.__init__(self)
		self.myQuadrantID	=	anId
		self.frequency		=	freq	
		self.mysqsZone		=	sqsZone
	
	
	def run(self):
		print "Checking status notifications for the following quadrant"+str(self.myQuadrantID)
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
	aNotManager	=	NotificationManager(myCounter,notificationFreq,SQSZ)
	aNotManager.start()
	myConter	=	myCounter+1
aNotManager.join()
