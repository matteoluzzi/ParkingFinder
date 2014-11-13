import thread
import boto
import Settings
import boto.sqs
from boto.sqs.message import Message
import threading
import json
import ParkingDYDBLoader as DBloader
import JSONManager as jm
from boto.sqs.message import Message

#backend server of a quadrant, makes an endless cycle: fetch request, select the right method for the kind of
#request and send back an answer on a queue

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
		print "connecting to "+str(self.mySettings.settings['SQSzone'])+"region"
		conn = boto.sqs.connect_to_region(self.mySettings.settings['SQSzone'][:-1])
		queueName	=	"_APPosto_SDCC_"+str(self.quadrant.getID())
		print queueName
		my_queue = conn.get_queue(queueName)
		#print "pippo" + str(my_queue)
		while my_queue == None:
			#print "creating SQS queue "+queueName
			my_queue = conn.create_queue(str(queueName))
			if my_queue==None:
				print "queue creation failed"
		print my_queue
		while 1:
			#print "Working"
			requests	=	my_queue.get_messages(wait_time_seconds=20)#tanto di default ne preleva solo 1
			print "queue "+str(queueName)+"pulled "+str(len(requests))+" messages"
			myResponse 	=	""
			for item in requests:
				print "deleting "+str(item)
				text	=	item.get_body()
				my_queue.delete_message(item)
				myrequest =	json.loads(text)
				aQuadrantID		=	myrequest[0]["quadrant"]
				requestID		=	myrequest[0]["r_id"]
				responseQueue	=	myrequest[0]["resp_queue"]
				if int(aQuadrantID)!=int(self.quadrant.getID()):
					raise Exception("wrong quadrant request "+str(aQuadrantID)+" on "+str(self.quadrant.getID()))
				self.myLoader.batchUpdate(self.quadrant.getParkList())	#update status
				rtype	=	myrequest[0]["type"]
				if str(rtype)=="overview":
					freePercentage	=	int(self.quadrant.getPercentageFreeParkings())
					print "percentuale parcheggi liberi "+str(freePercentage)+" richiesta id "+str(requestID)
					print "Serving an overview request"
					myResponse	=	jm.createOverviewResponse(requestID,freePercentage,self.quadrant.getID())
					print "Overview JSON response "+str(myResponse)
				elif str(rtype)=="full_list":
					tempList	=	list()
					myParkList	=	self.quadrant.getParkList()
					print "full list request"
					myResponse	=	jm.createListResponse(requestID,myParkList)
					print "full list JSON response"+str(myResponse)
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
							tempList.append(item)
					print "bounded list request"
					myResponse	=	jm.createListResponse(requestID,tempList)
					print "bounded list JSON response"+str(myResponse)
				else:
					raise Exception("Unknown type request")
				#CODICE DA TESTARE!!! (dovrebbe funzionare
				if myResponse:
					my_resp_queue = conn.get_queue(str(responseQueue))
					print "Response queue" + str(my_queue)
					while not my_resp_queue:
						#print "creating SQS queue "+queueName
						my_resp_queue = conn.create_queue(str(responseQueue))
					if my_resp_queue==None:
						print "queue creation failed"
					m = Message()
					m.set_body(str(myResponse))
					my_resp_queue.write(m)
				else:
					print "QuadrantHandler.py: error on request processing"
				


