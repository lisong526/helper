# -*- coding: utf-8 -*-

"""
    Author:LI SONG
    E-mail:lisong526@gmail.com
"""

__version__ = '0.9'

import os,sys,time,cStringIO,urllib,heapq
from pyquery import PyQuery
import pycurl
from threading import Thread
from Queue import Queue
import traceback
import smtplib
from email.mime.text import MIMEText

#设置默认编码
def setdefaultencoding():
	reload(sys)
	sys.setdefaultencoding('utf8')
	print time.strftime('%Y%m%d%H%M%S',time.localtime())

number_char="0123456789"

#字符串转整数 stof(xxx2.33dd)=2
def stoi(s):
	num=""
	start=False
	for i in range(len(s)):
		if s[i] in number_char:
			start=True
			num=num+s[i]
		elif start:
			break
	return 0 if len(num)==0 else int(num)

#字符串转浮点数 stof(xxx2.33dd)=2.33
def stof(s):
	if s is None: return 0
	s=s.replace(',','').replace(' ','')
	num=""
	start=False
	for i in range(len(s)):
		if s[i] in number_char:
			start=True
			num=num+s[i]
		elif s[i]=='.' and start:
			num=num+'.'
		elif start:
			break
	return 0 if len(num)==0 else float(num)

#日期转时间戳 2015-07-31 13:06:41	
def date2sec(date):
	fmt='%Y-%m-%d %H:%M:%S'
	if len(date)<=10: fmt='%Y-%m-%d'
	elif len(date)<=13: fmt='%Y-%m-%d %H'
	elif len(date)<=16: fmt='%Y-%m-%d %H:%M'
	
	sec=time.mktime(time.strptime(date,fmt))
	return int(sec*1000)

#时间戳转格式化日期 2015-7-31
def sec2date(sec):
	fmt='%Y-%m-%d'
	date=time.strftime(fmt,time.localtime(sec/1000))
	return date

#时间戳格式化时间 2015-07-31 13:06:01
def sec2datetime(sec):
	fmt='%Y-%m-%d %H:%M:%S'
	date=time.strftime(fmt,time.localtime(sec/1000))
	return date

#当前时间 
def now():
	return int(time.time()*1000)

#今天 如: 2015-07-31
def today():
	fmt='%Y-%m-%d'
	return time.strftime(fmt,time.localtime())

#从objectId中获取时间戳
def timestamp_from_objectid(objectid):
	result = 0
	try:
		result = int(time.mktime(objectid.generation_time.timetuple())*1000)+28800000
	except:
		pass
	return result

import hashlib
def md5(src):
	m2=hashlib.md5() 
	m2.update(src)
	return m2.hexdigest()

#########################  curl #######################################################

#抓取指定连接并返回pyquery对象	
def pq(url,param={}):
	body=curlBody(url,param)
	
	if body is None or len(body)==0: return None
	
	charset=param.get('charset')
	if charset is not None:
		body=body.decode(charset,'ignore')
	elif 'charset=gbk' in body:
		body=body.decode('gbk','ignore')
	
	return PyQuery(body)

#抓取网页 仅抓取响应体		
def curlBody(url,param={}):
	ct = 5 if param.get('retry',True) else 1
	return tryRun(ct,tryCurlBody,url,param)

#抓取网页 包括响应头和响应体
def curlHtml(url,param={}):
	ct = 5 if param.get('retry',True) else 1
	return tryRun(ct,tryCurlHtml,url,param)
	
#抓取文件
def fetch(url,dest,param={}):
	ct = 5 if param.get('retry',True) else 1
	return tryRun(ct,tryFetch,url,dest,param)

#curl 初始化
def curlInit(url,param={}):
	curl=pycurl.Curl()
	curl.setopt(pycurl.URL,url)
	curl.setopt(pycurl.REFERER,url)
	curl.setopt(pycurl.CONNECTTIMEOUT,param.get('connect_timeout',90))
	curl.setopt(pycurl.TIMEOUT,param.get('timeout',300))
	curl.setopt(pycurl.SSL_VERIFYPEER,0)
	curl.setopt(pycurl.FOLLOWLOCATION,1)
	curl.setopt(pycurl.MAXREDIRS,5)
	curl.setopt(pycurl.ENCODING, 'gzip')
	curl.setopt(pycurl.NOSIGNAL, True)
	#curl.setopt(pycurl.VERBOSE,1)
	curl.setopt(pycurl.USERAGENT,'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0')
	
	curl.setopt(pycurl.COOKIEJAR,'cookie.txt')
	if param.get('cookie') is not None:
		curl.setopt(pycurl.COOKIE,cookie)
	else:
		curl.setopt(pycurl.COOKIEFILE,'cookie.txt')
		
	if param.get('post_data') is not None:
		curl.setopt(pycurl.POSTFIELDS, urllib.urlencode(param.get('post_data')))
		print urllib.urlencode(param.get('post_data'))
	
	return curl


