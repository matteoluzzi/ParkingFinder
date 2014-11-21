from threading import Thread

from boto.sqs.message import Message
import boto.sqs as sqs
from static import Zone as zn
from json import loads, dumps
from Queue import Queue

class DispatcherThread(Thread):

	def __init__(self, queue_name):
		
		Thread.__init__(self)
		self._subscribers = {}
		self._queues = {}
		self._sqs_conn = sqs.connect_to_region(zn.EU_W_1)
		self._queue = self._sqs_conn.get_queue(queue_name)
		if self._queue == None:
			self._queue = self._sqs_conn.create_queue(queue_name)
	
	def subscribe(self, requestID, maxsize):

		if not self._queues.has_key(requestID):
			self._queues[requestID] = Queue(maxsize=maxsize)

	def get_message_queue(self, requestID):

		if requestID in self._queues.keys():
			return self._queues[requestID]
		else:
			raise KeyError("coda non trovata")

	def delete_message_queue(self, requestID):
		if requestID in self._queues.keys():
			del self._queues[requestID]
		else:
			raise KeyError("coda non trovata")



	def run(self):

		print "Waiting on the response queue ", self._queue  
		while True:
			raw_messages = self._queue.get_messages(wait_time_seconds=20)



			for raw_message in raw_messages:

				print "Dispatcher - new message ", raw_message
				message = loads(raw_message.get_body())[0]

				r_id = message['r_id']
				current_subs = 0
				if r_id in self._queues.keys():
					queue = self._queues[r_id]
					print "queue max size ", queue.maxsize
					if not r_id in self._subscribers.keys():
						self._subscribers[r_id] = 1
						current_subs = 1
					else:
						current_subs = self._subscribers[r_id] + 1
						self._subscribers[r_id] = current_subs
					counter = queue.maxsize - current_subs
					print "--------------->current_subs=", current_subs, " counter=", counter

					if counter == 0: #ultimo subscribers
						print "Ultimo messaggio"
						message["last"] = True
					queue.put(message)

					self._queue.delete_message(raw_message)

				else:
					print "errore relativo alla richiesta " + r_id
					self._queue.delete_message(raw_message)
					#print "cancello messaggio spurio"






