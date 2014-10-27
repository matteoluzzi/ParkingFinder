import boto.dynamodb2
from boto.dynamodb2.fields import HashKey, RangeKey, AllIndex
from boto.dynamodb2.table import Table
from boto.dynamodb2.types import NUMBER

connection= boto.dynamodb2.connect_to_region('eu-west-1')
parking = Table.create('parking', schema=[HashKey('parkid'),])