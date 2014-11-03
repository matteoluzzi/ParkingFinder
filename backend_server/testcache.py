import memcache
import time
mc = memcache.Client(['sdcc.wpvbcm.cfg.usw2.cache.amazonaws.com:11211'])
mc.set("prova","stocazzo",time=60)
out = mc.get("prova")
print str(out)
counter = 0 
while counter<10:
	time.sleep(10)
	out = mc.get("prova")
	counter	=	counter+1
	print str(out)
	
