import urllib
from xml.etree import ElementTree as ET

latitude = '41.9361139'
longitude = '12.4371478'

http://nominatim.openstreetmap.org/reverse?format=xml&lat=52.5487429714954&lon=-1.81602098644987&zoom=18&addressdetails=1

requestURL = 'http://nominatim.openstreetmap.org/reverse?format=xml&'
           + 'lat=' + latitude
           + '&lon=' + longitude 

root = ET.parse(urllib.urlopen(requestURL)).getroot()
print root
print '\n'
