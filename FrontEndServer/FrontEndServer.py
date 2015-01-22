#!/usr/bin/env python
# coding=utf-8

import ConfigParser, os
from multiprocessing.pool import ThreadPool

import boto.sqs as sqs
from boto.dynamodb2.table import Table

from DispatcherBroker_alt import DispatcherBroker
from handlers.HomeHandler import HomeHandler
from handlers.RegisterHandler import RegisterHandler
from handlers.LoginHandler import LoginHandler
from handlers.LogoutHandler import LogoutHandler
from handlers.QuadrantsSubscriptionHandler import QuadrantsSubscriptionHandler
from handlers.MapHandler_alt import MapHandler

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.websocket


class Application(tornado.web.Application):

	def __init__(self, settings):

		sqs_conn, user_table = self.connect(settings['zone'], settings['user_table'])
		self.request_queue = sqs_conn.get_queue(settings['request_queue'])
		self.notification_queue = sqs_conn.get_queue(settings['notification_queue'])
		self.quadrantslist = self.openQuadrantsList(settings['quadrants_list_path'])
		self.dispatcher = DispatcherBroker(int(settings['dispatcher_threads']), settings['response_queue'], settings['zone'], len(self.quadrantslist))

		pool = ThreadPool(int(settings['pool_size']))

		handlers = [
						(r'/', HomeHandler, dict(front_end_address=settings['front_end_address'], port=settings['port'])),
						(r'/register', RegisterHandler, dict(front_end_address=settings['front_end_address'], port=settings['port'], table=user_table)),
						(r'/login', LoginHandler, dict(table=user_table)),
						(r'/logout', LogoutHandler),
						(r'/subsquadrants', QuadrantsSubscriptionHandler, dict(subs_requests_queue=self.notification_queue)),
						(r'/imgs/(.*)', tornado.web.StaticFileHandler, {'path': 'static/imgs'}),
						(r'/map', MapHandler, dict(sqs_conn=sqs_conn, request_queue=self.request_queue, dispatcher=self.dispatcher, quadrantslist=self.quadrantslist, pool=pool, settings=settings))				
		]
		settings = dict(
						template_path=os.path.join(os.path.dirname(__file__), "templates"), static_path=os.path.join(os.path.dirname(__file__), "static"), 
						debug = True,
						xsrf_cookies=True,
						cookie_secret="l/4VqtnPR3Wv08iW5cX9UR+t7Prkekxuq82yjZn5eDc="
		)

		tornado.web.Application.__init__(self, handlers, **settings)

	@staticmethod
	def openQuadrantsList(path):
		line = ""
		with open(path, 'r') as inp:
			line = inp.readlines()
		return "".join(line)

	@staticmethod
	def connect(zone, table_name):	
		return sqs.connect_to_region(zone), Table(table_name)


def main():

	config = ConfigParser.ConfigParser()
	config.read("./settings/FrontEndSettings.ini")
	settings = config.defaults()
	application = Application(settings)

	http_server = tornado.httpserver.HTTPServer(application)
	http_server.listen(settings['port'])
	print ""
	print "----------------------------------------------"
	print "Started on port %s..." % (settings['port'],)
	print "----------------------------------------------"
	print ""
	tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()