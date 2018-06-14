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

temp_buffer = deque(maxlen=10)  # 10 position buffer for the last 10 reads

mins_since_post = 15

text_list = ["Don't blame the messenger, but someone left the freezer door open.",
             "Panic! Someone left the freezer open.",
             "I'm meeeeelting... close the freezer.",
             "There goes my snowman! Close the freezer.",
             "♫ Let it go, let it goooo ♫ And by it, I mean the freezer door when you close it.",
             "You know, there are cheaper ways to get air conditioning. Close the freezer door.",
             "Drip...drip...drip... That's the sound of everything in the freezer melting. Close the door!",
             "<Insert clever message about the freezer door bring open> ...Yeah I got lazy on this one.",
             "It's called a freezer, not a melter! Close the door!"
             ]

error_encountered = 0

def mean(l):  # The world's silliest function
    return sum(l) / len(l)


def buf_to_str(buf):
    string = ""
    for el in buf:
        string = string + str(el) + ", "
    return string

def webhook_slack_post(temp):
    global error_encountered

    try:
        req = urllib2.Request('https://hooks.slack.com/services/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')
        req.add_header('Content-Type', 'application/json')

        textChoice = random.randint(0,len(text_list) - 1)

        msgString = text_list[textChoice] + "\nThe temperature is currently: " + str(temp) + "˚C"

        text = {

            'text' : msgString

        }

        response = urllib2.urlopen(req, json.dumps(text))
    except:
        error_encountered = 1


def check_temp():
    global mins_since_post
    global error_encountered

    temp = sensor.readTempC()
    temp_buffer.append(temp)

    if mean(temp_buffer) > -10 and mins_since_post > 10:
        webhook_slack_post(temp_buffer[0])
        mins_since_post = 0

    elif mean(temp_buffer) > -10 and mins_since_post < 10:   # Makes sure that app doesn't constantly post to slack, waits 5 minutes after last post (mins_since_post) before posting
        mins_since_post = mins_since_post + 1
        if mins_since_post > 60000:
            mins_since_post = 100        # Ensures that integer doesn't overflow if freezer doesn't go over threshold for long time (unlikely, but possible)

    time.sleep(60)


while True:
    check_temp()




