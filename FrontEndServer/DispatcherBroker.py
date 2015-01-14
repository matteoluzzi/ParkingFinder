# coding=utf-8

from Queue import Queue, Empty
from Dispatcher import DispatcherThread
from threading import Lock

class DispatcherBroker():

	def __init__(self, num_threads, queue_name, zone, quadrantsNum):
		
		#dizionario reqID-subs dove salvo i subscriber serviti
		self._subscribers = {}
		
		#dizionario reqID-queue dove salvo le code di comunicazione con i subscribers
		self._subsQueues = {}

		#dizionario qID-queue dove salvo le richieste per un dato quadrante
		self._quadrantsRequests = {}

		self._lock = Lock()
		self._message_queue_lock = Lock()

		for i in range(1, quadrantsNum):
			self._quadrantsRequests[i] = None


		for i in range(0, num_threads):
			dispatcher = DispatcherThread(self, queue_name, zone)
			dispatcher.start()

	def subscribe(self, requestID, maxsize):
		self._message_queue_lock.acquire()
		if not self._subsQueues.has_key(requestID):
			self._subsQueues[requestID] = Queue(maxsize=maxsize)
		self._message_queue_lock.release()

	def belongsTo(self, requestID):
		'''verifica l'appartenenza di una richiesta al server'''
		self._message_queue_lock.acquire()
		try:
			self._subsQueues[requestID]
			self._message_queue_lock.release()
			return True
		except KeyError:
			print "errore nella belongsTo nel recuperare una subsQueue, coda non trovata"
			self._message_queue_lock.release()
			return False
			
	def get_message_queue(self, requestID):
		'''ritorna il riferimento alla coda richiesta'''
		try:
			queue = self._subsQueues[requestID]
			return queue
		except KeyError:
			print "errore nel recuperare una subsQueue, coda non trovata ", requestID
			return None

	def delete_queue(self, requestID):
		'''cancella la coda identificata da requestID quando tutti i subscribers sono stati serviti'''
		try:
			del self._subsQueues[requestID]
		except KeyError:
			print "errore nella cancellazione della subsQueue, coda non trovata"
			return None

	def delete_subscribers(self, requestID):
		'''cancella l'entry del dizionario relativo ai subscribers per una requestID'''
		try:
			del self._subscribers[requestID]
		except KeyError:
			print "errore nella cancellazione dei subscribers, requestID non trovata"
			return None

	def add_subscriber(self, requestID):
		'''aggiunge un subscribers ogni volta che arriva un messaggio, cancella il dizionario se è l'ultimo messaggio relativo a requestID'''
		queue = self.get_message_queue(requestID)
		current_subs = 0
		if queue != None:
			if not requestID in self._subscribers.keys():
				self._subscribers[requestID] = 1
				current_subs = 1
			else:
				current_subs = self._subscribers[requestID] + 1
				self._subscribers[requestID] = current_subs

			counter = queue.maxsize - current_subs
			print "--------------->current_subs=", current_subs, " counter=", counter, requestID

			if counter == 0: #ultimo messaggio
				self.delete_subscribers(requestID)
				print "ultimo messaggio per " + requestID
				return True
			return False
		else:
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

