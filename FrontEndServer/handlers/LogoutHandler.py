#!/usr/bin/env python
# coding=utf-8

from handlers.BaseHandler import BaseHandler

'''Handler per la gestione del logout, cancella il cookie settato'''

class LogoutHandler(BaseHandler):

	def get(self):

		self.clear_cookie("username")
		self.clear_cookie("email")
		self.clear_cookie("_xsrf")
		self.redirect("/")

	def post(self):

		self.redirect("/")