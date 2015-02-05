#this class creates JSON requests from methon calling
#
#defined 3 classes of requests:
#	overview request (contains requestid, response queue name, quadrant id)
#	full list	(same as above)
#	partial list(same as above plus 2 coordinates NW and NE)
# 	updated with methods for notification handling 

import json
import Parking as park

def createOverviewRequest(arg_id,arg_response_queue_name,arg_quadrant_id):
	data		=	[{"type":"overview" , "r_id" : arg_id , "resp_queue":arg_response_queue_name , "quadrant":arg_quadrant_id}]
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
	
def createListResponse(arg_id,parkingList,quadrantID,totseq=1,numberofsequence=1): #da testare
	datalist	=	list()
	for item in parkingList:
		datalist.append(item.getDictionary())
	data		=	[{"type":"list_response" , "r_id" : arg_id, "parkings":datalist, "npackets":totseq, "sequencen":numberofsequence, "quadrantID":quadrantID}]
	data_string	=	json.dumps(data)
	return data_string

def createOverviewResponse(arg_id,percentage,quadrantID):
	data		=	[{"type":"overview_response" , "r_id" : arg_id, "percentage":percentage , "quadrantID":quadrantID}]
	data_string =	json.dumps(data)
	return data_string
	
#metodi per iscrizione o invio notifiche

def sendNotificationForQuadrant(quadrantId,subject,messageBody):
	data		=	{"type":"sendNotification" , "quadrantID":str(quadrantId) , "subject":str(subject) , "messageBody":str(messageBody)}
	data_string	=	json.dumps(data)
	return data_string

def subscribeEmailNotification(quadrantId,mailAddress):
	data		=	{"type":"emailSubscribe" , "quadrantID":str(quadrantId) ,"address":str(mailAddress)}
	data_string	=	json.dumps(data)
	return data_string
	
def subscribeAndroidNotification(quadrantId,token):
	data		=	{"type":"androidSubscribe" , "quadrantID":str(quadrantId) ,"token":str(token)}
	data_string	=	json.dumps(data)
	return data_string
