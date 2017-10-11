# -*- coding: utf-8 -*-
"""
Created on 2017-09-10

@author: VictoriaChou
"""
import os
import json
import cookielib
import urllib
import urllib2
import re
import random
import time
import socket
from bs4 import BeautifulSoup as BS

import dataEncode
import myconf
from Logger import LogClient

import sys
reload(sys)
sys.setdefaultencoding('utf8')

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
        self.status = False
        self.access_token = None
        self.app_key = None
        self.initParams()
        self.timeout = 3
        socket.setdefaulttimeout(3)
        self.tryTimes = 8

    def initParams(self):
        self.logger = LogClient().createLogger('SinaWSpider', myconf.log_out_path)
        self.headers = myconf.headers
        self.access_token = myconf.access_token
        self.app_key = myconf.app_key
        return self

    def setAccount(self, username, password):
        self.username = username
        self.password = password
        return self
    
    def setPostData(self):
        self.servertime, self.nonce, self.pubkey, self.rsakv = dataEncode.get_prelogin_info()
        self.post_data = dataEncode.encode_post_data(self.username, self.password, self.servertime, self.nonce, self.pubkey, self.rsakv)
        return self
    
    def switchUserAgent(self, enableAgent=True):
        user_agent = random.choice(myconf.agent_list)
        self.headers["User-Agent"] = user_agent
        return self

    def switchUserAccount(self, userlist):
        is_login = False
        while not is_login: 
            self.switchUserAgent()
            self.logger.info("User-Agent is: " + self.headers["User-Agent"])
            user = random.choice(userlist).split("|")
            self.logger.info("logining with user: " + user[0])
            session = self.login(user[0], user[1])
            if not session.status:
                self.logger.info("Cannot login to sina!")
                continue
            is_login = True
        return self
    
    def enableCookie(self, enableProxy=False):
        self.cookiejar = cookielib.LWPCookieJar()  # 建立COOKIE
        cookie_support = urllib2.HTTPCookieProcessor(self.cookiejar)
        opener = urllib2.build_opener(cookie_support, urllib2.HTTPHandler)
        urllib2.install_opener(opener)
        return self
    
    def login(self, username=None, password=None):
        self.logger.info("Start to login...")
        self.setAccount(username, password) 
        self.setPostData()
        self.enableCookie(enableProxy=True)
        login_url = r'https://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.15)'
        headers = self.headers
        try:  
            request = urllib2.Request(login_url, urllib.urlencode(self.post_data), headers)
            resText = urllib2.urlopen(request).read()
            jsonText = json.loads(resText)
            if jsonText["retcode"] == "0":
                self.logger.info("Login success!")
                self.status = True
                cookies = ';'.join([cookie.name + "=" + cookie.value for cookie in self.cookiejar])
                headers["Cookie"] = cookies
            else:
                self.logger.error("Login Failed --> " + jsonText["reason"])
        except Exception, e:
            self.logger.error("Login Failed2! --> " + str(e))
        self.headers = headers
        return self
    
    def openURL(self, url, data=None, tryTimes=1):
        text = ""
        if tryTimes < self.tryTimes:
            try:
                self.logger.info("open url %s times: %s" %(str(tryTimes), url))
                req = urllib2.Request(url, data=data, headers=self.headers)
                text = urllib2.urlopen(req, timeout=1).read()
            except Exception, e:
                self.logger.error("openURL error, " + str(e))
                self.switchUserAccount(myconf.userlist)
                text = self.openURL(url, data=data, tryTimes = tryTimes+1)
        return text
    
    def output(self, content, out_path, save_mode="w"):
        self.logger.info("Save page to: " + out_path)
        prefix = os.path.dirname(out_path)
        if not os.path.exists(prefix):
            os.makedirs(prefix)
        fw = open(out_path, save_mode)
        fw.write(content)
        fw.close()
        return self
    
    def getUserInfos(self, uid):
        url_app = "http://weibo.cn/%s/info" %uid
        text_app = self.openURL(url_app)
        soup_app = unicode(BS(text_app, "html.parser"))
        nickname = re.findall(u'\u6635\u79f0[:|\uff1a](.*?)<br', soup_app)  # 昵称
        gender = re.findall(u'\u6027\u522b[:|\uff1a](.*?)<br', soup_app)  # 性别
        address = re.findall(u'\u5730\u533a[:|\uff1a](.*?)<br', soup_app)  # 地区（包括省份和城市）
        birthday = re.findall(u'\u751f\u65e5[:|\uff1a](.*?)<br', soup_app)  # 生日
        desc = re.findall(u'\u7b80\u4ecb[:|\uff1a](.*?)<br', soup_app)  # 简介
        sexorientation = re.findall(u'\u6027\u53d6\u5411[:|\uff1a](.*?)<br', soup_app)  # 性取向
        marriage = re.findall(u'\u611f\u60c5\u72b6\u51b5[:|\uff1a](.*?)<br', soup_app)  # 婚姻状况
        homepage = re.findall(u'\u4e92\u8054\u7f51[:|\uff1a](.*?)<br', soup_app)  #首页链接
        app_page = "http://weibo.cn/%s" %uid
        text_homepage = self.openURL(app_page)
        soup_home = unicode(BS(text_homepage, "html.parser"))
        tweets_count = re.findall(u'\u5fae\u535a\[(\d+)\]', soup_home)
        follows_count = re.findall(u'\u5173\u6ce8\[(\d+)\]', soup_home)
        fans_count = re.findall(u'\u7c89\u4e1d\[(\d+)\]', soup_home)
        url_web = "http://weibo.com/%s/info" %uid
        text_web = self.openURL(url_web)
        reg_date = re.findall(r"\d{4}-\d{2}-\d{2}", text_web)
        tag_url = "http://weibo.cn/account/privacy/tags/?uid=%s" %uid
        text_tag = self.openURL(tag_url)      
        soup_tag = BS(text_tag, "html.parser")
        res = soup_tag.find_all('div', {"class":"c"})
        tags = "|".join([elem.text for elem in res[2].find_all("a")])
        
        userinfo = {}
        userinfo["uid"] = uid
        userinfo["nickname"] = nickname[0] if nickname else ""
        userinfo["gender"] = gender[0] if gender else ""
        userinfo["address"] = address[0] if address else ""
        userinfo["birthday"] = birthday[0] if birthday else ""
        userinfo["desc"] = desc[0] if desc else ""
        userinfo["sex_orientation"] = sexorientation[0] if sexorientation else ""
        userinfo["marriage"] = marriage[0] if marriage else ""
        userinfo["homepage"] = homepage[0] if homepage else ""
        userinfo["tweets_count"] = tweets_count[0] if tweets_count else "0"
        userinfo["follows_count"] = follows_count[0] if follows_count else "0"
        userinfo["fans_count"] = fans_count[0] if fans_count else "0"
        userinfo["reg_date"] = reg_date[0] if reg_date else ""
        userinfo["tags"] = tags if tags else ""
        return userinfo

    def getUserFollows(self, uid, params="page=1"):
        time.sleep(2)
        self.switchUserAgent()
        url = "http://weibo.cn/%s/follow?rightmod=1&wvr=6/%s" %(uid, params)
        text = self.openURL(url)
        soup = BS(text, "html.parser")
        res = soup.find_all('table')
        reg_uid = r"uid=(\d+)&" 
        follows = {"uid": uid, "follow_ids": list(set([y for x in [re.findall(reg_uid, str(elem)) for elem in res] for y in x ]))}
        next_url = re.findall('<div><a href="(.*?)">下页</a>&nbsp', text) #匹配"下页"内容
        if len(next_url) != 0:
            url_params = next_url[0].split("?")[-1] 
            if url_params != params:
                follows['follow_ids'].extend(self.getUserFollows(uid, params=url_params)["follow_ids"]) #将结果集合并
        return follows
    
    def getUserFans(self, uid, params="page=1"):
        time.sleep(2)
        self.switchUserAgent()
        url = r"http://weibo.cn/%s/fans?%s" %(uid, params)
        text = self.openURL(url)
        soup = BS(text, "html.parser")
        res = soup.find_all('table')
        reg_uid = r"uid=(\d+)&"
        fans = {"uid": uid, "fans_ids": list(set([y for x in [re.findall(reg_uid, str(elem)) for elem in res] for y in x ]))}
        next_url = re.findall('<div><a href="(.*?)">下页</a>&nbsp', text) #匹配"下页"内容
        if len(next_url) != 0:
            url_params = next_url[0].split("?")[-1]
            if url_params != params:
                fans['fans_ids'].extend(self.getUserFans(uid, params=url_params)["fans_ids"]) #将结果集合并
        return fans
        
    def getUserTweets(self, uid, tweets_all, params="page=1"):
        self.switchUserAccount(myconf.userlist)
        url = r"http://weibo.cn/%s/profile?%s" %(uid, params)
        text = self.openURL(url)
        soup = BS(text, "html.parser")
        res = soup.find_all("div", {"class":"c"})
        tweets_list = []
        for elem in res:
            tweets = {}
            unicode_text = unicode(elem)
            sub_divs = elem.find_all("div")
            today = time.strftime('%Y-%m-%d',time.localtime(time.time()))
            if len(sub_divs) in [1, 2, 3]:
                tweets["uid"] = uid
                tweets["reason"] = "null"
                tweets["content"] = elem.find("span", {"class": "ctt"}).text
                soup_text = elem.find("span", {"class": "ct"}).text
                created_at = re.findall("\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d", unicode(soup_text))
                post_time = re.findall("\d\d:\d\d", unicode(soup_text))
                split_text = unicode(soup_text).split(u"\u5206\u949f\u524d")
                if not created_at:
                    created_at = re.findall(u"\d\d\u6708\d\d\u65e5 \d\d:\d\d", unicode(soup_text))
                    tweets["created_at"] = time.strftime("%Y-",time.localtime()) + unicode(created_at[0]).replace(u"\u6708", "-").replace(u"\u65e5", "") + ":00"
                    tweets["source"] = soup_text.split(created_at[0])[-1].strip(u"\u00a0\u6765\u81ea")
                elif created_at:
                    tweets["created_at"] = unicode(created_at[0]).replace(u"\u6708", "-").replace(u"\u65e5", "")
                    tweets["source"] = soup_text.split(created_at[0])[-1].strip(u"\u00a0\u6765\u81ea")
                elif post_time:
                    tweets["created_at"] = today + " " + post_time[0] + ":00"
                    tweets["source"] = soup_text.split(post_time[0])[-1].strip(u"\u00a0\u6765\u81ea")
                elif len(split_text) == 2:
                    tweets["created_at"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() - int(split_text[0])*60))
                    tweets["source"] = split_text[-1].strip(u"\u00a0\u6765\u81ea")
                tweets["like_count"] = re.findall(u'\u8d5e\[(\d+)\]', unicode_text)[-1]
                tweets["repost_count"] = re.findall(u'\u8f6c\u53d1\[(\d+)\]', unicode_text)[-1]
                tweets["comment_count"] = re.findall( u'\u8bc4\u8bba\[(\d+)\]', unicode_text)[-1]
            if len(sub_divs) == 0:
                pass
            elif len(sub_divs) == 1:
                tweets["type"] = "original_text"
            elif len(sub_divs) == 2:
                tweets["type"] = "original_image"
                #根据cmt的存在判断是否为转发的文字和原创的图文说说
                cmt = elem.find_all("span", {"class": "cmt"})
                if cmt: 
                    tweets["type"] = "repost_text"
                    tweets["reason"] = re.findall("</span>(.*?)<a", str(sub_divs[1]))[0]
            elif len(sub_divs) == 3:
                tweets["type"] = "repost_image"
                tweets["reason"] = re.findall("</span>(.*?)<a", str(sub_divs[2]))[0]
            else:
                self.logger.error("parse error")
                pass
            if tweets:
                tweets_list.append(json.dumps(tweets))
        tweets_all.extend(tweets_list)

        next_url = re.findall('<div><a href="(.*?)">下页</a>&nbsp', text) #匹配"下页"内容
        if len(next_url) != 0 and len(tweets_all) < 200:
            url_params = next_url[0].split("?")[-1]
            if url_params != params:
                self.getUserTweets(uid, tweets_all, params=url_params)
        return tweets_list
