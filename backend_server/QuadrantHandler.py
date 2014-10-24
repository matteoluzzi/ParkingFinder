import thread
import boto
import Settings
import boto.sqs
from boto.sqs.message import Message
import threading
import json
import ParkingDYDBLoader as DBloader

class QuadrantHandler(threading.Thread):
	__quadrant	=	0
	__mySettings	=	0
	__myLoader		=	0
	def __init__(self,myQuadrant,mySettingsArg,aLoader):
		threading.Thread.__init__(self)
		self.quadrant	=	myQuadrant
		self.mySettings	=	mySettingsArg
		self.myLoader	=	aLoader
		
	def run(self):
		conn = boto.sqs.connect_to_region(self.mySettings.settings['SQSzone'])
		queueName	=	"_SDCC_"+str(self.quadrant.getID())
		my_queue = conn.get_queue(queueName)
		print "pippo" + str(my_queue)
		while my_queue == None:
			print "creating SQS queue "+queueName
			my_queue = conn.create_queue(str(queueName))
			if my_queue==None:
				print "queue creation failed"
		print my_queue
		while 1:
			#print "Working"
			requests	=	my_queue.get_messages(wait_time_seconds=20)#tanto di default ne preleva solo 1
			print "queue "+str(queueName)+"pulled "+str(len(requests))+" messages"
			for item in requests:
				print "deleting "+str(item)
				text	=	item.get_body()
				my_queue.delete_message(item)
				myrequest =	json.loads(text)
				aQuadrantID	=	myrequest[0]["quadrant"]
				if int(aQuadrantID)!=int(self.quadrant.getID()):
					raise Exception("wrong quadrant request "+str(aQuadrantID)+" on "+str(self.quadrant.getID()))
				self.myLoader.batchUpdate(self.quadrant.getParkList())	#update status
				rtype	=	myrequest[0]["type"]
				if str(rtype)=="overview":
					print "percentuale parcheggi liberi "+str(self.quadrant.getPercentageFreeParkings())
					print "overview request"
				elif str(rtype)=="full_list":
					tempList	=	list()
					myParkList	=	self.quadrant.getParkList()
					for item in myParkList:
						tempList.append(item.getDictionary())
					jsonString	=	json.dumps(tempList)
					print "full list request"
					print jsonString
				elif str(rtype)=="bounded_list":
					tempList	=	list()
					maxlat		=	float(myrequest[0]["NWlat"])
					minlon		=	float(myrequest[0]["NWlon"])
					minlat		=	float(myrequest[0]["SElat"])
					maxlon		=	float(myrequest[0]["SElon"])
					myParkList	=	self.quadrant.getParkList()
					for item in myParkList:
						itemLat	=	float(item.getLatitude())
						itemLon	=	float(item.getLongitude())
						if((itemLat<=maxlat)and(itemLat>=minlat)and(itemLon>=minlon)and(itemLon<=maxlon)):
							tempList.append(item.getDictionary())
					jsonString	=	json.dumps(tempList)
					print jsonString
					print "bounded list request"
				else:
					raise Exception("Unknown type request")
				


