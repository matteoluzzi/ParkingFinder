#!/usr/bin/env python
# coding=utf-8
from handlers.BaseHandler import BaseHandler
from bcrypt import hashpw, gensalt
from multiprocessing.pool import ThreadPool
from tornado.escape import xhtml_escape
import tornado.web

'''Handler per gestire la registrazione di un utente al sito'''

class RegisterHandler(BaseHandler):

	def initialize(self, front_end_address, port, table):

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
