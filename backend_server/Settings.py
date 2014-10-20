#this class manages the system settings, these settings are loaded
#from a text file and can be in this format:
#key#value
#key#value1|value2|value3

class Settings:
	settings	=	{}	

	#loads the settings from a text file to a dictionary
	def __init__(self,filename):
		inputFile 	= open(filename, 'r')
		mystring=inputFile.readline()
		mystring=mystring.split('\n')[0]
		while ((mystring!="")and(mystring!="\0")):
			onesetting = mystring.split("#")
			key		=	str(onesetting[0])
			value	=	onesetting[1].split("|")
			if len(value)==1:
				value	=	value[0]
			self.settings[key]	=	value
			mystring=inputFile.readline()
			mystring=mystring.split('\n')[0]
		
#test	=	Settings("testimp.txt")
#print test.settings['prova']
#print test.settings['prova2']
