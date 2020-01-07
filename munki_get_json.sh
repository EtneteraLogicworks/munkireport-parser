#!/bin/sh
# DEBUG=1

MR_BASE_URL='https://report.logicworks.cz/index.php?'
MR_DATA_QUERY='/datatables/data'
MR_LOGIN=''
MR_PASSWORD=''

CLIENT_COLUMNS=(
    "munkireport.manifestname"
    #sla name
    "reportdata.serial_number"
    #serial
    "machine.machine_model"
    #model of the machine
    "machine.machine_name"
    #device type
    "machine.computer_name"
    #device host name
    "reportdata.long_username"
    #user name, surname
    "diskreport.mountpoint"
    #mount point to differentiate recovery partitions, internal mountpoint == /
    "diskreport.freespace"
    #disk free space, to include <30GB, value default in B
    "smart_stats.error_count"
    #smart stats errors
    "power.max_percent"
    #max battery <75%
    "reportdata.timestamp"
    #checkin >90days
    "fan_temps.mssf"
    #fan status, value "1"
    "security.sip"
    #system integrity protection, value "DISABLED"
    "power.condition"
    #battery condition, value "SERVICE NOW"
    "power.cycle_count"
    #battery cycle count
)

# Create query from columns
columns_to_query()
{
    # Pick up array as argument
    declare -a COLUMNS=("${!1}")
    MR_QUERY=""
    COL=0
    for i in "${COLUMNS[@]}"; do
        MR_QUERY="${MR_QUERY}columns[${COL}][name]=${i}&"
        COL=$((COL+1))
    done
}

# Authenticate and capture cookie
if [ $DEBUG ]; then echo 'Authenticating to munkireport..'; fi
COOKIE_JAR=$(curl -s -k --cookie-jar - --data "login=${MR_LOGIN}&password=${MR_PASSWORD}" ${MR_BASE_URL}/auth/login)
SESSION_COOKIE=$(echo $COOKIE_JAR | sed 's/.*PHPSESSID /PHPSESSID=/')

# Retrieve data with session cookie
columns_to_query CLIENT_COLUMNS[@]
if [ $DEBUG ]; then echo 'Retrieving client data..'; fi
echo $(curl -s -k --cookie "$SESSION_COOKIE" --data $MR_QUERY ${MR_BASE_URL}${MR_DATA_QUERY}) > "json_data.json"
# -k -> insecure option bypass certificate
