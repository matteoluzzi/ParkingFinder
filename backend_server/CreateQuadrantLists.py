#USATO UNA VOLTA SOLA, NON FA PARTE DEL PROGETTO


import Quadrant as quadrant
import SearchQuadrant as searchquadrant
import QuadrantTextFileLoader as loader
#import ParkingDYDBLoader as DBloader

def initializeQuadrants(searcher,parkingList):
	for item in parkingList:
			#print item
			#print item.getLatitude()
			lat				=	item.getLatitude()
			lon				=	item.getLongitude()
			point			=	[lat,lon]
			targetQuadrant	=	searcher.searchQuadrant(point)
			if targetQuadrant != -1:
				targetQuadrant.addToParkList(item)
			else:	
				raise Exception('quadrant not found for an item '+str(item.getId())+' latitude '+str(lat)+" longitude "+str(lon))
#myDBLoader		= DBloader.ParkingDYDBLoader('posti',True,str("sdcc.wpvbcm.cfg.usw2.cache.amazonaws.com:11211"),600)
print "ok1"
listaposti		= loader.QuadrantTextFileLoader.loadParking('postiroma.txt')
print "ok2"
listaQuadranti 	= searchquadrant.SearchQuadrant(loader.QuadrantTextFileLoader.load('listaquadranti.txt',0))
print "ok3"
initializeQuadrants(listaQuadranti,listaposti)
print "ok4"
#testquadrant = listaQuadranti.getQuadrantInstance(12)
#loader.QuadrantTextFileLoader.loadQuadrantParkings(testquadrant,"parkings/listquadrant62.txt",myDBLoader)
#testquadrant.getParkList()[0].update()
#quadrantParkList	=	testquadrant.getParkList()
#nparkings			=	len(quadrantParkList)
#print "chiamo batch update su "+str(nparkings)
#myDBLoader.batchUpdate(testquadrant.getParkList())
#print testquadrant.getParkList()[0]
#print "pippo"+str(testquadrant.getParkList()[0])
counter	=	1
mylist	=	list()
for item in listaQuadranti.quadrantsList:
	if(item.getNumberOfParkings()<=3000):
		mylist.append(item)
	else:
		qnlist	=	item.getSplitted(3000)
		for itemint in qnlist:
			mylist.append(itemint)
		
out_file2 = open("newpark/listaquadranti.txt","w")
for item in mylist:	
	print str(item.getNumberOfParkings())
	listapostiquadrante	=	item.getParkList()
	quadrantID	=	item.getID()
	out_file = open("newpark/listquadrant"+str(counter)+".txt","w")
	for itemint in listapostiquadrante:
		itemid	=	itemint.getId()
		itemlat =	itemint.getLatitude()
		itemlon	=	itemint.getLongitude()
		out_file.write(str(itemid)+"#"+str(itemlat)+"#"+str(itemlon)+"\n")
		testl	=	list()
		testl.append(itemlat)
		testl.append(itemlon)
		testr	=	item.inside(testl)
		if (testr==False):
			raise Exception("wrong quadrants")
		else:
			print "#"
	bounds	=	item.getBoundaries()
	NWString=	str(bounds['NW'][0])+"|"+str(bounds['NW'][1])
	NEString=	str(bounds['NE'][0])+"|"+str(bounds['NE'][1])
	SWString=	str(bounds['SW'][0])+"|"+str(bounds['SW'][1])
	SEString=	str(bounds['SE'][0])+"|"+str(bounds['SE'][1])
	myline	=	str(counter)+"#"+NWString+"#"+NEString+"#"+SWString+"#"+SEString+"\n"
	out_file2.write(myline)
	out_file.close()
	counter	=	counter+1
out_file2.close()
#testpoint	=	list()
#testpoint.append(41.92)
#testpoint.append(12.34)
#print listaQuadranti.searchQuadrant(testpoint)
#print "percentuale parcheggi liberi"+str(testquadrant.getPercentageFreeParkings())
