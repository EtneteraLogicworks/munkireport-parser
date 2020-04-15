#!/usr/bin/env python3

import collections
import time

import requests
import yaml

# Munkireport configuration
BASE_URL = "{{ munkireport_parser.url }}"
LOGIN = "{{ munkireport_parser.username }}"
PASSWORD = "{{ munkireport_parser.password }}"

UNWANTED = [ {{ munkireport_parser.unwanted_groups | wrap | join(', ') }} ]
COLUMNS = [
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
    "comment.text",
]

MANIFEST_NAME = 0
SERIAL_NUMBER = 1
MACHINE_MODEL = 2
MACHINE_NAME = 3
COMPUTER_NAME = 4
LONG_USERNAME = 5
MOUNTPOINT = 6
FREESPACE = 7
SMARTS_ERROR_COUNT = 8
POWER_MAX_PERCENT = 9
REPORT_TIMESTAMP = 10
FAN_TEMS_MSSFF = 11
SECURITY_SIP = 12
POWER_CONDITON = 13
POWER_CYCLE_COUNT = 14
COMMENT_TEXT = 15


def authenticate(session):
    """Authenticate and get a session cookie"""
    auth_url = "{0}/auth/login".format(BASE_URL)
    auth_data = {"login": LOGIN, "password": PASSWORD}
    auth_request = session.post(auth_url, data=auth_data)
    if auth_request.status_code != 200:
        print("Invalid url!")
        raise SystemExit


def generate_column_query():
    """Generate Munkireport API column query"""
    col_query = collections.OrderedDict()
    for index, column in enumerate(COLUMNS):
        col_query["columns[{0}][name]".format(index)] = column
    return col_query


def query(session, data):
    """Query Munkireport API"""
    query_url = "{0}/datatables/data".format(BASE_URL)
    query_data = session.post(query_url, data)
    return query_data.json()


def get_data():
    """Get data required for this script from Munkireport"""
    session = requests.Session()
    authenticate(session)
    json_data = query(session, data=generate_column_query())
    return json_data


def sortfunc(record):
    """Sort JSON array"""
    return "x" if record[0] is None else record[0].split("/")[1]


def determine_acknowledgement(record, report, ignore_string):
    """Mark report for output unless ignored"""
    if record[COMMENT_TEXT]:
        comment = record[COMMENT_TEXT].lower()
    else:
        comment = ""
    if ignore_string in comment:
        report["should"] = True
        return True

    report["should"] = True
    return False


def skip_record(record):
    """Filter out UNWANTED records"""
    if get_company(record) in UNWANTED:
        return True

    # We dont't care about records for other storage devices
    if record[MOUNTPOINT] != "/":
        return True

    return False


def get_company(record):
    """Get customer company name"""
    if record[MANIFEST_NAME] is not None:
        return record[MANIFEST_NAME].split("/")[1]

    return "unknown"


def add_problem(report, problem, description, ack):
    """Add problem dict to report"""
    report["Problems"][problem] = {}
    report["Problems"][problem]["Description"] = description
    report["Problems"][problem]["Acknowledged"] = ack


def generic_report(record, report):
    """Add generic information to the report"""

    company = get_company(record)
    report["SLA"] = company
    report["Serial"] = record[SERIAL_NUMBER]
    report["Model"] = record[MACHINE_MODEL]
    report["Device Type"] = record[MACHINE_NAME]
    report["Hostname"] = record[COMPUTER_NAME]

    if record[LONG_USERNAME] is not None:
        user_name = record[LONG_USERNAME]
    else:
        user_name = "unknown"
    report["Username"] = user_name


def storage_report(record, report):
    """Generate report for low storage situation"""
    threshold = 20000000000  # <= 20G local storage
    if record[FREESPACE] and int(record[FREESPACE]) <= threshold:
        value = float(record[FREESPACE]) / 1000000000.0
        add_problem(
            report,
            "Storage",
            { "Free space": "{0:.2g} GB".format(value) },
            determine_acknowledgement(record, report, "ack-storage"),
        )


def smart_report(record, report):
    """Generate report when there are smart errors"""
    if record[SMARTS_ERROR_COUNT] is not None and int(record[SMARTS_ERROR_COUNT]) > 0:
        add_problem(
            report,
            "SMART",
            "SMART errors: {}".format(record[SMARTS_ERROR_COUNT]),
            determine_acknowledgement(record, report, "ack-smart"),
        )


def battery_report(record, report):
    """Generate report when battery is bad"""
    # Capacity problem
    threshold = 75
    battery_bad = False
    description = {}
    if (
        record[POWER_MAX_PERCENT] is not None
        and int(record[POWER_MAX_PERCENT]) <= threshold
    ):
        description["Capacity"] = "{}%".format(record[POWER_MAX_PERCENT])
        battery_bad = True

    # Battery condition
    if record[POWER_CONDITON] == "Service Battery":
        description["Condition"] = "Service Battery"
        battery_bad = True

    if battery_bad and record[POWER_CYCLE_COUNT] is not None:
        description["Cycles"] = int(record[POWER_CYCLE_COUNT])

    if battery_bad:
        add_problem(
            report,
            "Battery",
            description,
            determine_acknowledgement(record, report, "ack-battery"),
        )


def security_report(record, report):
    """Generate report when security settings are disabled"""
    # SIP status
    if record[SECURITY_SIP] == "Disabled":
        add_problem(
            report,
            "SIP",
            "SIP is disabled",
            determine_acknowledgement(record, report, "ack-sip"),
        )


def uptime_report(record, report):
    """Generate report when computer is up for too long"""
    threshold = 90  # timestamp > 90 days
    if record[REPORT_TIMESTAMP] is not None:
        uptime = (time.time() - int(record[REPORT_TIMESTAMP])) / 86400
        checkin = time.ctime(int(record[REPORT_TIMESTAMP]))
        if uptime > threshold:
            add_problem(
                report,
                "Uptime",
                "Uptime {} days. Last checkin: {}".format(int(uptime), checkin),
                determine_acknowledgement(record, report, "ack-uptime"),
            )


def sensor_report(record, report):
    """Generate report when sensor is in bad state"""
    # bad fans
    if record[FAN_TEMS_MSSFF] == "1":
        add_problem(
            report,
            "Fan",
            "Fan Errors!",
            determine_acknowledgement(record, report, "ack-fans"),
        )


def prepare_machine_report(record):
    """Generates machine report"""

    report = {"should": False, "Problems": {}}

    if skip_record(record):
        return report

    generic_report(record, report)
    storage_report(record, report)
    smart_report(record, report)
    battery_report(record, report)
    uptime_report(record, report)
    security_report(record, report)
    sensor_report(record, report)

    return report


def process_data(json_data):
    """Parse downloaded data and generate report"""
    mydata = json_data["data"]
    mydata.sort(key=sortfunc)

    computers = []

    for record in mydata:
        report = prepare_machine_report(record)
        if report["should"]:
            report.pop("should", None)
            computers.append(report)

    print(yaml.dump(computers, allow_unicode=True, default_flow_style=False))


def main():
    """Run program"""
    json_data = get_data()
    process_data(json_data)


if __name__ == "__main__":
    main()
