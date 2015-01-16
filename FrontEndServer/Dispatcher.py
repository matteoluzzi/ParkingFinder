# coding=utf-8

from threading import Thread, Lock

from boto.sqs.message import Message
import boto.sqs as sqs
from json import loads, dumps

class DispatcherThread(Thread):

	def __init__(self, broker, queue_name, zone):		
		Thread.__init__(self)
		self._sqs_conn = sqs.connect_to_region(zone)
		self._queue = self._sqs_conn.get_queue(queue_name)
		self._broker = broker
		if self._queue == None:
			self._queue = self._sqs_conn.create_queue(queue_name)
		self._lock_overview = Lock()
		self._lock_detail = Lock()

		print "Inizialiazzazione completa"

	def copyMessage(self, msg):

		#logging.info("nella copyMessage")
		new_msg = {}
		for key in msg.keys():
			new_msg[key] = msg[key]
		return new_msg

	def run(self):
 
		while True:
			raw_messages = self._queue.get_messages(wait_time_seconds=20, num_messages=1)

			#logging.info("Rivevuti " + str(len(raw_messages)) + " messages")

			for raw_message in raw_messages:

				#logging.info("Nuovo messaggio " + str(raw_message.get_body()))
				message = loads(raw_message.get_body())[0]				
				
				r_id = message['r_id']
					
				#se il messaggio appartiene al server, processalo
				if self._broker.belongsTo(r_id):

					if message['type'] == "overview_response":
						q_id = message['quadrantID']	

						#scrivi il messaggio su tutte le code dove ci sono threads che lo hanno richiesto
						r_ids = self._broker.get_id_request(q_id)

						for r_id in r_ids:		
							#logging.info("prima della copyMessage")
							current_msg = self.copyMessage(message)
							#logging.info("Richiesta recuperata " + str(r_id) + " per il quadrante " + str(q_id))	
							self._lock_overview.acquire()
							if self._broker.add_subscriber(r_id):
								current_msg["last"] = True
								#logging.info("ultimo messaggio per " + r_id)
							self._lock_overview.release()
							try:
								queue = self._broker.get_message_queue(r_id)
								queue.put(current_msg)
							except:
								#logging.info("errore nel dispatcher, coda non trovata " + r_id)
								pass

						self._queue.delete_message(raw_message)

					else:
						self._lock_detail.acquire()
						if self._broker.add_subscriber(r_id):
								message["last"] = True
						self._lock_detail.release()
						queue = self._broker.get_message_queue(r_id)
						queue.put(message)
						self._queue.delete_message(raw_message)





