#this simple class implements the quadrant research

import Quadrant as quadrant
import QuadrantTextFileLoader as loader

class SearchQuadrant:
	inputFile	=	0
	quadrantsList	=	0
	quadrantsDict	=	{}
	def __init__(self,aList):	#list of quadrants
		self.quadrantsList =	aList
		for item in aList:
			quadId	=	item.getID()
			quadrantsDict[str(quadId)] = item

	#returns a quadrant for a geographic coordinate
	def searchQuadrant(self,point):
		latitude	=	float(point[0])
		longitude	=	float(point[1])
		myquadrant	=	-1	#if returns -1 there is no quadrant available for that coordinate
		for item in self.quadrantsList:
			check	=	item.inside(point)
			if check==True:
				return item
		return -1

	#returns the object with a quadrantID
	def getQuadrantInstance(self,qID):
		if self.quadrantsDict[int(qId)]==None:
			return -1
		else:
			return self.quadrantsList[int(qId)]
		
	def getQuadrantsForAnArea(self,NW,NE,SW,SE):
		fakeQuadrant	=	Quadrant(-1,NW,NE,SW,SE)
		resultList		=	list()
		for item in self.quadrantsList:
			coord	=	item.getBoundaries()
			aNW		=	coord['NW']
			aNE		=	coord['NE']
			aSW		=	coord['SW']
			aSE		=	coord['SE']
			if(fakeQuadrant.inside(aNW) or fakeQuadrant.inside(aNE) or fakeQuadrant.inside(aSW) or fakeQuadrant.inside(aSE)):
				returnList.append(item)
		return returnList
