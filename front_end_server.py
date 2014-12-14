#!/usr/bin/env python
# coding=utf-8

import os, sys, time, json, itertools, ConfigParser
from bcrypt import hashpw, gensalt

from boto.sqs.message import Message
import boto.sqs as sqs

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), './backend_server')))
from JSONManager import createOverviewRequest, createFullListRequest, createBoundedListRequest # @UnresolvedImport

from multiprocessing.pool import Pool, ThreadPool
from DispatcherBroker import DispatcherBroker

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.gen
import tornado.websocket
from tornado.escape import xhtml_escape, xhtml_unescape

class BaseHandler(tornado.web.RequestHandler):

	def initialize(self, front_end_address, port):

		self._address = front_end_address
		self._port = port
	
	def get(self):
		self.render("map.html", feAddress=self._address, fePort=self._port, signup=None)

class RegisterHandler(tornado.web.RequestHandler):

	def initialize(self, front_end_address, port):

		self._address = front_end_address
		self._port = port

	@tornado.web.asynchronous
	def post(self):

		username = xhtml_escape(self.get_argument("username"))
		email = xhtml_escape(self.get_argument("email"))
		password = xhtml_escape(self.get_argument("password"))
		conf_pass = xhtml_escape(self.get_argument("confirmPassword"))

		#Thread incaricato di gesitire la scrittura sul db
		pool = ThreadPool(processes=1)

	
		pool.apply_async(self.__checkDuplicates, args=(username, email, password), callback=self.__onfinish)

	def __checkDuplicates(self, username, email, password):

		signup = "Utente registrato con successo! Effettuare il login per accedere"

		#manca controllo su database del nome utente e password
		#se entrambi i controlli vanno a buon fine allora posso registrare l'utente sul db
		#setta error se c'è un errore

		encrypted_password = hashpw(password, gensalt())

		#salva le info sul db

		return (encrypted_password, signup)


	def __onfinish(self, args):

		print "entrypted password---------->" + args[0]
		self.render("map.html", feAddress=self._address, fePort=self._port, signup=args[1]) #nella render è presente self.finish()
		#self.redirect("/")

		
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

		re_write = yield tornado.gen.Task(self.__write_background, self.__send_parking_spots_request, args=(idReq, zoom_level, q_ids, neLat, neLon, swLat, swLon), kwargs={'pool':self._pool, 'settings':self._settings})


	def on_close(self):
		print "WebSocket closed!"
		self._connections.discard(self)
		
	
	def __write_background(self, func, callback, args=(), kwargs={}):
		'''funzione che lancia la scrittura sulle code'''
		
		# def _callback(idReq):


		# 	queue = self._dispatcher.get_message_queue(idReq)

		# 	print "waiting on ", queue
		# 	print queue

		# 	message = queue.get()
		# 	print "message: " + repr(message)
		# 	if message.has_key("last"):
		# 		message.pop("last", None)
		# 		self.write_message(message)
		# 		print "ultimo messaggio"
		# 		tornado.ioloop.IOLoop.instance().add_callback(lambda: callback(idReq))
		# 		self._dispatcher.delete_message_queue(idReq)

				
		# 	else:
		# 		self.write_message(message)


		# 	print "messaggio scritto al client"

		request = False

		sqs_queues_ids	= args[2]
		pool = kwargs['pool']
		settings = kwargs['settings']	

		for id in sqs_queues_ids:
			try:
				request = True
				pool.apply_async(func, args=(self._sqs_request_queue, id ,len(sqs_queues_ids), args[0], args[1], args[3], args[4], args[5], args[6], settings))					

			except KeyError:
				self.write_message(json.dumps({"type": "not found",  "quadrantID" : id, "percentage": -1}))			
		
	def __send_parking_spots_request(self, queue, q_id, req_size, idReq, zoom_level, neLat, neLon, swLat, swLon, settings):

		if int(zoom_level) >= 18:
			req_type = settings['specific_req_type']
			print req_type
			data = self.__create_request_message(settings, idReq, req_type, q_id, zoom_level=zoom_level, neLat=neLat, neLon=neLon, swLat=swLat, swLon=swLon)
		else:
			req_type = settings['global_req_type']
			data = self.__create_request_message(settings, idReq, req_type, q_id , zoom_level=zoom_level)

		self._dispatcher.subscribe(idReq, req_size)

		msg = Message()
		msg.set_body(data)	
		res = queue.write(msg)
		print "scritto messaggio ", res.get_body()
		
		queue = self._dispatcher.get_message_queue(idReq)

		print queue

		message = queue.get()
		print "message: " + repr(message)
		if message.has_key("last"):
			message.pop("last", None)
			self.write_message(message)
			print "ultimo messaggio"
			self._dispatcher.delete_queue(idReq)
			tornado.ioloop.IOLoop.instance().add_callback()			
		else:
			self.write_message(message)

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

	dispatcher = DispatcherBroker(int(settings['dispatcher_threads']), settings['response_queue'], settings['zone'])

	quadrantslist = openQuadrantsList(settings['quadrants_list_path'])

	pool = ThreadPool(int(settings['pool_size']))

		
	app = tornado.web.Application([(r'/', BaseHandler, dict(front_end_address=settings['front_end_address'], port=settings['port'])), 
		(r'/map', MapHandler, dict(sqs_conn=sqs, request_queue=request_queue, dispatcher=dispatcher, quadrantslist=quadrantslist, pool=pool, settings=settings)),
		(r'/register', RegisterHandler, dict(front_end_address=settings['front_end_address'], port=settings['port']))], 
		template_path=os.path.join(os.path.dirname(__file__), "templates"), static_path=os.path.join(os.path.dirname(__file__), "static"), debug = True,)
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



