#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import Adafruit_MCP9808.MCP9808 as MCP9808
import smtplib
from collections import deque
#from email.mime.text import MIMEText
import json
import urllib2
import random
import os
import cPickle as pickle
from datetime import datetime, timedelta
import csv

# print '**************************************'
# print '-----EXECUTING TEMP SENSOR SCRIPT-----'
# print '**************************************'

# Script created using scripts from:
# http://www.billconnelly.net/?p=375
# AND
# https://www.raspberrypi.org/magpi/raspberry-pi-fridge-monitor/
#   ( https://github.com/simonmonk/pi_magazine/blob/master/07_fridge_monitor/fridge_monitor.py )

# Connect to i2c sensor with default pins (SCL=P9_19, SDA = P9_20)
sensor = MCP9808.MCP9808()

# Initialize sensor
sensor.begin()

temp_buffer = deque(maxlen=5)  # 5 position buffer for the last 5 reads

mins_since_post = 100
last_post_selection = -1

error_encountered = 0

def mean(l):  # The world's silliest function
    return sum(l) / len(l)

def buf_to_str(buf):
    string = ""
    for el in buf:
        string = string + str(el) + ", "
    return string

def dt_adjust(dt):
    delta = timedelta(hours=-4)
    return dt + delta

def check_temp():
    temp = sensor.readTempC()
    #temp_buffer.append(temp)

    path_to_file = "/home/pi/Freezer_Temperatures.csv"
    path_to_file_overflow = "/home/pi/Freezer_Temperatures_Overflow.csv"
    #temp_file = open(path_to_file, "a")

    date_time_gmt = datetime.today()
    date_time_adj = dt_adjust(date_time_gmt)

    date_time_monday = datetime(2018, 06, 25, 00, 00, 00)
    date_time_tuesday = datetime(2018, 06, 26, 00, 00, 00)

    if date_time_adj > date_time_monday and date_time_adj < date_time_tuesday:
        with open(path_to_file, 'a') as f:
            writer = csv.writer(f)
            writer.writerow([date_time_adj, temp])
    elif date_time_adj > date_time_tuesday:
        with open(path_to_file_overflow, 'a') as fo:
            writer = csv.writer(fo)
            writer.writerow([date_time_adj, temp])

    time.sleep(60)


while True:
    check_temp()




