#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 22 17:43:26 2019
@author: cecky
@maintainer: michal.moravec@logicworks.cz
"""
import collections
import time

import requests

# Munkireport configuration
base_url = "https://report.logicworks.cz/index.php?"
login = ""
password = ""

unwanted = ["logicworks", "logicworks_test", "triad", "sw", "unknown"]
columns = [
    "munkireport.manifestname",
    "reportdata.serial_number",
    "machine.machine_model",
    "machine.machine_name",
    "machine.computer_name",
    "reportdata.long_username",
    "diskreport.mountpoint",
    "diskreport.freespace",
    "smart_stats.error_count",
    "power.max_percent",
    "reportdata.timestamp",
    "fan_temps.mssf",
    "security.sip",
    "power.condition",
    "power.cycle_count",
]


def authenticate(session):
    """Authenticate and get a session cookie"""
    auth_url = "{0}/auth/login".format(base_url)
    auth_data = {"login": login, "password": password}
    auth_request = session.post(auth_url, data=auth_data)
    if auth_request.status_code != 200:
        print("Invalid url!")
        raise SystemExit


def generate_column_query():
    """Generate Munkireport API column query"""
    q = collections.OrderedDict()
    for i, c in enumerate(columns):
        q["columns[{0}][name]".format(i)] = c
    return q


def query(session, data):
    """Query Munkireport API"""
    query_url = "{0}/datatables/data".format(base_url)
    query_data = session.post(query_url, data)
    return query_data.json()


def get_data():
    """Get data required for this script from Munkireport"""
    session = requests.Session()
    authenticate(session)
    json_data = query(session, data=generate_column_query())
    return json_data


def sortfunc(r):
    """Sort JSON array"""
    return "x" if r[0] is None else r[0].split("/")[1]


def skip_record(record):
    """Filter out unwanted records"""
    if get_company(record) in unwanted:
        return True

    # We dont't care about records for other storage devices
    if record[6] != "/":
        return True

    return False


def get_company(record):
    """Get customer company name"""
    if record[0] is not None:
        return record[0].split("/")[1]

    return "unknown"


def generic_report(record, report):
    """Add generic information to the report"""

    company = get_company(record)
    report["message"] += "SLA: {}\n".format(company)
    report["message"] += "Serial#: {}\n".format(record[1])
    report["message"] += "Model: {}\n".format(record[2])
    report["message"] += "Device type: {}\n".format(record[3])
    report["message"] += "Hostname: {}\n".format(record[4])

    if record[5] is not None:
        user_name = record[5]
    else:
        user_name = "unknown"
    report["message"] += "Name and surname: {}\n".format(user_name)


def storage_report(record, report):
    """Generate report for low storage situation"""
    threshold = 30000000000  # <= 30G local storage
    if record[7] and int(record[7]) <= threshold:
        value = float(record[7]) / 1000000000.0
        report["message"] += "Free space (GB): {0:.2g}\n".format(value)
        report["should"] = True


def smart_report(record, report):
    """Generate report when there are smart errors"""
    if record[8] is not None and int(record[8]) > 0:
        report["message"] += "SMART errors: {}\n".format(record[8])
        report["should"] = True


def battery_report(record, report):
    """Generate report when battery is bad"""
    # Capacity problem
    threshold = 75
    battery_bad = False
    if record[9] is not None and int(record[9]) <= threshold:
        report["message"] += "Battery (%): {}\n".format(record[9])
        report["should"] = True
        battery_bad = True

    # Battery condition
    if record[13] == "Service Battery":
        report["message"] += "Battery condition: Service battery\n"
        report["should"] = True
        battery_bad = True

    if battery_bad and record[14] is not None:
        report["message"] += "Battery cycle count {}\n".format(record[14])


def security_report(record, report):
    """Generate report when security settings are disabled"""
    # SIP status
    if record[12] == "Disabled":
        report["message"] += "SIP status: Disabled\n"
        report["should"] = True


def uptime_report(record, report):
    """Generate report when computer is up for too long"""
    threshold = 90  # timestamp > 90 days
    if record[10] is not None:
        uptime = (time.time() - int(record[10])) / 86400
        checkin = time.ctime(int(record[10]))
        if uptime > threshold:
            report["message"] += "Last checkin: {}\n".format(checkin)
            report["should"] = True


def sensor_report(record, report):
    """Generate report when sensor is in bad state"""
    # bad fans
    if record[11] == "1":
        report["message"] += "Fan errors !\n"
        report["should"] = True


def prepare_machine_report(record):
    """Generates machine report"""

    report = {"message": "", "should": False}

    if skip_record(record):
        return report

    generic_report(record, report)
    storage_report(record, report)
    smart_report(record, report)
    battery_report(record, report)
    uptime_report(record, report)
    security_report(record, report)
    sensor_report(record, report)

    report["message"] += "\n------\n"

    return report


def process_data(json_data):
    """Parse downloaded data and generate report"""
    mydata = json_data["data"]
    mydata.sort(key=sortfunc)
    for record in mydata:
        report = prepare_machine_report(record)
        if report["should"]:
            print(report["message"])
        else:
            continue


def main():
    """Run program"""
    json_data = get_data()
    process_data(json_data)


if __name__ == "__main__":
    main()
