#NON FUNZIONA SU AWS, SI PUO RIMUOVERE
#USATO PER OTTENERE QUARTIERI RELATIVI AI QUADRANTI, NON FA PARTE DEL PROGETTO
import SearchQuadrant as searchquadrant
import QuadrantTextFileLoader as loader
import urllib2
from xml.etree import ElementTree as ET

#http://nominatim.openstreetmap.org/reverse?format=xml&lat=52.5487429714954&lon=-1.81602098644987&zoom=18&addressdetails=1
def getSuburb(latitude,longitude):
	requestURL = 'http://nominatim.openstreetmap.org/reverse?format=xml&'+'lat='+str(latitude)+'&lon='+str(longitude) 
	#print requestURL
	root = ET.parse(urllib2.urlopen(requestURL)).getroot()
	for child in root:
		#print child.tag
		#print child.attribute
		#print "#"
		for child2 in child:
			name	=	child2.tag
			if name=="suburb":
				return "Suburb "+child2.text
	for child in root:
		#print child.tag
		#print child.attribute
		#print "#"
		for child2 in child:
			name	=	child2.tag
			if name=="postcode":
				return "Post Code "+child2.text
	for child in root:
		#print child.tag
		#print child.attribute
		#print "#"
		for child2 in child:
			name	=	child2.tag
			if name=="city_district":
				return "City District "+child2.text
	for child in root:
		#print child.tag
		#print child.attribute
		#print "#"
		for child2 in child:
			name	=	child2.tag
			if name=="road":
				return "Road "+child2.text
	for child in root:
		#print child.tag
		#print child.attribute
		#print "#"
		for child2 in child:
			name	=	child2.tag
			if name=="city":
				return "City "+child2.text
	return requestURL
print getSuburb('41.9361139','12.4371478')
listaQuadranti 	= loader.QuadrantTextFileLoader.load('listaquadranti.txt',0)
counter = 1
out_file = open("test.txt","w")
for item in listaQuadranti:
	center	=	item.getCenter()
	outstring	=	str(counter)+"\t"+getSuburb(center['lat'],center['lon'])+str('\n')
	print	outstring
	out_file.write(outstring)
	counter = counter + 1
out_file.close()
