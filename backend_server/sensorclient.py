import socket
import sys
from random import randint
from multiprocessing import Process
import time
HOST, PORT = "localhost", 9999
def sensor(status,nometxt):
	fp= open(nometxt)
	lines=fp.readlines()
	randline=randint(0,len(lines)-1)
	full=lines[int(randline)].split('#') 
	id= full[0] 
	latitude=full[1] 
	longitude=full[2]
	fp.close()
	data = id+status+"_"+latitude+"_"+longitude
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.sendto(data + "\n", (HOST, PORT))


	print "Sent:     {}".format(data)
i=1
while(True):
	if i%50==0:
		time.sleep(10)
	time.sleep(0.1)
	randquadrant= str(randint(1, 1235))
	nometxt="parkings/listquadrant"+randquadrant+".txt"
	i=i+1
	randstat= randint(1, 2)
	if randstat==1:
		p=Process(target=sensor, args=('_E', nometxt))
	else:
		p=Process(target=sensor, args=('_B', nometxt))
	p.start()
	p.join()
