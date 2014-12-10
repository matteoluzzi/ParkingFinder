#!/usr/bin/env python
# coding=utf-8

import os, sys, time, json, itertools, ConfigParser

from boto.sqs.message import Message
import boto.sqs as sqs

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), './backend_server')))
from JSONManager import createOverviewRequest, createFullListRequest, createBoundedListRequest # @UnresolvedImport

from multiprocessing.pool import Pool, ThreadPool
from Dispatcher import DispatcherThread

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.gen
import tornado.websocket

class BaseHandler(tornado.web.RequestHandler):

	def initialize(self, front_end_address, port):

		self._address = front_end_address
		self._port = port
	
	def get(self):
		self.render("map.html", feAddress=self._address, fePort=self._port)
		
class MapHandler(tornado.websocket.WebSocketHandler):


	def initialize(self, sqs_conn, request_queue, thread, quadrantslist, pool, settings):

		self._sqs_conn = sqs_conn
		self._sqs_request_queue = request_queue
		self._dispatcher = thread
		self._settings = settings
		self._quadrants_list = quadrantslist
		'''insieme di connessioni al server'''
		self._connections = set()
		self._pool = pool

	def open(self):
		print "WebSocket opened!"
		self._connections.add(self)
		quadrant_list_msg = json.dumps({"type": "quadrant_list", "data" : self._quadrants_list})
		self.write_message(quadrant_list_msg)

	@tornado.gen.engine
	def on_message(self, raw_message):


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
		#pool = ThreadPool(100)

		re_write = yield tornado.gen.Task(self.__write_background, self.__send_parking_spots_request, args=(idReq, zoom_level, q_ids, neLat, neLon, swLat, swLon), kwargs={'pool':self._pool, 'settings':self._settings})

		#pool.close()

	def on_close(self):
		print "WebSocket closed!"
		self._connections.discard(self)
		
	
	def __write_background(self, func, callback, args=(), kwargs={}):
		'''funzione che lancia la scrittura sulle code'''
		
		def _callback(idReq):


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
		settings = kwargs['settings']	

		for id in sqs_queues_ids:
			try:
				if id in range(1,51):

					request = True
					pool.apply_async(func, args=(self._sqs_request_queue, id ,50, args[0], args[1], args[3], args[4], args[5], args[6], settings), callback=_callback)					

			except KeyError:
				self.write_message(json.dumps({"type": "not found",  "quadrantID" : id, "percentage": -1}))

		if request == False:
			tornado.ioloop.IOLoop.instance().add_callback(lambda: callback(json.dumps("{res : -1}")))
			
				
	
		
	def __send_parking_spots_request(self, queue, q_id, pool_size, idReq, zoom_level, neLat, neLon, swLat, swLon, settings):
		 			
		print "nella sending ...."

		if int(zoom_level) >= 20:
			req_type = settings['specific_req_type'] + zoom_level
			data = self.__create_request_message(settings, idReq, req_type, q_id, zoom_level, neLat, neLon, swLat, swLon)
		else:
			req_type = settings['global_req_type']
			data = self.__create_request_message(settings, idReq, req_type, q_id , zoom_level=zoom_level)

		self._dispatcher.subscribe(idReq, pool_size)

		msg = Message()
		msg.set_body(data)	
		res = queue.write(msg)
		print "scritto messaggio ", res.get_body()
		return idReq
	


	@staticmethod
	def __create_request_message(settings, idReq, reqType, q_id, zoom_level=None, neLat=None, neLon=None, swLat=None, swLon=None):
		
		print "nella create...."

		request = ""
		if reqType == settings['global_req_type']:
			request = createOverviewRequest(idReq, settings['response_queue'], q_id)
		elif reqType == settings['specific_req_type']:
			request = createFullListRequest(idReq, settings['response_queue'], q_id)
		else:
			request = createBoundedListRequest(idReq, settings['response_queue'], q_id, (neLat, neLon), (swLat, swLon))
		
		return request	

def connect(zone):	
	return sqs.connect_to_region(zone)

def initialize(sqs_conn, settings):
  	
	sqs_queues = {}
	# for i in range(1,10):
	# 	curr_queues = sqs.get_all_queues(prefix = settings['prefix'] + str(i))  # @UndefinedVariable
	# 	sqs_queues.update(preapareDict(curr_queues))
	# print sqs_queues

	request_queue = sqs.get_queue(settings['request_queue'])

	print request_queue

	dispatcher = DispatcherThread(settings['response_queue'], settings['zone'])
	dispatcher.start()

	quadrantslist = openQuadrantsList(settings['quadrants_list_path'])

	pool = ThreadPool(int(settings['pool_size']))

		
	app = tornado.web.Application([(r'/', BaseHandler, dict(front_end_address=settings['front_end_address'], port=settings['port'])), (r'/map', MapHandler, dict(sqs_conn=sqs, request_queue=request_queue, thread=dispatcher, quadrantslist=quadrantslist, pool=pool, settings=settings))], template_path=os.path.join(os.path.dirname(__file__), "templates"), static_path=os.path.join(os.path.dirname(__file__), "static"), debug = True,)
	http_server = tornado.httpserver.HTTPServer(app)
	http_server.listen(settings['port'])
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

	config = ConfigParser.ConfigParser()
	config.read("FrontEndSettings.ini")
	settings = config.defaults()



	sqs = connect(settings['zone'])
	initialize(sqs, settings)	



