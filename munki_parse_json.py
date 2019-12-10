#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 22 17:43:26 2019
TODO:
    - output formatting
    - refactoring to be future proof, not hard-coded
@author: cecky
"""
import sys
import json
import time

# filename = sys.argv[1]

def sortfunc(r):
    return "MissingCompanyName" if r[0] == None else r[0].split("/")[1]

with open("json_data.json", "r") as fd:
    mydata = json.loads(fd.read())["data"]
    mydata.sort(key=sortfunc)
    for rec in mydata:
        if (
            # <= 30G local storage
            (rec[6] == "/" and int(rec[7]) <= 32212254720)
            # smart errors
            or (rec[8] != None and int(rec[8]) > 0)
            # <= 75% battery
            or (rec[9] != None and int(rec[9]) <= 75)
            # timestamp > 90 days
            or (rec[10] != None and ((time.time() - int(rec[10]))/86400 > 90))
            ):
            print("SLA -",
                  "MissingCompanyName" if rec[0] == None else rec[0].split("/")[1],
                  "\n",
                  #
                  "Serial -",
                  rec[1],
                  "\n"
                  #
                  "Model -",
                  rec[2],
                  "\n",
                  #
                  "Device type -",
                  rec[3],
                  "\n",
                  #
                  "Hostname -",
                  rec[4],
                  "\n",
                  #
                  "Name and surname -",
                  "NoUserName" if rec[5] == None else rec[5],
                  "\n",
                  #
                  "Mountpoints -",
                  "NoMountPoint" if rec[6] == None else rec[6],
                  "\n",
                  #
                  "Free space (GB) -",
                  "NoFreeSpaceData" if rec[7] == None else float(rec[7])/1073741824.0,
                  "\n",
                  #
                  "SMART -",
                  "NoSmartData" if rec[8] == None else int(rec[8]),
                  "\n",
                  #
                  "Battery (%) -",
                  "NoBatteryData" if rec[9] == None else int(rec[9]),
                  "\n",
                  #
                  "Last checkin -",
                  "NoTimestamp" if rec[10] == None else time.ctime(int(rec[10])),
                  "\n",
                  "------",
                  "\n\n"
                  )
