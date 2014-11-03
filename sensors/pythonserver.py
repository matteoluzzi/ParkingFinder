import SocketServer
import boto.dynamodb2
from boto.dynamodb2.table import Table
from boto.dynamodb2.items import Item

class MyUDPHandler(SocketServer.BaseRequestHandler):
    """
    This class works similar to the TCP handler class, except that
    self.request consists of a pair of data and client socket, and since
    there is no connection the client address must be given explicitly
    when sending data back via sendto().
    """

    def handle(self):
        data = self.request[0].strip()
        full= data.split('_')
        id= full[0]
        stato= full[1]
        print id
        print stato
        socket = self.request[1]
        print "{} wrote:".format(self.client_address[0])
        print data
        parking=Table('parking')
        park = parking.get_item(parkid = id)
        park['stato']=stato
        park.save()
        #socket.sendto(data.upper(), self.client_address)

if __name__ == "__main__":
    HOST, PORT = "localhost", 9999
    server = SocketServer.UDPServer((HOST, PORT), MyUDPHandler)
    server.serve_forever()
