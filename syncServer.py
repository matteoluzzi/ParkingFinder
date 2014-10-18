import tornado.web
import tornado.ioloop
import tornado.httpserver
import tornado.options
import os, json, time
from tornado import gen

from static import Zone as zn, Queue as qe

import boto.sqs
from boto.sqs.message import Message


from tornado.options import define, options
define("port", default=8080, type=int)


class BaseHandler(tornado.web.RequestHandler):

	def get(response):
		response.render("map.html")

	

class MapHandler(tornado.web.RequestHandler):


	def initialize(self, sqs_conn, sqs_queue):

		self._sqs_conn = sqs_conn
		self._sqs_send_queue = sqs_queue


	def post(self):

		zoom_level = self.get_argument('zoom_level')
		neLat = self.get_argument('neLat')
		neLon = self.get_argument('neLon')
		swLat = self.get_argument('swLat')
		swLon = self.get_argument('swLon')
		data = self._create_request_message(zoom_level, neLat, neLon, swLat, swLon)

		self._send_parking_spots_request(data)

		response = self._retrieve_parking_spots(data)
		print "------> response ,", json.dumps(response)
		self.write(json.dumps(response))

	


	def _send_parking_spots_request(self, data):

		msg = Message()
		msg.set_body(json.dumps(data))
		self._sqs_send_queue.write(msg)
	
	@staticmethod
	def _create_request_message(zoom_level, neLat, neLon, swLat, swLon):
		return {"zoom":zoom_level, "neLat":neLat, "neLon":neLon, "swLat":swLat, "seLon":swLon}



	def _retrieve_parking_spots(self, data):
		positions = []
		rs = self._sqs_send_queue.get_messages(num_messages=1, wait_time_seconds=10)
		if len(rs) > 0:
			for msg in rs:
				positions.append(json.loads(msg.get_body()))
				self._sqs_send_queue.delete_message(msg)
			return positions
		else:
			return -1







def connect_to_sqs_queue(zone, queue_name):

	sqs_conn = boto.sqs.connect_to_region(zone)

	if sqs_conn == None:
		raise TypeError

	sqs_queue = sqs_conn.get_queue(queue_name)

	if sqs_queue == None:
		raise TypeError

	return sqs_conn, sqs_queue





if __name__ == "__main__":



	sqs, queue = connect_to_sqs_queue(zn.ZONE_2, qe.FRONT_END_QUEUE)


	app = tornado.web.Application([(r'/map', MapHandler, dict(sqs_conn=sqs, sqs_queue=queue)), (r'/', BaseHandler)], 
		template_path=os.path.join(os.path.dirname(__file__), "templates"), 
		static_path=os.path.join(os.path.dirname(__file__), "static"),
			debug = True,)
	http_server = tornado.httpserver.HTTPServer(app)
	http_server.listen(options.port)
	tornado.ioloop.IOLoop.instance().start()
	


