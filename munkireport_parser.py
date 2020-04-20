#!/usr/bin/env python3

import argparse
import collections
import sys
import time

import requests
import yaml

# Munkireport configuration
CONFIG_PATH_DEFAULT = "munkireport-parser.yml"
CONFIG_REQUIRED_PARAMETERS = (
    "base_url",
    "username",
    "password",
)

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


class MunkiParseError(Exception):
    pass


def authenticate(session, base_url, login, password):
    """Authenticate and get a session cookie"""
    auth_url = "{0}/auth/login".format(base_url)
    auth_data = {"login": login, "password": password}
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


def query(session, base_url, data):
    """Query Munkireport API"""
    query_url = "{0}/datatables/data".format(base_url)
    query_data = session.post(query_url, data)
    return query_data.json()


def get_data(config):
    """Get data required for this script from Munkireport"""
    session = requests.Session()
    authenticate(session, config["base_url"], config["username"], config["password"])
    json_data = query(session, config["base_url"], data=generate_column_query())
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
        report["should"] = False
        return True

    report["should"] = True
    return False


def skip_record(record, excluded_companies=None):
    """Filter out unwanted records"""
    if get_company(record) in (excluded_companies or ()):
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


def prepare_machine_report(record, excluded_companies):
    """Generates machine report"""

    report = {"should": False, "Problems": {}}

    if skip_record(record, excluded_companies):
        return report

    generic_report(record, report)
    storage_report(record, report)
    smart_report(record, report)
    battery_report(record, report)
    uptime_report(record, report)
    security_report(record, report)
    sensor_report(record, report)

    return report


def process_data(json_data, config):
    """Parse downloaded data and generate report"""
    mydata = json_data["data"]
    mydata.sort(key=sortfunc)

    computers = []

    for record in mydata:
        report = prepare_machine_report(record, config.get("excluded"))
        if report["should"]:
            report.pop("should", None)
            computers.append(report)

    print(yaml.dump(computers, allow_unicode=True, default_flow_style=False))


def parse_args():
    """Define argument parser and returns parsed command line arguments"""
    parser = argparse.ArgumentParser(
       description="Tool to create user-readable reports of selected paramaters from munkireport",
    )
    parser.add_argument(
        "-c", "--config",
        dest='config_file',
        type=argparse.FileType('r'),
        default=CONFIG_PATH_DEFAULT,
        help="Path to configuration file"
    )

    return parser.parse_args()


def parse_config(config_file):
    """Parse and check provided configuration file"""
    try:
        config = yaml.load(config_file, Loader=yaml.SafeLoader)
        for member in CONFIG_REQUIRED_PARAMETERS:
            if member not in config:
                raise MunkiParseError("'{}' parameter is missing in the config".format(member))
        return config

    except yaml.error.YAMLError as e:
        print("Failed to load YAML config: {}".format(e), file=sys.stderr)
        sys.exit(1)

    except MunkiParseError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)


def main():
    """Run program"""
    args = parse_args()
    config = parse_config(args.config_file)

    json_data = get_data(config)
    process_data(json_data, config)


if __name__ == "__main__":
    main()
