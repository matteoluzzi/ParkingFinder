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

		self._lock = Lock()
		self._subscribers_lock = Lock()
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
		self._subscribers_lock.acquire()
		if not self._subscribers.has_key(requestID):
			self._subscribers[requestID] = maxsize
		self._subscribers_lock.release()

	def belongsTo(self, requestID):
		'''verifica l'appartenenza di una richiesta al server'''
		self._subscribers_lock.acquire()
		try:
			self._subscribers[requestID]
			self._subscribers_lock.release()
			return True
		except KeyError:
			print "errore nella belongsTo nel recuperare una subsQueue, coda non trovata"
			self._subscribers_lock.release()
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
		self._subscribers_lock.acquire()
		try:
			curr_subs = self._subscribers[requestID]
			curr_subs -= 1
			print "---------------> " + repr(requestID) + " mancano " + repr(curr_subs)
			if curr_subs == 0:
				self.delete_subscribers(requestID)
				self._subscribers_lock.release()
				print "ultimo messaggio per " + requestID
				return True
			else:
				self._subscribers[requestID] = curr_subs
				self._subscribers_lock.release()
		except KeyError:
			self._subscribers_lock.release()
			print "errore relativo alla richiesta " + requestID
			return False

	def get_id_request(self, qID):
		'''ritorna i codici di richiesta per un determinato quadrante'''
		self._lock.acquire()
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
		self._lock.release()
		return ret

	def create_quadrant_request(self, qID, reqID):
		'''crea la coda di richieste per il qudrante qID nel caso non fosse presente e vi iniserisce la richiesta'''
		self._lock.acquire()
		if not self._quadrantsRequests[qID]:
			self._quadrantsRequests[qID] = Queue()
			self._quadrantsRequests[qID].put_nowait(reqID)
			print "coda creata ", self._quadrantsRequests[qID], qID, reqID
			self._lock.release()
			return True
		else:
			print "coda già presente, aggiunta richiesta " + str(reqID) + " per il quadrante " + str(qID)
			queue = self._quadrantsRequests[qID]
			queue.put_nowait(reqID)
			self._lock.release()
			return False

