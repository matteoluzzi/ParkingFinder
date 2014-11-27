import ParkingDYDBLoader as DBloader
import QuadrantHandler as qh
import SearchQuadrant as searchquadrant
import QuadrantTextFileLoader as loader
import Settings as settings
import threading
import traceback
import JSONManager as jm
import boto
from boto.sqs.message import Message
import json

imp				=	settings.Settings("testimp.txt")
print "connecting to "+str(imp.settings['SQSzone'])+"region"
conn = boto.sqs.connect_to_region(imp.settings['SQSzone'][:-1])
queueName	=	"testqueue"
print queueName
my_queue = conn.get_queue(queueName)
#print "pippo" + str(my_queue)
while my_queue == None:
	#print "creating SQS queue "+queueName
	my_queue = conn.create_queue(str(queueName))
	if my_queue==None:
		print "queue creation failed"
	print my_queue
testrequest	=	jm.createFullListRequest(15,queueName,1)

myfakelist = range(1500)
contat = 1
for item in myfakelist:
		try:
			destinationQueueName	=	"_SDCC_"+str(contat)
			contat	=	contat	+	1
			dest_queue = conn.get_queue(destinationQueueName)
			dest_queue.delete()
		except:
			print "errore"
return
		
destinationQueueName	=	"_SDCC_"+str(1)
dest_queue = conn.get_queue(destinationQueueName)
while dest_queue == None:
	dest_queue = conn.create_queue(str(destinationQueueName))
	if dest_queue==None:
		print "queue creation failed"
print "destination queue "+str(dest_queue)
m = Message()
m.set_body(str(testrequest))
dest_queue.write(m)
print testrequest
print "message sent on "+str(dest_queue)
receivedAnswer	= False
while not receivedAnswer:
	requests	=	my_queue.get_messages(wait_time_seconds=20)#tanto di default ne preleva solo 1
	print "queue "+str(queueName)+"pulled "+str(len(requests))+" messages"
	for item in requests:
		text		=	item.get_body()
		print text
		response	=	json.loads(text)
		response_id	=	response[0]
		print response[0]
		print response[0]["r_id"]
		responseID	=	int(response[0]["r_id"])
		if responseID==1:
			my_queue.delete_message(item)
			print "fetched response "+str(response_id)
			receivedAnswer	=	True
		print "finito"

