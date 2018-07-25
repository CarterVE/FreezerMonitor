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
from datetime import datetime, timedelta
import itertools
import csv

#***************************************
#********* FREEZER MONITOR  ************
#***************************************

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

for i in range(0,35):
    long_temp_buffer.append(0)

mins_since_post = 15
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

def dt_adjust(dt):
    delta = timedelta(hours=-4)
    return dt + delta

def webhook_slack_post(temp, override_msg):
    global error_encountered
    global last_post_selection

    req = urllib2.Request('https://hooks.slack.com/services/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')      #Watt lab slack - Freezer Monitor webhook link
    req.add_header('Content-Type', 'application/json')

    if override_msg == "":
        try:
            textChoice = random.randint(0,len(text_list) - 1)   #Generate random number N such that a <= N <= b (selects dialogue from list)

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

    pickled_script_runs = "pickled_script_runs"

    try:
        path_to_run_file = "/home/pi/run_freezer_monitor_file.txt"
        run_tester = open(path_to_run_file, "r")
        run_tester.close()
    except IOError:
        script_runs = 0
        file_pickled_script_runs = open(pickled_script_runs, "w")
        pickle.dump(script_runs, file_pickled_script_runs)           # Resets script runs if the file run_freezer_monitor_file.txt does not exist
        file_pickled_script_runs.close()
        print "Script runs reset, Freezer Monitor quitting now..."
        quit()                  # Quits the application if the file run_freezer_monitor_file.txt does not exist

    temp = sensor.readTempC()
    short_temp_buffer.append(temp)
    long_temp_buffer.append(temp)
    long_temp_buffer_fThirty = list(itertools.islice(long_temp_buffer, 0, 30))

    path_to_status_file = "/home/pi/FreezerMonitor_Status.txt"
    date_time_gmt = datetime.today()
    date_time_adj = dt_adjust(date_time_gmt)

    txt = "FreezerMonitor last took a reading at: " + str(date_time_adj) + "\nThe temperature was: " + str(temp) + "°C" \
        "\n\nIf this reading was taken within the last minute, FreezerMonitor is currently running. (Note: Hour may be incorrect based on DST/time zone)." \
        "\nTo see/graph last 24 hours of measurements, open FreezerTemperatures_Last24Hours.csv" \
        "\n\nTo stop FreezerMonitor, rename run_freezer_monitor_file.txt to dont_run_freezer_monitor_file.txt, and reboot." \
        "\nIf file is not named run_freezer_monitor_file.txt, FreezerMonitor will not run.\n"

    with open(path_to_status_file, 'w') as f:
        f.write(txt)
    #os.chmod(path_to_file, 0o777)

    path_to_last24hour_file = "/home/pi/FreezerTemperatures_Last24Hours.csv"
    with open(path_to_last24hour_file, "a+") as f:
        data = list(csv.reader(f))

    with open(path_to_last24hour_file, "w") as f:
        writer = csv.writer(f)
        for row in data:
            if row[0] > str(date_time_adj + timedelta(days=-1)):
                writer.writerow(row)
        writer.writerow([date_time_adj, temp])


    if len(short_temp_buffer) == 1:

        try:
            file_pickled_script_runs = open(pickled_script_runs, "r")
            script_runs = pickle.load(file_pickled_script_runs)
            file_pickled_script_runs.close()
            # print script_runs

            if script_runs > 0:
                override_msg = "Freezer monitor is running! (This may indicate a power interruption occurred.)"
                webhook_slack_post(short_temp_buffer[-1], override_msg)

            if script_runs > 1000:
                script_runs = 10       # Prevent overflow error, actual number of runtimes doesn't matter
            else:
                script_runs += 1

            # script_runs = 0        # For resetting script runs to prevent Slack POST on next run

            file_pickled_script_runs = open(pickled_script_runs, "w")
            pickle.dump(script_runs, file_pickled_script_runs)
            file_pickled_script_runs.close()

        except IOError:
            #print "IO Error({0}): {1}".format(e.errno, e.strerror)
            file_pickled_script_runs = open(pickled_script_runs, "w")
            script_runs = 1
            pickle.dump(script_runs, file_pickled_script_runs)
            file_pickled_script_runs.close()

        while temp > -14:       # Waits for the temperature to fall after starting, unless this is not necessary
            time.sleep(60)
            temp = sensor.readTempC()


    elif ((mean(short_temp_buffer) - mean(long_temp_buffer_fThirty)) > 5 and mean(short_temp_buffer) > -12 and mins_since_post > 45) or (mean(short_temp_buffer) > -8 and mins_since_post > 45):     # Ensures there is a spike differing from last 45 minutes by at least 8 degrees and average is over -12 degC, mins since last post is over 10, and that buffer of temperatures is full, respectively
        webhook_slack_post(short_temp_buffer[-1], "")
        mins_since_post = 0

    else:                               # Makes sure that app doesn't constantly post to slack, waits 45 minutes after last post (mins_since_post) before posting
        mins_since_post += 1
        if mins_since_post > 6000:
            mins_since_post = 100       # Ensures that integer doesn't overflow if freezer doesn't go over threshold for long time (unlikely, but possible)

    time.sleep(60)

time.sleep(60)

while True:
    check_temp()




