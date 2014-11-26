import Quadrant as quadrant
import Parking as pk


class QuadrantTextFileLoader:
	
	#loads quadrants from a textfile
	@staticmethod
	def load(filename,updater=0):
		quadrantsList	= list()
		inputFile 	= open(filename, 'r')
		mystring=inputFile.readline()
		mystring=mystring.split('\n')[0]
		while ((mystring!="")and(mystring!="\0")):
			quadrantinfo = mystring.split("#")
			newID		=	quadrantinfo[0]
			newNW		=	quadrantinfo[1].split("|") #pair of coordinates
			newNE		=	quadrantinfo[2].split("|")
			newSW		=	quadrantinfo[3].split("|")
			newSE		=	quadrantinfo[4].split("|")
			newQuadrant	=	quadrant.Quadrant(newID,newNW,newNE,newSW,newSE,updater)
			quadrantsList[int(newID)]=newQuadrant
			mystring=inputFile.readline()
			mystring=mystring.split('\n')[0]
		return quadrantsList

	#loads parkings from a textfile
	@staticmethod
	def loadParking(filename,updater=0):
		print "loading"
		parkingList	= list()
		inputFile 	= open(filename, 'r')
		mystring=inputFile.readline()
		mystring=mystring.split('\n')[0]
		while ((mystring!="")and(mystring!="\0")):
			#print mystring
			parkinginfo = mystring.split("#")
			newID		=	parkinginfo[0]
			lat 		=	parkinginfo[1]
			lon		=	parkinginfo[2]
			newParking	=	pk.Parking(newID,updater,lat,lon)
			parkingList.append(newParking)
			mystring=inputFile.readline()
			mystring=mystring.split('\n')[0]
		print "finished"
		return parkingList
	
	@staticmethod
	def loadQuadrantParkings(aQuadrant,aFile,anUpdater):
		inputFile 	= open(aFile, 'r')
		mystring=inputFile.readline()
		mystring=mystring.split('\n')[0]
		while ((mystring!="")and(mystring!="\0")):
			#print mystring
			parkinginfo = mystring.split("#")
			newID		=	parkinginfo[0]
			lat 		=	parkinginfo[1]
			lon			=	parkinginfo[2]
			newParking	=	pk.Parking(newID,anUpdater,lat,lon)
			aQuadrant.addToParkList(newParking)
			mystring=inputFile.readline()
			mystring=mystring.split('\n')[0]

