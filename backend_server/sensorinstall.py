import boto.dynamodb2
from boto.dynamodb2.table import Table
from boto.dynamodb2.items import Item 




for i in range(1,2000):
	n=0
	nometxt="parkings/listquadrant"+str(i)+".txt"
	fp= open(nometxt)
	lines=fp.readlines()
	for item in lines:
		full=lines[n].split('#') 
		n=n+1
		id= full[0] 
		latitude=full[1] 
		longitude=full[2]
		fp.close()
		print id
		print latitude
		print longitude
		parking=Table('parking')
		with parking.batch_write() as batch:
			batch.put_item(data={
				'idposto': id,
				'extra' : 'init',
				'stato': 'init',
				'latitude': latitude,
				'longitude': longitude,
				}),
