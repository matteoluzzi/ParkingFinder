import boto.dynamodb2
from boto.dynamodb2.table import Table
from boto.dynamodb2.items import Item 



file = open('parkinittest.txt', 'r')

for line in file:
	full=line.split('#') 
	id= full[0] 
	latitude=full[1] 
	longitude=full[2]
	parking=Table('parking')
	with parking.batch_write() as batch:
		batch.put_item(data={
			'parkid': id,
			'stato': 'init',
			'latitude': latitude,
			'longitude': longitude,
	}),
   