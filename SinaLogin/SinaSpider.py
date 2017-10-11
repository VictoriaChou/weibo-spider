# -*- coding: utf-8 -*-
"""
Created on 2017-09-10

@author: VictoriaChou
"""
import os
import getpass
import json
import requests
import cookielib
import urllib
import urllib2
import gzip
import StringIO
import time

import dataEncode
from Logger import LogClient

class SinaClient(object):
    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password
        self.servertime = None
        self.nonce = None
        self.pubkey = None
        self.rsakv = None
        self.post_data = None
        self.headers = {}
        self.session = None   
        self.cookiejar = None
        self.logger = None        
        self.state = False
        self.initParams()

    def initParams(self):
        self.logger = LogClient().createLogger('SinaClient', 'out/log_' + time.strftime("%Y%m%d", time.localtime()) + '.log')
        self.headers = dataEncode.headers
        return self
    
    def setAccount(self, username, password):
        self.username = username
        self.password = password
        return self
    
    def setPostData(self):
        self.servertime, self.nonce, self.pubkey, self.rsakv = dataEncode.get_prelogin_info()
        self.post_data = dataEncode.encode_post_data(self.username, self.password, self.servertime, self.nonce, self.pubkey, self.rsakv)
        return self
        
    def login(self, username=None, password=None):
        self.setAccount(username, password) 
        self.setPostData()
        login_url = r'https://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.15)'
        session = requests.Session()
        response = session.post(login_url, data=self.post_data)
        json_text = response.content.decode('gbk')
        res_info = json.loads(json_text)
        try:
            if res_info["retcode"] == "0":
                self.logger.info("Login success!")
                self.state = True
                cookies = session.cookies.get_dict()
                cookies = [key + "=" + value for key, value in cookies.items()]
                cookies = "; ".join(cookies)
                session.headers["Cookie"] = cookies
            else:
                self.logger.error("Login Failed! | " + res_info["reason"])
        except Exception, e:
            self.logger.error("Loading error --> " + e)
        self.session = session
        return session
    
    def enableCookie(self, enableProxy=False):
        self.cookiejar = cookielib.LWPCookieJar()
        cookie_support = urllib2.HTTPCookieProcessor(self.cookiejar)
        opener = urllib2.build_opener(cookie_support, urllib2.HTTPHandler)
        urllib2.install_opener(opener)
    
    def login2(self, username=None, password=None):
        self.logger.info("Start to login...")
        self.setAccount(username, password) 
        self.setPostData()
        self.enableCookie()
        login_url = r'https://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.15)'
        headers = self.headers
        request = urllib2.Request(login_url, urllib.urlencode(self.post_data), headers)
        resText = urllib2.urlopen(request, timeout=1).read()
        try:        
            jsonText = json.loads(resText)
            if jsonText["retcode"] == "0":
                self.logger.info("Login success!")
                self.state = True
                cookies = ';'.join([cookie.name + "=" + cookie.value for cookie in self.cookiejar])
                headers["Cookie"] = cookies
            else:
                self.logger.error("Login Failed --> " + jsonText["reason"])
        except Exception, e:
            print e
        self.headers = headers
        return self
    
    def openURL(self, url, data=None):
        req = urllib2.Request(url, data=data, headers=self.headers)
        text = urllib2.urlopen(req,timeout=1).read()
        return text
    
def testLogin():
    client = SinaClient()
    username = raw_input("Please input username: ")
    password = getpass.getpass("Please input your password: ")   
    session = client.login(username, password)
    follow = session.post("http://weibo.cn/1669282904/follow").text.encode("utf-8")
    client.output(follow, "out/follow.html")

if __name__ == '__main__':
    testLogin()
    