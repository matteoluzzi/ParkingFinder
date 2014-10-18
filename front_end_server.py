#!/usr/bin/env python

import os, sys, time, json, uuid

from static import Zone as zn, Queue as qe, ReqType as rt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), './lib/botornado')))
import botornado.sqs
from boto.sqs.message import Message

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.gen
from tornado.options import define, options
define("port", default=8080, type=int)

tornado.options.parse_command_line(sys.argv)

class BaseHandler(tornado.web.RequestHandler):
	
	def get(self):
		self.render("map.html")
		
class MapHandler(tornado.web.RequestHandler):


	def initialize(self, sqs_conn, sqs_queue):

		self._sqs_conn = sqs_conn
		self._sqs_send_queue = sqs_queue
	
	@tornado.gen.coroutine
	def post(self):
		start_time = time.time()
		id = self.get_argument('id')
		zoom_level = self.get_argument('zoom_level')
		neLat = self.get_argument('neLat')
		neLon = self.get_argument('neLon')
		swLat = self.get_argument('swLat')
		swLon = self.get_argument('swLon')
		
		req_type = ""
		data = {}
		if int(zoom_level) >= 15:
			req_type = rt.SPECIFIC + zoom_level
			data = self._create_request_message(id, req_type, zoom_level, neLat, neLon, swLat, swLon)
		else:
			req_type = rt.GLOBAL
			data = self._create_request_message(id, req_type, zoom_level=zoom_level)
		print data
		
		#scruttura sulla coda di sqs in maniera asincrona		
		res = yield self._send_parking_spots_request(data)
		write_time = time.time() - start_time  
		print "done writing ", write_time
		
 		ret = yield self._retrieve_parking_spots(data)
 		read_time = time.time() - write_time - start_time	 
 		print "done reading & deleting", read_time
 		self.write(json.dumps(ret['positions']))
		
# 		yield self._delete_messages(ret['response'])
# 		delete_time = time.time() - read_time - start_time
# 		print "done deleting ", delete_time
		
		#chiusura connessione ad operazioni terminate
		self.finish()
		
	@tornado.gen.coroutine
	def _send_parking_spots_request(self, data, callback=None):
		msg = Message()
		msg.set_body(json.dumps(data))
		res = yield tornado.gen.Task(self._sqs_send_queue.write, msg)
		raise tornado.gen.Return(res)
	
	@tornado.gen.coroutine	
	def _retrieve_parking_spots(self, data, callback=None):
				
		response = yield tornado.gen.Task(self._sqs_send_queue.get_messages, num_messages=1)	
		positions = []
		if len(response) > 0:
			for msg in response:
				positions.append(json.loads(msg.get_body()))
				yield tornado.gen.Task(self._sqs_send_queue.delete_message, msg)
			ret = {"positions" : positions, "response" : response}
			raise tornado.gen.Return(ret)
		else:
			raise tornado.gen.Return(-1)
	
		
		
	@tornado.gen.coroutine
	def _delete_messages(self, messages, callback=None):
		
		for msg in messages:
			res = yield tornado.gen.Task(self._sqs_send_queue.delete_message, msg)
		return	

	@staticmethod
	def _create_request_message(id, reqType, zoom_level=None, neLat=None, neLon=None, swLat=None, swLon=None):
		return {"id":id, "zoom":zoom_level, "neLat":neLat, "neLon":neLon, "swLat":swLat, "seLon":swLon, "reqType":reqType}
	

def connect():	
	return botornado.sqs.connect_to_region(zn.ZONE_2)

def get_queue(name, sqs_conn):
  def cb(response):
  	queue = response
  	app = tornado.web.Application([(r'/', BaseHandler), (r'/map', MapHandler, dict(sqs_conn=sqs, sqs_queue=queue))], template_path=os.path.join(os.path.dirname(__file__), "templates"), static_path=os.path.join(os.path.dirname(__file__), "static"), debug = True,)
  	http_server = tornado.httpserver.HTTPServer(app)
  	http_server.listen(options.port)

  sqs_queue = sqs.get_queue(name, callback=cb)




if __name__ == "__main__":
	
	ioloop = tornado.ioloop.IOLoop.instance()
	sqs = connect()
	ioloop.add_timeout(time.time(), get_queue(qe.FRONT_END_QUEUE, sqs))
	ioloop.start()



