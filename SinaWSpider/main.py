# -*- coding: utf-8 -*-
"""
Created on 2017-09-10

@author: VictoriaChou
"""

import SinaSpider as slib
import myconf
import json
import random
import pymongo
from MongoQueue import MongoQueue

#初始化MongoDB
def initMongoClient():
    uri = "mongodb://{username}:{password}@{host}:{port}/{db_name}?authMechanism=MONGODB-CR".format(username="*******",
                                                                       password="*******",
                                                                       host="localhost",
                                                                       port=27017,
                                                                       db_name="sina_db")
    conn = pymongo.MongoClient(uri)
    print "Connected to Mongodb!"
    db = conn.sina_db
    return db

def spiderSinaData(session, db, uid):
    uidlist = [] 
    try:
        collection = db.userinfo
        if collection.find_one({"uid": uid}) == None:
            session.switchUserAccount(myconf.userlist)        
            userinfo = session.getUserInfos(uid)    
            session.output(json.dumps(userinfo), "output/%s/%s_info.json" %(uid, uid)) 
            collection.insert(userinfo)
        
        session.switchUserAccount(myconf.userlist)
        follows = session.getUserFollows(uid)
        session.output(json.dumps(follows), "output/%s/%s_follows.json" %(uid, uid)) 
        collection = db.follows
        if collection.find_one({"uid": uid}) == None:    
            collection.insert(follows)
            
        session.switchUserAccount(myconf.userlist)
        fans = session.getUserFans(uid)
        session.output(json.dumps(fans), "output/%s/%s_fans.json" %(uid, uid)) 
        collection = db.fans
        if collection.find_one({"uid": uid}) == None:    
            collection.insert(fans)
        
        uidlist = list(set(uidlist).union(fans["fans_ids"]).union(follows["follow_ids"]))

        user_tweets = []
        session.getUserTweets(uid, user_tweets)
        collection = db.tweets
        for elem in user_tweets:
            if collection.find_one(elem) == None:
                collection.insert(json.loads(elem))
    except Exception,e:
        session.logger.error("spiderSinaData Exception! -->" + str(e) )
        return uidlist
    return uidlist

def main():
    mongo_queue = MongoQueue()
    db = mongo_queue.db
    client = slib.SinaClient()
    session = client.switchUserAccount(myconf.userlist)
    uid = "6167535231"
    mongo_queue.push(uid)          
    cnt = 0
    while True:
        cnt += 1
        uid = mongo_queue.pop()
        if uid == None:
            session.logger.info("All of mongo_queue is scraped!")
            break
        session.logger.info("scraping " + str(cnt) + "th user, uid is " + uid)
        uidlist = spiderSinaData(session, db, uid)
        for wait_uid in uidlist:
            mongo_queue.push(wait_uid)
        mongo_queue.complete(uid)
        

# 多进程，跑满cpu
def muti_process_main():
    import multiprocessing
    cpu_num = multiprocessing.cpu_count() 
    processes = []
    for i in range(1):
        pro = multiprocessing.Process(target=main)
        pro.start()
        processes.append(pro)
    for p in processes:
        p.join()

if __name__ == '__main__':
    muti_process_main()
    