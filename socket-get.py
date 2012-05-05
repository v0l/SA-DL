#!/usr/bin/env python
#
#	SA-DL v0.1
#

from socket import *
import threading,sys,time

BLOCK_SIZE = 8192
SPEED_UPDATE = 1

class DownloadThread(threading.Thread):
	def __init__(self, host, path, offset, adapter,fileHandle):
		threading.Thread.__init__(self)
		self.file = fileHandle
		try:
			self.s = socket(AF_INET, SOCK_STREAM)
			self.s.bind((adapter,1337))
			self.s.connect( (host, 80) )
			self.q = buildRequest(host,path,offset)
			self.s.send(self.q)
		except Exception as er:
			print er

	def run(self):
		pos = 0
		startTime = time.time()
		lastUpdate = 0
		lpos = 0
		while True:
			try:
				self.s.recv(BLOCK_SIZE)
				pos+=1
				elapsedTime = (time.time()-startTime)
				if lastUpdate+SPEED_UPDATE<elapsedTime:
					lastUpdate = elapsedTime
					sys.stdout.write("\r" + humanize_bytes(lpos*BLOCK_SIZE/elapsedTime) + "/s   ")
					sys.stdout.flush()
					lpos = pos-lpos
			except Exception as er:
				print er
		self.s.close()
        
def buildRequest(host,adr,offset):
	return "GET " + adr + " HTTP/1.1\r\nHost: " + host + "\r\nRange: bytes=" + str(offset) + "-\r\n\r\n\r\n"

def parseContentLength(resp):
	if resp.find("Content-Length:")>0:
		return resp[resp.find("Content-Length:")+16:resp.find("\r\n",resp.find("Content-Length:")-1)]
	else:
		return -1

def humanize_bytes(bytes, precision=2):
    abbrevs = ((1<<50L, 'PB'),(1<<40L, 'TB'),(1<<30L, 'GB'),(1<<20L, 'MB'),(1<<10L, 'kB'),(1, 'bytes'))
    if bytes == 1:
        return '1 byte'
    for factor, suffix in abbrevs:
        if bytes >= factor:
            break
    return '%.*f %s' % (precision, bytes / factor, suffix)

#f = open("test1.data",'w+')
#f.truncate(1024)

t = DownloadThread("minesrc.com","/world.zip",0,"192.168.1.100",220)
t.start()

