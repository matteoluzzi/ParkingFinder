#this class creates JSON requests from methon calling
#
#defined 3 classes of requests:
#	overview request (contains requestid, response queue name, quadrant id)
#	full list	(same as above)
#	partial list(same as above plus 2 coordinates NW and NE)

import json
import Parking as park

def createOverviewRequest(arg_id,arg_response_queue_name,arg_quadrant_id):
	data		=	{"type":"overview" , "r_id" : arg_id , "resp_queue":arg_response_queue_name , "quadrant":arg_quadrant_id}
	data_string	=	json.dumps(data)
	return data_string
	
def createFullListRequest(arg_id,arg_response_queue_name,arg_quadrant_id):
	data		=	[{"type":"full_list" , "r_id" : arg_id , "resp_queue":arg_response_queue_name , "quadrant":arg_quadrant_id}]
	data_string	=	json.dumps(data)
	return data_string
	
def createBoundedListRequest(arg_id,arg_response_queue_name,arg_quadrant_id,arg_NW,arg_SE):
	data		=	[{"type":"bounded_list" , "r_id" : arg_id , "resp_queue":arg_response_queue_name , "quadrant":arg_quadrant_id, "NWlat":arg_NW['lat'] , "NWlon":arg_NW['lon'] , "SElat":arg_SE['lat'] ,"SElon":arg_SE['lon']}]
	data_string	=	json.dumps(data)
	return data_string
	
def createListResponse(arg_id,parkingList): #da testare
	datalist	=	list()
	for item in parkingList:
		datalist.append(item.getDictionary())
	data		=	[{"type":"list_response" , "r_id" : arg_id, "parkings":datalist}]
	data_string	=	json.dumps(data)
	return data_string

def createOverviewResponse(arg_id,percentage,quadrantID):
	data		=	[{"type":"overview_response" , "percentage":percentage , "quadrantID":quadrantID}]
	data_string =	json.dumps(data)
	return data_string
	


# test1 = createOverviewRequest(2,"pippo",123)
# test2 = createFullListRequest(3,"pluto",124)
# NW	=	{"lat":12.44,"lon":44.34}
# SE	=	{"lat":9.55,"lon":26.73}
# test3 = createBoundedListRequest(4,"topolino",125,NW,SE)
# #print test1
# #print test2
# #print test3
# testp1	=	park.Parking(1)
# testp2	=	park.Parking(2)
# testp3	=	park.Parking(3)
# plist	=	list()
# plist.append(testp1)
# plist.append(testp2)
# plist.append(testp3)
#print testp1.getStatus()
#print testp1.getExtra()
#print createListResponse(23,plist)