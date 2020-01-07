#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 22 17:43:26 2019
TODO:
    - fancy output formatting
    - refactoring to be future proof
@author: cecky
"""
import sys
import json
import time

# filename = sys.argv[1]

unwanted = {"logicworks","logicworks_test","triad","sw"}

def sortfunc(r):
    return "x" if r[0] == None else r[0].split("/")[1]

with open("json_data.json", "r") as fd:
    mydata = json.loads(fd.read())["data"]
    mydata.sort(key=sortfunc)
    for rec in mydata:
        company = "unknown" if rec[0] == None else rec[0].split("/")[1]
        if  ((company not in unwanted) and (rec[6] == "/") and
            (
            # <= 30G local storage
            (rec[6] == "/" and int(rec[7]) <= 32212254720)
            # smart errors
            or (rec[8] != None and int(rec[8]) > 0)
            # <= 75% battery
            or (rec[9] != None and int(rec[9]) <= 75)
            # timestamp > 90 days
            or (rec[10] != None and ((time.time() - int(rec[10]))/86400 > 90))
            # bad fans
            or (rec[11] != None and int(rec[11]) == "1")
            # SIP status
            or (rec[12] != None and rec[12] == "Disabled")
            # battery condition
            or (rec[13] != None and rec[13] == "Service Battery")
            )):
            print("SLA: ",company,
                  #
                  "\nSerial#: ",rec[1],
                  #
                  "\nModel: ",rec[2],
                  #
                  "\nDevice type: ",rec[3],
                  #
                  "\nHostname: ",rec[4],
                  #
                  "\nName and surname: ","unknown" if rec[5] == None else rec[5],
                  #
                  # "\nMountpoint: ","unknown" if rec[6] == None else rec[6],
                  #
                  "\nFree space (GB): "+str(float(rec[7])/1073741824.0) if (rec[6] == "/" and int(rec[7]) <= 32212254720) else "",
                  #
                  "\nSMART errors: "+str(int(rec[8])) if (rec[8] != None and int(rec[8]) > 0) else "",
                  #
                  "\nBattery (%): "+str(int(rec[9])) if (rec[9] != None and int(rec[9]) <= 75) else "",
                  #
                  "\nBattery condition: Service battery" if (rec[13] != None and rec[13] == "Service Battery") else "",
                  #
                  "\nBattery cycle count: "+str(int(rec[14])) if (rec[14]!=None) else "",
                  #
                  "\nSIP status: Disabled" if (rec[12] != None and rec[12] == "Disabled") else "",
                  #
                  "\nFan errors !" if (rec[11] != None and int(rec[11]) == "1") else "",
                  #
                  "\nLast checkin: "+str(time.ctime(int(rec[10]))) if (rec[10] != None and ((time.time() - int(rec[10]))/86400 > 90)) else "",
                  "\n------\n"
                  )
