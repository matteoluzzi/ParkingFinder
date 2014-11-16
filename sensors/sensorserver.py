import SocketServer
import boto.dynamodb2
import threading
import socket
import time
import ParkingDYDBLoader
#from atomicLong import AtomicLong
from boto.dynamodb2.table import Table
from boto.dynamodb2.items import Item

global listab
listab=list()

global listad
listad={}

global numoperations
numoperations=0


class MyUDPHandler(SocketServer.BaseRequestHandler):
    """
    This class works similar to the TCP handler class, except that
    self.request consists of a pair of data and client socket, and since
    there is no connection the client address must be given explicitly
    when sending data back via sendto().
    """
	
    def handle(self):
    	
    
    	counterlock.acquire()
    	global numoperations
    	numoperations+=1
    	counterlock.release()
    	event.wait()
    	cur_thread = threading.current_thread()
        data = self.request[0].strip()
        full= data.split('_')
        id= full[0]
        stato= full[1]
        latitude= full[2]
        longitude= full[3]
        temp = [id,stato,latitude,longitude]
        print temp
        global listab
        listab.append(temp)
        print cur_thread
        #time.sleep(5)
        #print "slept"
        #print stato
        socket = self.request[1]
        #print "{} wrote:".format(self.client_address[0])
        #print data
        #print cur_thread
        #parking=Table('parking')
        #park = parking.get_item(parkid = id)
        #park['stato']=stato
        #park.save()
        #socket.sendto(data.upper(), self.client_address)

class ThreadedUDPServer(SocketServer.ThreadingMixIn, SocketServer.UDPServer):
	pass

def batch():
	while True:
		if numoperations >= 15:
			global listab
			event.clear()
			global numoperations
			numoperations=0
			print "event numero elementi"
			print len(listab)
			global myLoader
			myLoader=ParkingDYDBLoader.ParkingDYDBLoader('parking')
			
			myLoader.updateFromSensor(listab)
			#batch........
			
			
			#print listab
			del listab
			listab = list()			
			event.set()
			
			print "release"
			
			


#if __name__ == "__main__":

HOST, PORT = "localhost", 9999
counterlock = threading.Lock()

event = threading.Event()
event.set()
check_thread = threading.Thread(target=batch)
check_thread.daemon=True
check_thread.start()
print "check started"
server = ThreadedUDPServer((HOST, PORT), MyUDPHandler)
server.serve_forever()
#server_thread = threading.Thread(target=server.serve_forever)
#server_thread.daemon = True
#server_thread.start()
#print "Server loop running in thread:", server_thread.name
#time.sleep(5)
	
		#SocketServer.UDPServer((HOST, PORT), MyUDPHandler)
	#server.serve_forever()