#!/usr/bin/env python
# coding=utf-8

from handlers.BaseHandler import BaseHandler

from multiprocessing.pool import ThreadPool
import tornado.web
from boto.sqs.message import Message
import json, re,os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend_server')))
from JSONManager import subscribeEmailNotification 


'''Handler per il processamento delle richieste di sottoscrizione ad uno o più quadranti'''

class QuadrantsSubscriptionHandler(BaseHandler):

	def set_default_headers(self):
		
		self.set_header("Access-Control-Allow-Origin", "*")

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
		#self.__onfinish(None)

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