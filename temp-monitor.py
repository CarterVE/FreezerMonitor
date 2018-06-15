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

temp_buffer = deque(maxlen=5)  # 5 position buffer for the last 5 reads

mins_since_post = 100
last_post_selection = -1

text_list = ["Don't blame the messenger, but someone left the freezer door open.",
             "Panic! Someone left the freezer open.",
             "I'm meeeeelting... close the freezer.",
             "There goes my snowman! Close the freezer.",
             "♫ Let it go, let it goooo ♫ And by it, I mean the freezer door when you close it.",
             "You know, there are cheaper ways to get air conditioning. Close the freezer door.",
             "Drip...drip...drip... That's the sound of everything in the freezer melting. Close the door!",
             "<Insert clever message about the freezer door bring open> ...Yeah I got lazy on this one.",
             "It's called a freezer, not a melter! Close the door!",
             "Shiver me timbers! The freezer door is swinging in the breeze!"
             ]

error_encountered = 0

def mean(l):  # The world's silliest function
    return sum(l) / len(l)


def buf_to_str(buf):
    string = ""
    for el in buf:
        string = string + str(el) + ", "
    return string

def webhook_slack_post(temp, override_msg):
    global error_encountered
    global last_post_selection

    req = urllib2.Request('https://hooks.slack.com/services/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')
    req.add_header('Content-Type', 'application/json')

    if override_msg == "":
        try:
            textChoice = random.randint(0,len(text_list) - 1)

            while last_post_selection == textChoice:
                textChoice = random.randint(0, len(text_list) - 1)

            msgString = text_list[textChoice] + "\nThe temperature is currently: " + str(temp) + "˚C"

            text = {

                'text' : msgString

            }

            last_post_selection = textChoice        # Records which message was posted, so message is not repeated twice (might be annoying)

            response = urllib2.urlopen(req, json.dumps(text))
        except:
            error_encountered = 1
    else:
        msgString = override_msg + "\nThe temperature is currently: " + str(temp) + "˚C"

        text = {

            'text': msgString

        }

        response = urllib2.urlopen(req, json.dumps(text))


def check_temp():
    global mins_since_post
    global error_encountered

    temp = sensor.readTempC()
    temp_buffer.append(temp)

    if len(temp_buffer) == 1:

        override_msg = "Freezer monitor is up and running! (Note: This may indicate a power interruption occurred.)"
        webhook_slack_post(temp_buffer[-1], override_msg)

        time.sleep(600)         # Wait after first starting, for temperature to fall


    if mean(temp_buffer) > -10 and mins_since_post > 15 and len(temp_buffer) > 4:     # Ensures average is over -10 degC, mins since last post is over 10, and that buffer of temperatures is full, respectively
        webhook_slack_post(temp_buffer[-1], "")
        mins_since_post = 0

    elif mean(temp_buffer) > -10 and mins_since_post <= 15:   # Makes sure that app doesn't constantly post to slack, waits 5 minutes after last post (mins_since_post) before posting
        mins_since_post += 1
        if mins_since_post > 60000:
            mins_since_post = 100        # Ensures that integer doesn't overflow if freezer doesn't go over threshold for long time (unlikely, but possible)

    else:
        mins_since_post += 1
        if mins_since_post > 6000:
            mins_since_post = 100


    time.sleep(60)


while True:
    check_temp()




