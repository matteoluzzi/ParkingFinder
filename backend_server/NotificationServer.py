import Settings as settings
import Quadrant as quad
import boto.sns
import boto.sqs
import threading
import json

class NotificationServer(threading.Thread):
	snsConnection		=	0
	nQuadrants		=	0
	topics			=	{}
	snsRegion		=	0
	settingsHandler	=	0
	def __init__(self):	
		threading.Thread.__init__(self)
		self.settingsHandler		=	settings.Settings("testimp.txt")
		myRegion			=	str(self.settingsHandler.settings['awsRegion'])
		myRegion			=	myRegion[:-1] #mistero... backspace in fondo a stringa
		self.snsRegion		=	myRegion
		self.snsConnection		=	boto.sns.connect_to_region(myRegion)
		self.nQuadrants			=	str(self.settingsHandler.settings['nQuadrants'])
		fakelist	=	range(int(self.nQuadrants))
		counter 	=	1
		for item in fakelist:
			myTopic	=	self.snsConnection.create_topic("quadrant_"+str(counter))['CreateTopicResponse']['CreateTopicResult']['TopicArn']
			if myTopic:
				self.topics[str(counter)] 	=	myTopic
			counter	=	counter	+	1
			
	def run(self):
		print "inizio thread"
		conn = boto.sqs.connect_to_region(self.snsRegion)
		queueName	=	"notificationQueue"
		my_queue = conn.get_queue(queueName)
		print "pippo" + str(my_queue)
		while my_queue == None:
			print "creating SQS queue "+queueName
			my_queue = conn.create_queue(str(queueName))
			if my_queue==None:
				print "queue creation failed"
		print my_queue
		while 1:
			print "Working"
			requests	=	my_queue.get_messages(wait_time_seconds=20)#tanto di default ne preleva solo 1
			print "queue "+str(queueName)+"pulled "+str(len(requests))+" messages"
			for item in requests:
				print "deleting "+str(item)
				text	=	item.get_body()
				my_queue.delete_message(item)
				myRequest =	json.loads(text)
				aquadrantID	=	myRequest['quadrantID']
				requestType	=	myRequest['type']
				if requestType=="sendNotification":
					subj	=	myRequest['subject']
					mess	=	myRequest['messageBody']
					self.sendANotification(aquadrantID,subj,mess)
				elif requestType=="emailSubscribe":
					addr	=	myRequest['address']
					self.mailSubscribe(aquadrantID,addr)
					
	def sendANotification(self,quadrantID,aSubject,messageBody):
		topicarn	=	self.topics[str(quadrantID)]
		if topicarn:
			publication	=	self.snsConnection.publish(topic=topicarn,subject=aSubject,message=messageBody)
			if not publication:
				"error while sending notification"
		else: 
			print "sns queue not found"
				
	def mailSubscribe(self,quadrantID,address):
		mytopic	=	self.topics[str(quadrantID)]
		if not mytopic:
			print "topic not found"
			return
		#print mytopic
		self.snsConnection.subscribe(mytopic,"email",address)
		
testmio	=	NotificationServer()
testmio.start()
#testq	=	quad.Quadrant(25,0,0,0,0)
#testmio.mailSubscribe(testq.getID(),"paride.casulli@gmail.com")
	
		

