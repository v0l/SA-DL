#!/usr/bin/env python
#
#	SA-DL v0.3 POC
#

from socket import *
import threading,sys,time,array

BLOCK_SIZE = 128
SPEED_UPDATE = 1
DATA_RECV = 0
DATA_LEN = 0

def buildRequest(host,adr,offset,end):
	return "GET " + adr + " HTTP/1.1\r\nHost: " + host + "\r\nRange: bytes=" + str(offset) + "-" + str(end) + "\r\n\r\n\r\n"
		
class DownloadThread(threading.Thread):
	def __init__(self, host, path, offset, adapter,fileHandle):
		threading.Thread.__init__(self)
		self.file = open(fileHandle,'w')
		self.file.seek(offset)
		if offset != 0:
			end = DATA_LEN/2
		else:
			end = DATA_LEN
		try:
			self.s = socket(AF_INET, SOCK_STREAM)
			self.s.bind((adapter,1337))
			self.s.connect( (host, 80) )
			self.q = buildRequest(host,path,offset,end)
			self.s.send(self.q)
		except Exception as er:
			print er

	def run(self):
		global DATA_RECV,DATA_LEN
		headerClear = False
		while True:
			try:
				data = self.s.recv(BLOCK_SIZE)
				self.file.write(data)
				DATA_RECV += len(data)
			except Exception as er:
				print er
				return;
		self.s.close()
		print "Done"
class MainThread(threading.Thread):
	def __init__(self,host,path):
		threading.Thread.__init__(self)
		
		##Globals
		global DATA_LEN
		
		##Get content length
		s = socket(AF_INET, SOCK_STREAM)
		s.connect( (host, 80) )
		q = buildRequest(host,path,0,'')
		s.send(q)
		d = s.recv(512)
		print d
		DATA_LEN = int(self.parseContentLength(d))
		print "File size: " + self.humanize_bytes(DATA_LEN)
		s.close()
		
		##initialize the file
		File = path[path.rfind('/')+1:len(path)]
		f = open(File,'w+')
		f.truncate(DATA_LEN)
		f.close()
		
		t = DownloadThread(host,path,0,"192.168.1.100",File)
		t.start()
		t2 = DownloadThread(host,path,DATA_LEN/2,"192.168.1.15",File)
		t2.start()
		
	def run(self):
		downloading = True

		while downloading:
			sys.stdout.write("\r" + str(self.humanize_bytes(DATA_RECV)) + "   ")
			sys.stdout.flush()
			time.sleep(1)
			
	def parseContentLength(self,resp):
		if resp.find("Content-Length:")>0:
			return resp[resp.find("Content-Length:")+16:resp.find("\r\n",resp.find("Content-Length:")-1)]
		else:
			return -1

	def humanize_bytes(self,bytes, precision=2):
		bytes = float(bytes)
		a = ['B','kB','MB','GB','PB']
		p = 0
		while bytes>=1024:
			bytes /= 1024
			p += 1
		return str(str(round(bytes,precision)) + " " + a[p])

main = MainThread("minesrc.com","/imgs/screenshots/2012-02-03_18.08.48.png")
main.start()
