# -*- coding: utf-8 -*-
"""
Created on 2017-09-10

@author: VictoriaChou
"""
import base64
import rsa
import binascii
import requests
import json
import re

def encode_username(username):
    return base64.encodestring(username)[:-1]
    
def encode_password(password, servertime, nonce, pubkey):
    rsaPubkey = int(pubkey, 16)
    RSAKey = rsa.PublicKey(rsaPubkey, 65537) #创建公钥
    codeStr = str(servertime) + '\t' + str(nonce) + '\n' + str(password) #根据js拼接方式构造明文
    pwd = rsa.encrypt(codeStr, RSAKey)  #使用rsa进行加密
    return binascii.b2a_hex(pwd)

def get_prelogin_info():
    url = r'http://login.sina.com.cn/sso/prelogin.php?entry=weibo&callback=sinaSSOController.preloginCallBack&su=&rsakt=mod&client=ssologin.js(v1.4.18)'
    html = requests.get(url).text
    jsonStr = re.findall(r'\((\{.*?\})\)', html)[0]
    data = json.loads(jsonStr)
    servertime = data["servertime"]
    nonce = data["nonce"]
    pubkey = data["pubkey"]
    rsakv = data["rsakv"]
    return servertime, nonce, pubkey, rsakv

def encode_post_data(username, password, servertime, nonce, pubkey, rsakv):
    su = encode_username(username)
    sp = encode_password(password, servertime, nonce, pubkey)
    post_data = {
        "cdult" : "3",
        "domain" : "sina.com.cn",
        "encoding" : "UTF-8",
        "entry" : "sso",
        "from" : "null",
        "gateway" : "1",
        "pagerefer" : "",
        "prelt" : "0",
        "returntype" : "TEXT",
        "savestate" : "30",
        "service" : "sso",
        "sp" : password,
        "sr" : "1366*768",
        "su" : su,
        "useticket" : "0",
        "vsnf" : "1"
    }    
    
    return post_data
