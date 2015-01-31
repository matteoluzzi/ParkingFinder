#!/usr/bin/env python
# coding=utf-8

from Queue import Empty, Queue
from multiprocessing.pool import Pool
from threading import RLock
import json, sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend_server')))
from JSONManager import createOverviewRequest, createFullListRequest

from boto.sqs.message import Message

import tornado.websocket
from tornado.escape import json_encode, json_decode
from tornado.ioloop import IOLoop

connections = dict()
ws = dict()
messages_queue = Queue()

'''Handler per la gestione delle richieste riguardanti la mappa, lo scambio di messaggi req/resp avviene su una websocket'''

class MapHandler(tornado.websocket.WebSocketHandler):

	def initialize(self, request_queue, dispatcher, quadrantslist, pool, settings):

		self._sqs_request_queue = request_queue
		self._broker = dispatcher
		self._settings = settings
		self._quadrants_list = quadrantslist
		self._pool = pool
		self._broker.setComponents(self, messages_queue)

	def check_origin(self, origin):

		return True
		
	def open(self):
		print "WebSocket opened!"
		ws[self] = set()
		quadrant_list_msg = json.dumps({"type": "quadrant_list", "data" : self._quadrants_list})
		self.write_message(quadrant_list_msg)

	def on_message(self, raw_message):
		message = json.loads(raw_message)
		print ws, connections

		msg_type = message["type"]
		
		if msg_type == "normal":

			idReq = message['id']
			zoom_level = message['zoom_level']
			neLat = message['neLat']
			neLon = message['neLon']
			swLat = message['swLat']
			swLon = message['swLon']
			quadrants = message['quadrants']

			connections[idReq] = self.ws_connection
			ws[self].add(idReq)
			#print "aggiunta connessione a " + repr(connections)

			q_ids = set(map(lambda x: int(x),quadrants.split("|")))
			print q_ids

			self._broker.subscribe(idReq, len(q_ids))

			try:
				self._pool.apply_async(self.__send_parking_spots_request, args=(self._sqs_request_queue, q_ids, idReq, zoom_level, neLat, neLon, swLat, swLon, self._settings), callback=None)
			except:
		 		import traceback
			 	print traceback.format_exc()

			print "writing jobs submitted!!!!!!!!!!!"
			
		else: #messaggio di heartbeat
			pass

	def on_close(self):

		for idReq in ws[self]:
			try:	
				del connections[idReq]
			except KeyError:
				pass
		
		del ws[self]
		print "WebSocket closed!"
		print connections, ws

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
				if self._broker.create_quadrant_request(q_id, idReq) == True: #scrivo il messaggio su sqs solo se nessun altro lo ha già fatto
					req_type = settings['global_req_type']
					data = self.__create_request_message(settings, idReq, req_type, q_id , zoom_level=zoom_level)
					msg = Message()
					msg.set_body(data)	
					res = queue.write(msg)
					print "scritto messaggio ", res.get_body()
		return 

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


	def write_message_to_client(self):

		try:
		 	message = messages_queue.get_nowait()

			idReq = message['r_id']

			try:
				ws_conn = connections[idReq]
				if isinstance(message, dict):
					message = tornado.escape.json_encode(message)
				if ws_conn:
					#print "scrivo " + message + " al client su " + repr(ws_conn)
					ws_conn.write_message(message)
				if "last" in message:
					del connections[idReq]
			except KeyError: #il client ha chiuso la pagina con messaggi in processamento
				pass
			del message

		except Empty:
			pass

	

