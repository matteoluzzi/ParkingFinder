#!/usr/bin/env python
# coding=utf-8

from handlers.BaseHandler import BaseHandler


'''Handler principale responsabile di renderizzare l'home page del sito'''

class HomeHandler(BaseHandler):

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