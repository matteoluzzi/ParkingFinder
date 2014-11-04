#!/usr/bin/env python

import os, sys, time, json, itertools

from static import Zone as zn, ReqType as rt

from boto.sqs.message import Message
import boto.sqs as sqs

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), './backend_server')))
from JSONManager import createOverviewRequest, createFullListRequest, createBoundedListRequest # @UnresolvedImport
import QuadrantTextFileLoader as loader # @UnresolvedImport
import SearchQuadrant as searcher # @UnresolvedImport

from multiprocessing.pool import ThreadPool

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


	def initialize(self, sqs_conn, sqs_queues, q_list):

		self._sqs_conn = sqs_conn
		self._sqs_send_queues = sqs_queues
		self._quadrant_list = q_list
#		print self._quadrant_list
	
	@tornado.web.asynchronous
	@tornado.gen.engine
	def post(self):
		
		start_time = time.time()
		idReq = self.get_argument('id')
		zoom_level = self.get_argument('zoom_level')
		neLat = self.get_argument('neLat')
		neLon = self.get_argument('neLon')
		swLat = self.get_argument('swLat')
		swLon = self.get_argument('swLon')
		centerLat = self.get_argument("centerlat")
		centerLng = self.get_argument("centerlng")
		
		quadrantSearcher = searcher.SearchQuadrant(self._quadrant_list)
		center = (float(centerLat), float(centerLng))
		#q_id = quadrantSearcher.searchQuadrant(center)
		q_list = quadrantSearcher.getQuadrantsForAnArea((neLat, swLon), (neLat, neLon), (swLat, swLon), (swLat, neLon))
		#q_ids = itertools.chain(map(lambda x: x.getID(), q_list))
		q_ids = map(lambda x: x.getID(), q_list)
		res = []
		#q_ids = q_ids[:2]	
		print q_ids
		
		#ad ogni richiesta instanzio un pool di thread per gestire le chiamate ad sqs
		pool = ThreadPool(len(q_ids))
		start_time = time.time()
		re_write = yield tornado.gen.Task(self.__write_background, self.__send_parking_spots_request, args=(idReq, zoom_level, q_ids, neLat, neLon, swLat, swLon), kwargs={'pool':pool})
		write_time = time.time() -start_time
		#scruttura sulla coda di sqs in maniera asincrona		
 		re_read = yield tornado.gen.Task(self.__read_and_delete_background, self.__retrieve_parking_spots, args=(q_ids, ), kwargs={'pool':pool})
 		read_time = time.time() - write_time - start_time
 		
 		print re_read
 		json_response = json.dumps(re_read)
 		self.write(json_response)
 		
		pool.close()
 		
		#chiusura connessione ad operazioni terminate
		self.finish()
	
	def __write_background(self, func, callback, args=(), kwargs={}):
		
		def _callback(result):
			tornado.ioloop.IOLoop.instance().add_callback(lambda: callback(result))
		
		sqs_queues_ids	= args[2]
		pool = kwargs['pool']		
		queues = []
		for id in sqs_queues_ids:
			queues.append((id, self._sqs_send_queues[id]))
			
		arguments = [(queue, id, args[0], args[1], args[3], args[4], args[5], args[6]) for id, queue in queues]
		pool.map_async(func, arguments, callback=_callback)
	
		
	def __send_parking_spots_request(self, args):
		
		queue = args[0]
		q_id = args[1]
		idReq = args[2]
		zoom_level = args[3]
		neLat = args[4]
		neLon = args[5]
		swLat = args[6]
		swLon = args[7]
		 			
		if int(zoom_level) >= 17:
			req_type = rt.SPECIFIC + zoom_level
			data = self.__create_request_message(idReq, req_type, q_id, zoom_level, neLat, neLon, swLat, swLon)
		else:
			req_type = rt.GLOBAL
			data = self.__create_request_message(idReq, req_type, q_id , zoom_level=zoom_level)

		msg = Message()
		msg.set_body(data)	
		res = queue.write(msg)
		return res
	
	def __read_and_delete_background(self,  func, callback, args=(), kwargs={}):
		
		def _callback(result):
			tornado.ioloop.IOLoop.instance().add_callback(lambda: callback(result))
			
		sqs_queues_ids	= args[0]
		pool = kwargs['pool']
		
		queues = []
		for id in sqs_queues_ids:
			queues.append(self._sqs_send_queues[id])		
			
		pool.map_async(func, queues, callback=_callback)

		

	def __retrieve_parking_spots(self, queue):			
		
		response_read = queue.get_messages(num_messages=1)
				
		if len(response_read) == 1:
			for msg in response_read:				
				msg_body = json.loads(msg.get_body())

				response_delete = queue.delete_message(msg)
								
			return msg_body
				
		else:
			print "lettura non riuscita sulla coda " + repr(queue)	
			return -1	


	@staticmethod
	def __create_request_message(idReq, reqType, q_id, zoom_level=None, neLat=None, neLon=None, swLat=None, swLon=None):
		
		request = ""
		if reqType == rt.GLOBAL:
			request = createOverviewRequest(idReq, "_SDCC_" + str(q_id), q_id)
		elif reqType == rt.SPECIFIC:
			request = createFullListRequest(idReq, "_SDCC_" + str(q_id), q_id)
		else:
			request = createBoundedListRequest(idReq, "_SDCC_" + str(q_id), q_id, (neLat, neLon), (swLat, swLon))
		
		return request	

def connect():	
	return sqs.connect_to_region(zn.ZONE_2, aws_access_key_id = "AKIAITUR2OQ2ZQA3ODQQ", aws_secret_access_key = "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")

def initialize(sqs_conn):
  	
	q_list = loader.QuadrantTextFileLoader.load("backend_server/listaquadranti.txt")
	sqs_queues = {}
	for i in range(1,10):
		curr_queues = sqs.get_all_queues(prefix = "_SDCC_" + str(i))  # @UndefinedVariable
		sqs_queues.update(preapareDict(curr_queues))
	app = tornado.web.Application([(r'/', BaseHandler), (r'/map', MapHandler, dict(sqs_conn=sqs, sqs_queues=sqs_queues, q_list=q_list))], template_path=os.path.join(os.path.dirname(__file__), "templates"), static_path=os.path.join(os.path.dirname(__file__), "static"), debug = True,)
	http_server = tornado.httpserver.HTTPServer(app)
	http_server.listen(options.port)
	tornado.ioloop.IOLoop.instance().start()


def preapareDict(queue_list):
	res = {}
	for queue in queue_list:
		key = int(queue.url[queue.url.rfind("_") +1:])
		res[key] = queue
	return res

if __name__ == "__main__":

	sqs = connect()
	initialize(sqs)
	



