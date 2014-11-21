#!/usr/bin/env python
# coding=utf-8

import os, sys, time, json, itertools

from static import Zone as zn, ReqType as rt, Path as pt, Queue as qu

from boto.sqs.message import Message
import boto.sqs as sqs

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), './backend_server')))
from JSONManager import createOverviewRequest, createFullListRequest, createBoundedListRequest # @UnresolvedImport
import QuadrantTextFileLoader as loader # @UnresolvedImport
import SearchQuadrant as searcher # @UnresolvedImport

from multiprocessing.pool import Pool, ThreadPool
from Dispatcher import DispatcherThread

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.gen
import tornado.websocket
from tornado.options import define, options
define("port", default=8000, type=int)

tornado.options.parse_command_line(sys.argv)

class BaseHandler(tornado.web.RequestHandler):
	
	def get(self):
		self.render("map.html")
		
class MapHandler(tornado.websocket.WebSocketHandler):


	def initialize(self, sqs_conn, sqs_queues, q_list, thread, quadrantslist):

		self._sqs_conn = sqs_conn
		self._sqs_send_queues = sqs_queues
		self._quadrant_list = q_list
		self._dispatcher = thread
		self._quadrant_list_string = quadrantslist
		'''insieme di connessioni al server'''
		self._connections = set()

	def open(self):
		print "WebSocket opened!"
		self._connections.add(self)
		quadrant_list_msg = json.dumps({"type": "quadrant_list", "res" : -1, "data" : self._quadrant_list_string})
		self.write_message(quadrant_list_msg)

	@tornado.gen.engine
	def on_message(self, raw_message):

		print "received message"

		message = json.loads(raw_message)
		idReq = message['id']
		zoom_level = message['zoom_level']
		neLat = message['neLat']
		neLon = message['neLon']
		swLat = message['swLat']
		swLon = message['swLon']
		quadrants = message['quadrants']

		q_ids = set(map(lambda x: int(x),quadrants.split("|")))
		print q_ids

		#ad ogni richiesta instanzio un pool di thread per gestire le chiamate ad sqs
		pool = ThreadPool(len(q_ids))

		re_write = yield tornado.gen.Task(self.__write_background, self.__send_parking_spots_request, args=(idReq, zoom_level, q_ids, neLat, neLon, swLat, swLon), kwargs={'pool':pool})

		pool.close()

	def on_close(self):
		print "WebSocket closed!"
		self._connections.discard(self)
		
	
	def __write_background(self, func, callback, args=(), kwargs={}):
		'''funzione che lancia la scrittura sulle code'''
		
		def _callback(idReq):

			print "scritto messaggio, in attesa della risposta"

			queue = self._dispatcher.get_message_queue(idReq)
			print queue

			message = queue.get()
			print "message: " + repr(message)
			if message.has_key("last"):
				message.pop("last", None)
				self.write_message(message)
				print "ultimo messaggio"
				tornado.ioloop.IOLoop.instance().add_callback(lambda: callback(idReq))
				self._dispatcher.delete_message_queue(idReq)

				
			else:
				self.write_message(message)


			print "messaggio scritto al client"

		request = False

		sqs_queues_ids	= args[2]
		pool = kwargs['pool']		
		for id in sqs_queues_ids:
			if id in range(1,101):

				request = True
				pool.apply_async(func, args=(self._sqs_send_queues[id], id ,100, args[0], args[1], args[3], args[4], args[5], args[6]), callback=_callback)					
			
			else:
				#print "coda " + repr(id) + " non trovata"
				self.write_message(json.dumps({"type": "not found",  "quadrantID" : id, "percentage": -1}))

		if request == False:
			tornado.ioloop.IOLoop.instance().add_callback(lambda: callback(json.dumps("{res : -1}")))
			
				
	
		
	def __send_parking_spots_request(self, queue, q_id, pool_size, idReq, zoom_level, neLat, neLon, swLat, swLon):

		print "nella __send_parking_spots_request"
		 			
		if int(zoom_level) >= 17:
			req_type = rt.SPECIFIC + zoom_level
			data = self.__create_request_message(idReq, req_type, q_id, zoom_level, neLat, neLon, swLat, swLon)
		else:
			req_type = rt.GLOBAL
			data = self.__create_request_message(idReq, req_type, q_id , zoom_level=zoom_level)

		self._dispatcher.subscribe(idReq, pool_size)

		msg = Message()
		msg.set_body(data)	
		res = queue.write(msg)
		return idReq
	


	@staticmethod
	def __create_request_message(idReq, reqType, q_id, zoom_level=None, neLat=None, neLon=None, swLat=None, swLon=None):
		
		request = ""
		if reqType == rt.GLOBAL:
			request = createOverviewRequest(idReq, qu.RESPONSE_QUEUE, q_id)
			print request
		elif reqType == rt.SPECIFIC:
			request = createFullListRequest(idReq, qu.PREFIX + str(q_id), q_id)
		else:
			request = createBoundedListRequest(idReq, qu.PREFIX + str(q_id), q_id, (neLat, neLon), (swLat, swLon))
		
		return request	

def connect():	
	return sqs.connect_to_region(zn.EU_W_1)

def initialize(sqs_conn):
  	
	q_list = loader.QuadrantTextFileLoader.load(pt.QUADRANTSLISTPATH)
	sqs_queues = {}
	for i in range(1,10):
		curr_queues = sqs.get_all_queues(prefix = qu.PREFIX + str(i))  # @UndefinedVariable
		sqs_queues.update(preapareDict(curr_queues))

	dispatcher = DispatcherThread(qu.RESPONSE_QUEUE)
	dispatcher.start()

	quadrantslist = openQuadrantsList(pt.QUADRANTSLISTPATH)

		
	app = tornado.web.Application([(r'/', BaseHandler), (r'/map', MapHandler, dict(sqs_conn=sqs, sqs_queues=sqs_queues, q_list=q_list, thread=dispatcher, quadrantslist=quadrantslist))], template_path=os.path.join(os.path.dirname(__file__), "templates"), static_path=os.path.join(os.path.dirname(__file__), "static"), debug = True,)
	http_server = tornado.httpserver.HTTPServer(app)
	http_server.listen(options.port)
	print "ready to serve"
	tornado.ioloop.IOLoop.instance().start()


def openQuadrantsList(path):
	line = ""
	with open(path, 'r') as inp:
		line = inp.readlines()
	return "".join(line)

def preapareDict(queue_list):
	res = {}
	for queue in queue_list:
		key = int(queue.url[queue.url.rfind("_") +1:])
		res[key] = queue
	return res

if __name__ == "__main__":
	print "initializing..."
	sqs = connect()
	initialize(sqs)	



