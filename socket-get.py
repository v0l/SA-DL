from socket import *

def getPacket(host,adr):
	return "GET " + adr + " HTTP/1.1\r\nHost: " + host + "\r\nUser-Agent: Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2 (.NET CLR 3.5.30729)\r\nAccept: */*\r\nAccept-Language: en\r\n\r\nAccept-Charset: utf-8\r\nKeep-Alive: 300\r\nConnection: keep-alive\r\n\r\n\r\n"

def parseContentLength(resp):
	if resp.find("Content-Length:")>0:
		return resp[resp.find("Content-Length:")+16:resp.find("\r\n",resp.find("Content-Length:")-1)]
	else:
		return -1

s = socket( AF_INET, SOCK_STREAM )
s.connect( ( "minesrc.com", 80 ) )
req = getPacket("minesrc.com","/world.zip")
bytesSent = s.send( req )
data = s.recv(256)
size = parseContentLength(data)
print str(round(float(size)/1024/1024,2)) + " Mb"
s.close()