#尝试执行N次
def tryRun(ct,func,*args):
	if ct<=0: return None
	
	try:
		res=func(*args)
		if res is not None:
			return res
	except Exception,e:
		#traceback.print_exc()
		pass
	
	time.sleep(0.5)	
	return tryRun(ct-1,func,*args)
	
def tryCurlBody(url,param={}):
	body=cStringIO.StringIO()
	
	curl=curlInit(url,param)
	curl.setopt(pycurl.WRITEFUNCTION, body.write)
	curl.perform()
	curl.close()
	
	return body.getvalue()

#抓取网页 包括响应头和响应体
def tryCurlHtml(url,param={}):
	body=cStringIO.StringIO()
	header=cStringIO.StringIO()
	
	curl=curlInit(url,param)
	curl.setopt(pycurl.HEADERFUNCTION, header.write)
	curl.setopt(pycurl.WRITEFUNCTION, body.write)
	curl.perform()
	curl.close()
	
	html={}
	html['header']=header.getvalue()
	html['body']=body.getvalue()
	
	return html

#抓取文件
def tryFetch(url,dest,param={}):
	fp=open(dest,'wb')
	
	curl=curlInit(url,param)
	curl.setopt(pycurl.WRITEDATA,fp)
	curl.perform()
	curl.close()
	
	fp.close()
	return True


#####################################  线程  ###################################################
#多线程
class LThreadPool:
	def __init__(self,q=1000000,w=5):
		self.tasks=Queue(maxsize=q)
		self.threads=[LThread(self.tasks,i) for i in range(w)]
	
	#添加任务
	def put(self,func,*args):
		self.tasks.put((func,args))
	
	#标记任务完成
	def finish(self):
		for t in self.threads:
			self.put('exit')
			self.put('exit')
	
	#检查线程状态
	def isAlive(self):
		for t in self.threads:
			if t.isAlive():
				return True
		return False	

#线程
class LThread(Thread):
	def __init__(self,tasks,seq):
		Thread.__init__(self)
		self.tasks=tasks
		self.seq=seq
		self.start()

	def run(self):
		while True:
			try:
				func,args=self.tasks.get(True,1)
				if 'exit'==func: break
				try:
					func(*args)
				except Exception,e:
					traceback.print_exc()
			except:
				pass


###############################  sendmail  ####################################

def sendMail(to,subject,content):
	try:
		smtpserver = 'smtp.163.com'
		sender = 'x@163.com'
		username = 'x'
		password = 'x'
		
		msg = MIMEText(content,'html','utf-8')
		msg['Subject'] = subject
		msg['From'] = sender
		if type(to) == type([]):
			msg['To'] = ','.join(to)
		else:
			msg['To'] = to
		
		smtp = smtplib.SMTP()
		smtp.connect(smtpserver)
		smtp.starttls()
		smtp.login(username, password)
		smtp.sendmail(sender, to, msg.as_string())
		smtp.quit()
	except Exception,e:
		traceback.print_exc()
		

####################################  base62  ################################################

ALPHABET = "0JhgREjBqHAw1C2IMvcNQzWF4TsDuyKxZtkb7GXL6lmOirp9eoY3na8VP5dUfS"

def base62_encode(num, alphabet=ALPHABET):
    """Encode a number in Base X

    `num`: The number to encode
    `alphabet`: The alphabet to use for encoding
    """
    if (num == 0): return alphabet[0]
    
    arr = []
    base = len(alphabet)
    while num:
        rem = num % base
        num = num // base
        arr.append(alphabet[rem])
    arr.reverse()
    return ''.join(arr)

def base62_decode(string, alphabet=ALPHABET):
    """Decode a Base X encoded string into the number

    Arguments:
    - `string`: The encoded string
    - `alphabet`: The alphabet to use for encoding
    """
    base = len(alphabet)
    strlen = len(string)
    num = 0

    idx = 0
    for char in string:
        power = (strlen - (idx + 1))
        num += alphabet.index(char) * (base ** power)
        idx += 1
    return num
    


###############################  最小堆  ##################################

#求topK, 越大越在上
class TopkHeap(object):
    def __init__(self, k):
        self.k = k
        self.data = []
        self.refData = {}

    def push(self, elem, ref):
        if len(self.data) < self.k:
            heapq.heappush(self.data, elem)
            self.refData[elem]=ref
        else:
            topk_small = self.data[0]
            if elem > topk_small:
                heapq.heapreplace(self.data, elem)
            	del self.refData[topk_small]
            	self.refData[elem]=ref

    def topK(self):
        return [self.refData[x] for x in reversed([heapq.heappop(self.data) for x in xrange(len(self.data))])]
