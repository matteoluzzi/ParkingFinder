#!/usr/bin/env python
# coding=utf-8

import os, sys, time, json, itertools, ConfigParser, re, functools
from Queue import Empty
from bcrypt import hashpw, gensalt

from boto.sqs.message import Message
import boto.sqs as sqs
from boto.dynamodb2.table import Table

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), './backend_server')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), './lib/futures')))
from JSONManager import createOverviewRequest, createFullListRequest, createBoundedListRequest, subscribeEmailNotification # @UnresolvedImport

from multiprocessing.pool import Pool, ThreadPool
from multiprocessing import Lock
from DispatcherBroker import DispatcherBroker

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.gen
import tornado.websocket
from tornado.escape import xhtml_escape, xhtml_unescape, json_encode, json_decode

subscribe_lock = Lock()


'''Handler generico dal quale ereditano tutti gli altri handlers che nesessitano di comunicare tramite cookies'''

class MyHandler(tornado.web.RequestHandler):

	def set_flash_message(self, key, message):
		self.set_secure_cookie('flash_msg_%s' % key, message)
	
	def get_flash_message(self, key):
		val = self.get_secure_cookie('flash_msg_%s' % key)
		self.clear_cookie('flash_msg_%s' % key)
		return val


'''Handler principale responsabile di renderizzare l'home page del sito'''

class BaseHandler(MyHandler):

	def initialize(self, front_end_address, port):

		self._address = front_end_address
		self._port = port
	
	def get(self):

		login_msg = self.get_flash_message("login_msg")
		register_msg = self.get_flash_message("register_msg")
		if login_msg != None:
			self.render("map.html", feAddress=self._address, fePort=self._port, signup=None, login=login_msg)
		elif register_msg != None:
			self.render("map.html", feAddress=self._address, fePort=self._port, signup=register_msg, login=None)
		else:
			self.render("map.html", feAddress=self._address, fePort=self._port, signup=None, login=None)

	def get_current_user(self):

		return self.get_secure_cookie("username")

'''Handler per gestire la registrazione di un utente al sito'''


class RegisterHandler(MyHandler):

	def initialize(self, front_end_address, port, table):

		self._address = front_end_address
		self._port = port
		self._table = table

	def get(self):

		self.redirect("/")

	@tornado.web.asynchronous
	def post(self):

		username = xhtml_escape(self.get_argument("username"))
		email = xhtml_escape(self.get_argument("email"))
		password = xhtml_escape(self.get_argument("password"))
		conf_pass = xhtml_escape(self.get_argument("confirmPassword"))

		#Thread incaricato di gesitire la scrittura sul db
		pool = ThreadPool(processes=1)
		pool.apply_async(self.__checkDuplicates, args=(username, email, password), callback=self.__onfinish)
		pool.close()

	def __checkDuplicates(self, username, email, password):

		signup = "Utente registrato con successo! Effettuare il login per accedere"
		try: #cerca eventuali duplicati
			duplicate = self._table.get_item(user_email=email)
			signup = "Email già registrata, scegline un altra o accedi"
			self.set_flash_message("register_msg", signup)
			return
		except: #non ci sono duplicati
			encrypted_password = hashpw(password, gensalt())
			self.set_flash_message("register_msg", signup)
			self._table.put_item(data={'user_email':email, 'user_username':username, 'user_password':encrypted_password})
			return

	def __onfinish(self, result):

		self.clear_cookie("_xsrf")

		self.redirect("/")


'''Handler per gestire il login di un utente, la sessione viene mantenuta tramite un cookie settato sul browser'''

class LoginHandler(MyHandler):

	def initialize(self, table):

		self._table = table

	def get(self):

		self.redirect("/")

	@tornado.web.asynchronous
	def post(self):

		email = xhtml_escape(self.get_argument("email"))
		password = xhtml_escape(self.get_argument("password"))

		pool = ThreadPool(processes=1)
		pool.apply_async(self.__checkLogin, args=(email, password), callback=self.__onfinish)
		pool.close()

	def __checkLogin(self, email, password):

		login_err = None
		try:
			user = self._table.get_item(user_email=email) #prendi l'utente salvato sul db
			passw = user.get('user_password')
			if hashpw(password, passw) == passw: #se le password coincidono autentica l'utente con un cookie
				self.set_secure_cookie("username", user.get('user_username'))
				self.set_secure_cookie("email", user.get('user_email'))
				self.set_flash_message("login_msg", "")
				return
			else:
				login_err = "Nome o password errati, riprovare"
				self.set_flash_message("login_msg", login_err)
				return
		except:
			login_err = "Nome o password errati, riprovare"
			self.set_flash_message("login_msg", login_err)
			return

	def __onfinish(self, result):

			self.clear_cookie("_xsrf")
			self.redirect("/")


'''Handler per la gestione del logout, cancella il cookie settato'''

class LogoutHandler(MyHandler):

	def get(self):

		self.clear_cookie("username")
		self.clear_cookie("email")
		self.clear_cookie("_xsrf")
		self.redirect("/")

	def post(self):

		self.redirect("/")


'''Handler per il processamento delle richieste di sottoscrizione ad uno o più quadranti'''

