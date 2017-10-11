# -*- coding: utf-8 -*-
"""
Created on 2017-09-10

@author: VictoriaChou
"""
import os
import logging  

class LogClient(object):
    def __init__(self):
        self.logger = None

    def createLogger(self, logger_name, log_file):
        prefix = os.path.dirname(log_file)
        if not os.path.exists(prefix):
            os.makedirs(prefix)
        logger = logging.getLogger(logger_name)  
        logger.setLevel(logging.INFO)  
        fh = logging.FileHandler(log_file)  
        ch = logging.StreamHandler()  
        formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')  
        fh.setFormatter(formatter)  
        ch.setFormatter(formatter)  
        logger.addHandler(fh)  
        logger.addHandler(ch)
        self.logger = logger
        return self.logger