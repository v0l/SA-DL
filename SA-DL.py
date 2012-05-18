#!/usr/bin/env python
#
#	SA-DL v0.1.2 Beta
#
#	Copyright Kieran Harkin 2012

from socket import *
import threading,sys,time,array,httplib,datetime

BLOCK_SIZE = 1024
SPEED_UPDATE = 1
DATA_RECV = 0
DATA_LEN = 0
THREADS_DONE = 0
LINKS = []
CHUNK_SIZE = 0
DEVS = []
DEBUG = False

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

def loadInterfaceList(cmd):
	if cmd.find(','):
		for dev in cmd.split(','):
			DEVS.append(dev)
			print "Device added: " + dev
	else:
		DEVS.append(dev)
	
	##Set chunk size
	CHUNK_SIZE = DATA_LEN/len(DEVS)
	
class DownloadThread(threading.Thread):
	def __init__(self, host, path, id, adapter,fileHandle):
		threading.Thread.__init__(self)
		self.file = open(fileHandle,"wb")
		
		offset = CHUNK_SIZE*id
		end = offset+CHUNK_SIZE
		
		self.file.seek(offset)
		
		try:
			self.s = socket(AF_INET, SOCK_STREAM)
			self.s.bind((adapter,0))
			self.s.connect( (host, 80) )
			self.q = buildRequest(host,path,offset,end)
			self.s.send(self.q)
		except:
			print "Connection Error!"

	def run(self):
		global DATA_RECV,DATA_LEN,THREADS_DONE
		
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
					self.s.close()
					return
				DATA_RECV += len(data)
			except:
				print "Socket error..No response"
				return;
		self.s.close()
		print "Done"
		
class MainThread(threading.Thread):
	def __init__(self,host,path):
		global DEBUG
		threading.Thread.__init__(self)
		self.host = host
		self.path = path
		
	def run(self):
		global THREADS_DONE,DATA_RECV,DATA_LEN,DEVS
		DATA_RECV = 0
		DATA_LEN = 0
		THREADS_DONE = 0
		
		##Get content length
		try:
			s = socket(AF_INET, SOCK_STREAM)
			s.settimeout(2.0)
			s.bind((DEVS[0],0))
			s.connect( (self.host, 3128) )
			q = buildRequest(self.host,self.path,0,'')
			print q
			s.send(q)
			d = s.recv(512)
			DATA_LEN = int(self.parseContentLength(d))
		except:
			print "Cant connect to host: " + self.host
			return;
			
		print "File size: " + self.humanize_bytes(DATA_LEN)
		s.close()
		
		##initialize the file
		split = self.path.rfind('/')
		if self.path.rfind('=')>split:
			split = self.path.rfind('=')
			
		File = self.path[split+1:len(self.path)]
		File = File.replace("%20"," ")
		print File + "\n"
		f = open(File,"w")
		f.truncate(DATA_LEN)
		f.close()
		
		for dev in range(len(DEVS)):
			t = DownloadThread(self.host,self.path,dev,DEVS[dev],File)
			t.start()

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
			if THREADS_DONE==len(DEVS):
				#print "\n~" + str(self.humanize_bytes(DATA_RECV/(time.time()-start))) + "/s   "
				#print "Time taken: " + str(datetime.timedelta(seconds=time.time()-start))
				print "\n------------------------------\n"
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
		elif sys.argv[arg]=="--debug":
			DEGUB = True
			
	for link in LINKS:
		if link.find("http://")>=0:
			link = link.replace("http://","")
		try:
			main = MainThread(link[0:link.find("/")],link)
			main.start()
			main.join()
		except:
			print "Error: " + link
			break;

else:
	print "Invalid syntax : " + str(sys.argv)
	printAbout()
