#!/usr/bin/env python
# coding=utf-8

from Queue import Empty
from multiprocessing.pool import Pool
import json, sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend_server')))
from JSONManager import createOverviewRequest, createFullListRequest

from boto.sqs.message import Message

import tornado.websocket
from tornado.escape import json_encode, json_decode


'''Handler per la gestione delle richieste riguardanti la mappa, lo scambio di messaggi req/resp avviene su una websocket'''

class MapHandler(tornado.websocket.WebSocketHandler):

	def initialize(self, sqs_conn, request_queue, dispatcher, quadrantslist, pool, settings):

		self._sqs_conn = sqs_conn
		self._sqs_request_queue = request_queue
		self._dispatcher = dispatcher
		self._settings = settings
		self._quadrants_list = quadrantslist
		'''insieme di connessioni al server'''
		self._connections = set()
		self._pool = pool

	def check_origin(self, origin):

		return True
		
	def open(self):
		print "WebSocket opened!"
		self._connections.add(self)
		quadrant_list_msg = json.dumps({"type": "quadrant_list", "data" : self._quadrants_list})
		self.write_message(quadrant_list_msg)

	def on_message(self, raw_message):
		message = json.loads(raw_message)

		msg_type = message["type"]
		
		if msg_type == "normal":

			idReq = message['id']
			zoom_level = message['zoom_level']
			neLat = message['neLat']
			neLon = message['neLon']
			swLat = message['swLat']
			swLon = message['swLon']
			quadrants = message['quadrants']

			q_ids = set(map(lambda x: int(x),quadrants.split("|")))
			print q_ids

			self.__write_background(self.__send_parking_spots_request, args=(idReq, zoom_level, q_ids, neLat, neLon, swLat, swLon), kwargs={'pool':self._pool, 'settings':self._settings})

		else: #messaggio di heartbeat
			pass

	def on_close(self):
		print "WebSocket closed!"
		self._connections.discard(self)
		
	
	def __write_background(self, func, args=(), kwargs={}):
		'''funzione che lancia la scrittura sulle code'''

		def on_write_complete(result):
			ws_conn = result[0]
			idReq = result[1]
			writing_jobs_size = result[2]

			for i in range(0, writing_jobs_size):
			
				self._pool.apply_async(self.__retrive_and_write, args=(ws_conn, idReq))
		
		quadrant_ids = args[2]
		pool = kwargs['pool']
		settings = kwargs['settings']
		self._dispatcher.subscribe(args[0], len(quadrant_ids))	
		try:
			pool.apply_async(func, args=(self._sqs_request_queue, quadrant_ids, args[0], args[1], args[3], args[4], args[5], args[6], settings), callback=on_write_complete)
		except:
	 		import traceback
		 	print traceback.format_exc()

		print "writing jobs submitted!!!!!!!!!!!"
		
	def __send_parking_spots_request(self, queue, q_ids, idReq, zoom_level, neLat, neLon, swLat, swLon, settings):

		for q_id in q_ids:

			if int(zoom_level) >= 18:
				req_type = settings['specific_req_type']
				print req_type
				data = self.__create_request_message(settings, idReq, req_type, q_id, zoom_level=zoom_level, neLat=neLat, neLon=neLon, swLat=swLat, swLon=swLon)
				msg = Message()
				msg.set_body(data)	
				res = queue.write(msg)
				print "scritto messaggio ", res.get_body()
			else:
				if self._dispatcher.create_quadrant_request(q_id, idReq) == True: #scrivo il messaggio su sqs solo se nessun altro lo ha già fatto
					req_type = settings['global_req_type']
					data = self.__create_request_message(settings, idReq, req_type, q_id , zoom_level=zoom_level)
					msg = Message()
					msg.set_body(data)	
					res = queue.write(msg)
					print "scritto messaggio ", res.get_body()

		return (self.ws_connection, idReq, len(q_ids))

	def __retrive_and_write(self, ws_conn, idReq):

		queue = self._dispatcher.get_message_queue(idReq)			

		try:
			message = queue.get(timeout=30)

			#print "message: " + repr(message)
			message['r_id'] = idReq
			if message.has_key("last"):
				message.pop("last", None)
				if isinstance(message, dict):
					message = tornado.escape.json_encode(message)
				if ws_conn:
					ws_conn.write_message(message)
				print "ultimo messaggio, cancello la coda per " + idReq
				self._dispatcher.delete_queue(idReq)	
			else:
				if isinstance(message, dict):
					message = tornado.escape.json_encode(message)
				if ws_conn:
					ws_conn.write_message(message)
				print "scritto messaggio al client ", idReq
		except Empty:
			self._pool.apply_async(self.__retrive_and_write, args=(ws_conn, idReq))
			print "nessun messaggio entro il timeout"
		except:
			import traceback
			print traceback.format_exc()
		
	@staticmethod
	def __create_request_message(settings, idReq, reqType, q_id, zoom_level=None, neLat=None, neLon=None, swLat=None, swLon=None):

		request = ""
		if reqType == settings['global_req_type']:
			request = createOverviewRequest(idReq, settings['response_queue'], q_id)
		elif reqType == settings['specific_req_type']:
			request = createFullListRequest(idReq, settings['response_queue'], q_id)
		else:
			request = createBoundedListRequest(idReq, settings['response_queue'], q_id, (neLat, neLon), (swLat, swLon))
		
		return request	