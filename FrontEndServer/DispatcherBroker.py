# coding=utf-8

from Queue import Queue, Empty
from Dispatcher import DispatcherThread
from threading import Lock

class DispatcherBroker():

	def __init__(self, num_threads, queue_name, zone, quadrantsNum):
		
		#dizionario reqID-subs dove salvo i subscriber serviti
		self._subscribers = {}
		
		#dizionario qID-queue dove salvo le richieste per un dato quadrante
		self._quadrantsRequests = {}

		#dizionario (qID, reqID)-num_of_messages dove salvo il numero di messaggi splittati ricevuti
		self._splittedMessages = {}

		self._requestLock = Lock()
		self._subscribersLock = Lock()
		self._splittedLock = Lock()
		self._dispatcherThreads = set()


		for i in range(1, quadrantsNum):
			self._quadrantsRequests[i] = None


		for i in range(0, num_threads):
			dispatcher = DispatcherThread(self, queue_name, zone)
			dispatcher.start()
			self._dispatcherThreads.add(dispatcher)

	def setComponents(self, handler, queue):
		
		for dispatcher in self._dispatcherThreads:
			dispatcher.setHandler(handler)
			dispatcher.setQueue(queue)



	def subscribe(self, requestID, maxsize):
		'''registra una richiesta'''
		self._subscribersLock.acquire()
		if not self._subscribers.has_key(requestID):
			self._subscribers[requestID] = maxsize
		self._subscribersLock.release()

	def belongsTo(self, requestID):
		'''verifica l'appartenenza di una richiesta al server'''
		self._subscribersLock.acquire()
		try:
			self._subscribers[requestID]
			self._subscribersLock.release()
			return True
		except KeyError:
			print "errore nella belongsTo nel recuperare una subsQueue, coda non trovata"
			self._subscribersLock.release()
			return False


	def delete_subscribers(self, requestID):
		'''cancella l'entry del dizionario relativo ai subscribers per una requestID'''
		try:
			del self._subscribers[requestID]
		except KeyError:
			print "errore nella cancellazione dei subscribers, requestID non trovata"
			return None

	def add_subscriber(self, requestID):
		'''aggiunge un subscribers ogni volta che arriva un messaggio, cancella il dizionario se è l'ultimo messaggio relativo a requestID'''
		self._subscribersLock.acquire()
		try:
			curr_subs = self._subscribers[requestID]
			curr_subs -= 1
			print "---------------> " + repr(requestID) + " mancano " + repr(curr_subs)
			if curr_subs == 0:
				self.delete_subscribers(requestID)
				self._subscribersLock.release()
				print "ultimo messaggio per " + requestID
				return True
			else:
				self._subscribers[requestID] = curr_subs
				self._subscribersLock.release()
		except KeyError:
			self._subscribersLock.release()
			print "errore relativo alla richiesta " + requestID
			return False

	def get_id_request(self, qID):
		'''ritorna i codici di richiesta per un determinato quadrante'''
		self._requestLock.acquire()
		ret = []
		while True:
			try:
				ret.append(self._quadrantsRequests[qID].get_nowait())				
			except KeyError:
				print "coda di richieste non trovata per il quadrante " + str(qID)
				break
			except Empty:
				self._quadrantsRequests[qID] = None
				break
		self._requestLock.release()
		return ret

	def create_quadrant_request(self, qID, reqID):
		'''crea la coda di richieste per il qudrante qID nel caso non fosse presente e vi iniserisce la richiesta'''
		self._requestLock.acquire()
		if not self._quadrantsRequests[qID]:
			self._quadrantsRequests[qID] = Queue()
			self._quadrantsRequests[qID].put_nowait(reqID)
			print "coda creata ", self._quadrantsRequests[qID], qID, reqID
			self._requestLock.release()
			return True
		else:
			print "coda già presente, aggiunta richiesta " + str(reqID) + " per il quadrante " + str(qID)
			queue = self._quadrantsRequests[qID]
			queue.put_nowait(reqID)
			self._requestLock.release()
			return False

	def updateSplittedMessages(self, key, num):
		'''aggiorna il numero di messaggi splittati ricevuti per un dato quadrante e una data richiesta, crea una nuova entry quando riceve il primo messaggio'''
		self._splittedLock.acquire()
		print key, num
		try:
			curr_num = self._splittedMessages[key] -1
			print "messaggio splittato numero " + str(num - curr_num)
			if curr_num == 0: #ultimo messaggio
				del self._splittedMessages[key]
				self._splittedLock.release()
				return True
			self._splittedMessages[key] = curr_num
			self._splittedLock.release()
			return False
		except KeyError: #primo messaggio tra quelli splittati
			self._splittedMessages[key] = num - 1
			print "messaggio splittato numero 1"
			self._splittedLock.release()
			return False



