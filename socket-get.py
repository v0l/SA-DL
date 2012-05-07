#!/usr/bin/env python
#
#	SA-DL v1.1 POC
#
#	Copyright Kieran Harkin 2012

from socket import *
import threading,sys,time,array,httplib,datetime

BLOCK_SIZE = 512
SPEED_UPDATE = 1
DATA_RECV = 0
DATA_LEN = 0
THREADS_DONE = 0
LINKS = []

def buildRequest(host,adr,offset,end):
	return "GET " + adr + " HTTP/1.1\r\nHost: " + host + "\r\nRange: bytes=" + str(offset) + "-" + str(end) + "\r\n\r\n\r\n"

def printAbout():
	print "Copyright Kieran Harkin 2012 (c)\n\nUsage:\n\tSA-DL.py <options> <file1,file2...>\n\n\nOptions:\n\t-i\tEnter interfaces to use (comma spereated)\n\t\t-i 192.168.0.1,192.168.0.2\n\n\t-f\tEnter text file with links\n\t\t-f links.txt\n\n\t-d\tOutput directory\n\t\t-d downloads/\n"

def loadTextFile(file):
	global LINKS
	try:
		file = open(file,"r")
		for i in file:
			LINKS.append(i.strip())	
		print str(len(LINKS)) + " links loaded!\n"
		return True
	except Exception as ex: 
		print ex
		return False
class DownloadThread(threading.Thread):
	def __init__(self, host, path, offset, adapter,fileHandle,name):
		threading.Thread.__init__(self)
		self.name = name
		self.file = open(fileHandle,'wb')
		self.file.seek(offset)
		
		if offset>0:
			end = DATA_LEN
		else:
			end = (DATA_LEN/2)-1
			
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
					#print "\n" + self.name + ":~" + str(round(DATA_RECV/(time.time()-start)/1024,2)) + "kB/s"
					self.s.close()
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
		self.host = host
		self.path = path
		
	def run(self):
		global THREADS_DONE,DATA_RECV,DATA_LEN
		DATA_RECV = 0
		DATA_LEN = 0
		THREADS_DONE = 0
		
		##Get content length
		s = socket(AF_INET, SOCK_STREAM)
		s.connect( (self.host, 80) )
		q = buildRequest(self.host,self.path,0,'')
		s.send(q)
		d = s.recv(512)
		DATA_LEN = int(self.parseContentLength(d))
		print "File size: " + self.humanize_bytes(DATA_LEN)
		s.close()
		
		##initialize the file
		File = self.path[self.path.rfind('/')+1:len(self.path)]
		File = File.replace("%20"," ")
		print File + "\n"
		f = open(File,'wb+')
		f.truncate(DATA_LEN)
		f.close()
		
		self.t = DownloadThread(self.host,self.path,0,"192.168.1.100",File,"Thread-1")
		self.t.start()
		self.t2 = DownloadThread(self.host,self.path,DATA_LEN/2,"192.168.1.10",File,"Thread-2")
		self.t2.start()
		downloading = True
		start = time.time()
		lSize = 0
		
		while downloading:
			try:
				tos = ((DATA_LEN-DATA_RECV)/(DATA_RECV-lSize))
			except:
				tos = 0

			sys.stdout.write("\r" + str(self.humanize_bytes(DATA_RECV)) + " - " + self.humanize_bytes(DATA_RECV-lSize) + "/s [ " + str(datetime.timedelta(seconds=tos)) + " ]    ")
			sys.stdout.flush()
			lSize = DATA_RECV
			if THREADS_DONE==2:
				#print "\n~" + str(self.humanize_bytes(DATA_RECV/(time.time()-start))) + "/s   "
				#print "Time taken: " + str(datetime.timedelta(seconds=time.time()-start))
				print "-----------------\n"
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

##Menu systems
if len(sys.argv)>1:
	
	for arg in range(len(sys.argv)):
		if sys.argv[arg]=="-f":
			#Load text file of links
			try:
				if not loadTextFile(sys.argv[arg+1]):
					raise
			except:
				print "Invalid syntax : " + str(sys.argv)
				exit()
		elif sys.argv[arg]=="-i":
			#load the interfaces
			loadInterfaceList(sys.argv[arg+1])
			
	for link in LINKS:
		if link.find("http://")>=0:
			link = link.replace("http://","")
		main = MainThread(link[0:link.find("/")],link[link.find("/"):len(link)])
		main.start()
		main.join()
else:
	print "Invalid syntax : " + str(sys.argv)
	printAbout()