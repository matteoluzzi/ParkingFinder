#!/usr/bin/env python
# coding=utf-8

from handlers.BaseHandler import BaseHandler
from tornado.escape import xhtml_escape
from multiprocessing.pool import ThreadPool
from bcrypt import hashpw, gensalt
import tornado.web

'''Handler per gestire il login di un utente, la sessione viene mantenuta tramite un cookie settato sul browser'''

class LoginHandler(BaseHandler):

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