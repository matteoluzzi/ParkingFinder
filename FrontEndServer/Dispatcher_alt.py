# coding=utf-8

from threading import Thread, Lock
import logging

from boto.sqs.message import Message
import boto.sqs as sqs
from json import loads, dumps

from tornado.ioloop import IOLoop

#logging.basicConfig(filename='logging/Dispatcher.log',level=logging.INFO)

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
		self._handler = None
		self_messages_queue = None

		print "Inizialiazzazione completa"

	def setHandler(self, handler):
		self._handler = handler

	def setQueue(self, queue):
		self._messages_queue = queue

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

						#recupera le i codici di richiesta che necessitano di quel quadrante
						r_ids = self._broker.get_id_request(q_id)

						#logging.info("Richieste recuperate per il quadrante " + str(q_id) + " " + repr(r_ids))
						messages = []

						for r_id in r_ids:		
							#logging.info("prima della copyMessage")
							current_msg = self.copyMessage(message)
							#logging.info("Richiesta recuperata " + str(r_id) + " per il quadrante " + str(q_id))	
							#self._lock_overview.acquire()
							if self._broker.add_subscriber(r_id):
								current_msg["last"] = True
								#logging.info("ultimo messaggio per " + r_id)
							#self._lock_overview.release()
							current_msg['r_id'] = r_id
							if self._handler:
								print "aggiungo callback al client" + " curr_message" + repr(current_msg)
								try:
									copiedMessage = self.copyMessage(current_msg)
									messages.append(copiedMessage)
									self._messages_queue.put_nowait(copiedMessage)
									IOLoop.instance().add_callback(lambda: self._handler.write_message_to_client())
									print messages
								except:
									import traceback
			 						print traceback.format_exc()
							#current_msg = None
						#cancella il messaggio da sqs
						self._queue.delete_message(raw_message)

					else:
						#self._lock_detail.acquire()
						if self._broker.add_subscriber(r_id):
								message["last"] = True
						#self._lock_detail.release()
						if self._handler:
								print "aggiungo callback al client"
								IOLoop.instance().add_callback(lambda: self._handler.write_message_to_client(current_msg))
						self._queue.delete_message(raw_message)





