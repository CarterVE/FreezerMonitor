#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import Adafruit_MCP9808.MCP9808 as MCP9808
#import smtplib
from collections import deque
#from email.mime.text import MIMEText
import json
import urllib2
import random
import os
import cPickle as pickle

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

short_temp_buffer = deque(maxlen=3)     # 3 position buffer for the last 3 mins of temperature
long_temp_buffer = deque(maxlen=35)     # 35 position buffer to average previous 35 mins of temperature

for i in range(0,45):
    long_temp_buffer.append(0)

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

    req = urllib2.Request('https://hooks.slack.com/services/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')      #Watt lab slack - Freezer Monitor webhook link
    req.add_header('Content-Type', 'application/json')

    if override_msg == "":
        try:
            textChoice = random.randint(0,len(text_list) - 1)

            while last_post_selection == textChoice:
                textChoice = random.randint(0, len(text_list) - 1)

            msgString =  text_list[textChoice] + "\nThe temperature is currently: " + str(temp) + "˚C"

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
    short_temp_buffer.append(temp)
    long_temp_buffer.append(temp)

    if len(short_temp_buffer) == 1:

        time.sleep(120)

        pickled_script_runs = "pickled_script_runs"

        try:
            path_to_run_file = "/home/pi/run_freezer_monitor_file.txt"
            run_tester = open(path_to_run_file, "r")
            run_tester.close()
        except IOError:
            script_runs = 0

            file_pickled_script_runs = open(pickled_script_runs, "w")
            pickle.dump(script_runs, file_pickled_script_runs)
            file_pickled_script_runs.close()

            quit()

        try:
            file_pickled_script_runs = open(pickled_script_runs, "r")
            script_runs = pickle.load(file_pickled_script_runs)
            file_pickled_script_runs.close()
            # print script_runs

            if script_runs > 0:
                override_msg = "Freezer monitor is running! (Note: This may indicate a power interruption occurred.)"
                webhook_slack_post(short_temp_buffer[-1], override_msg)

            if script_runs > 1000:
                script_runs = 10       # Prevent overflow error, actual number of runtimes doesn't matter
            else:
                script_runs += 1

            # script_runs = 0        # For resetting script runs to prevent Slack POST on next run

            file_pickled_script_runs = open(pickled_script_runs, "w")
            pickle.dump(script_runs, file_pickled_script_runs)
            file_pickled_script_runs.close()

        except IOError as e:
            #print "IO Error({0}): {1}".format(e.errno, e.strerror)
            file_pickled_script_runs = open(pickled_script_runs, "w")

            #print "first run"
            script_runs = 1

            pickle.dump(script_runs, file_pickled_script_runs)
            file_pickled_script_runs.close()

        time.sleep(900)         # Wait after first starting, for temperature to fall


    if (mean(short_temp_buffer) - mean(long_temp_buffer[0:30])) > 5 and mean(short_temp_buffer) > -14 and mins_since_post > 45 and len(short_temp_buffer) > 1:     # Ensures there is a spike differing from last 45 minutes by at least 8 degrees and average is over -12 degC, mins since last post is over 10, and that buffer of temperatures is full, respectively
        webhook_slack_post(short_temp_buffer[-1], "")
        mins_since_post = 0

    elif (mean(short_temp_buffer) - mean(long_temp_buffer[0:30])) > 5 and mean(short_temp_buffer) > -14 and mins_since_post <= 45:   # Makes sure that app doesn't constantly post to slack, waits 5 minutes after last post (mins_since_post) before posting
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