class QuadrantsSubscriptionHandler(MyHandler):

	def check_origin(self, origin):

		return True

	def initialize(self, subs_requests_queue):

		self.__subs_requests_queue = subs_requests_queue

	def get(self):

		self.redirect("/")

	@tornado.web.asynchronous
	def post(self):

		quadrants = self.get_arguments("quadrants")
		pool = ThreadPool(processes=1)
		pool.apply_async(self.__write_subscriptions, args=(quadrants, ), callback=self.__onfinish)
		pool.close

	def __write_subscriptions(self, quadrants):

		print quadrants
		quadrants = self.__validate_input(quadrants)
		print quadrants
		user_email = self.get_secure_cookie("email")
		for quadrant in quadrants:
			subscription = subscribeEmailNotification(quadrant, user_email)
			print subscription
			msg = Message()
			msg.set_body(subscription)
			self.__subs_requests_queue.write(msg)
		return

	def __validate_input(self, quadrants):

		return [int(q) for q in quadrants if re.match("^\d+$", q)]

	def __onfinish(self, result):

		self.write(json.dumps("success"))
		self.finish()


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


	def on_close(self):
		print "WebSocket closed!"
		self._connections.discard(self)
		
	
	def __write_background(self, func, args=(), kwargs={}):
		'''funzione che lancia la scrittura sulle code'''

		def on_write_complete(result):
			print "nella on_wrritecomeplet"
			ws_conn = result[0]
			idReq = result[1]
			writing_jobs_size = result[2]

			for i in range(0, writing_jobs_size):
			
				self._pool.apply_async(self.__retrive_and_write, args=(ws_conn, idReq))
				#self._pool.submit(self.__retrive_and_write, args=(ws_conn, idReq), kwargs=None)	
		
		quadrant_ids = args[2]
		pool = kwargs['pool']
		settings = kwargs['settings']
		self._dispatcher.subscribe(args[0], len(quadrant_ids))	
		# for id in quadrant_ids:
		# 	try:
		# 		pool.apply_async(func, args=(self._sqs_request_queue, id ,len(quadrant_ids), args[0], args[1], args[3], args[4], args[5], args[6], settings), callback=on_write_complete)					
	 # 		except:
	 # 			import traceback
		# 		print traceback.format_exc()
		try:
			pool.apply_async(func, args=(self._sqs_request_queue, quadrant_ids, args[0], args[1], args[3], args[4], args[5], args[6], settings), callback=on_write_complete)
		except:
	 		import traceback
		 	print traceback.format_exc()

		print "writing jobs submitted!!!!!!!!!!!"
		
	def __send_parking_spots_request(self, queue, q_ids, idReq, zoom_level, neLat, neLon, swLat, swLon, settings):

		for q_id in q_ids:

			print "nella sendparkign..."
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
			message = queue.get()

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
		
		print "nella create...."

		request = ""
		if reqType == settings['global_req_type']:
			request = createOverviewRequest(idReq, settings['response_queue'], q_id)
		elif reqType == settings['specific_req_type']:
			request = createFullListRequest(idReq, settings['response_queue'], q_id)
		else:
			request = createBoundedListRequest(idReq, settings['response_queue'], q_id, (neLat, neLon), (swLat, swLon))
		
		return request	


'''Funzioni accessorie per l'instaurazione della connessione con i servizi di amazon (sqs e dynamoDB) e per la configurazione dell'applicazione web'''

def connect(zone, table_name):	
	return sqs.connect_to_region(zone), Table(table_name)

def initialize(sqs_conn, user_table, settings):
  	
	sqs_queues = {}
	request_queue = sqs.get_queue(settings['request_queue'])
	notification_queue = sqs.get_queue(settings['notification_queue'])
	quadrantslist = openQuadrantsList(settings['quadrants_list_path'])
	dispatcher = DispatcherBroker(int(settings['dispatcher_threads']), settings['response_queue'], settings['zone'], len(quadrantslist))

	pool = ThreadPool(int(settings['pool_size']))
	#pool = ThreadPoolExecutor(max_workers=int(settings['pool_size']))

		
	app = tornado.web.Application([(r'/', BaseHandler, dict(front_end_address=settings['front_end_address'], port=settings['port'])), 
		(r'/map', MapHandler, dict(sqs_conn=sqs, request_queue=request_queue, dispatcher=dispatcher, quadrantslist=quadrantslist, pool=pool, settings=settings)),
		(r'/register', RegisterHandler, dict(front_end_address=settings['front_end_address'], port=settings['port'], table=user_table)),
		(r'/login', LoginHandler, dict(table=user_table)),
		(r'/logout', LogoutHandler),
		(r'/subsquadrants', QuadrantsSubscriptionHandler, dict(subs_requests_queue=notification_queue)),
		(r'/imgs/(.*)', tornado.web.StaticFileHandler, {'path': 'static/imgs'},)], 
		template_path=os.path.join(os.path.dirname(__file__), "templates"), static_path=os.path.join(os.path.dirname(__file__), "static"), debug = True,
		xsrf_cookies=True,
		cookie_secret="l/4VqtnPR3Wv08iW5cX9UR+t7Prkekxuq82yjZn5eDc=")

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

	sqs, dynamo_table = connect(settings['zone'], settings['user_table'])
	initialize(sqs, dynamo_table,  settings)	

