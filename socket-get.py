#!/usr/bin/env python
#
#	SA-DL v0.3 POC
#

from socket import *
import threading,sys,time,array,httplib

BLOCK_SIZE = 1024
SPEED_UPDATE = 1
DATA_RECV = 0
DATA_LEN = 0
THREADS_DONE = 0

def buildRequest(host,adr,offset,end):
	return "GET " + adr + " HTTP/1.1\r\nHost: " + host + "\r\nRange: bytes=" + str(offset) + "-" + str(end) + "\r\n\r\n\r\n"
		
class DownloadThread(threading.Thread):
	def __init__(self, host, path, offset, adapter,fileHandle,name):
		threading.Thread.__init__(self)
		self.name = name
		self.file = open(fileHandle,'w')
		self.file.seek(offset)
		
		if offset>0:
			end = DATA_LEN
		else:
			end = DATA_LEN/2
			
		try:
			self.s = socket(AF_INET, SOCK_STREAM)
			self.s.bind((adapter,0))
			self.s.connect( (host, 80) )
			self.q = buildRequest(host,path,offset,end)
			self.s.send(self.q)
		except Exception as er:
			print er

	def run(self):
		global DATA_RECV,DATA_LEN,THREADS_DONE
		headerClear = False
		
		self.data_len = 0
		start = time.time()
		resp = httplib.HTTPResponse(self.s)
		resp.begin()
		
		while True:
			try:
				data = resp.read(BLOCK_SIZE)
				if len(data)>0:
					self.file.write(data)
					self.data_len += len(data)
				else:
					THREADS_DONE += 1
					print "\n" + self.name + ":~" + str(round(DATA_RECV/(time.time()-start)/1024,2)) + "kB/s"
					return
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
		DATA_LEN = int(self.parseContentLength(d))
		print "File size: " + self.humanize_bytes(DATA_LEN)
		s.close()
		
		##initialize the file
		File = path[path.rfind('/')+1:len(path)]
		f = open(File,'w+')
		f.truncate(DATA_LEN)
		f.close()
		
		self.t = DownloadThread(host,path,1,"192.168.1.100",File,"Thread-1")
		self.t.start()
		self.t2 = DownloadThread(host,path,DATA_LEN/2,"192.168.1.16",File,"Thread-2")
		self.t2.start()
		
	def run(self):
		global THREADS_DONE,DATA_RECV
		downloading = True
		start = time.time()
		
		while downloading:
			sys.stdout.write("\r" + str(self.humanize_bytes(DATA_RECV)) + "   ")
			sys.stdout.flush()
			if THREADS_DONE==2:
				print "\n~" + str(self.humanize_bytes(DATA_RECV/(time.time()-start))) + "/s"
				print "Time taken: " + str(time.time()-start)
				break
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

main = MainThread("kharkin.ie","/SubExtract.zip")
main.start()
