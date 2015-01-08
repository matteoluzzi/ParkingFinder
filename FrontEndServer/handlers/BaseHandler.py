import tornado.web

'''Handler generico dal quale ereditano tutti gli altri handlers che nesessitano di comunicare tramite cookies'''

class BaseHandler(tornado.web.RequestHandler):

	def set_flash_message(self, key, message):
		self.set_secure_cookie('flash_msg_%s' % key, message)
	
	def get_flash_message(self, key):
		val = self.get_secure_cookie('flash_msg_%s' % key)
		self.clear_cookie('flash_msg_%s' % key)
		return val