---
title: "Munkireport parser"
original author: [Tomáš Jamrich]
maintainer: [Michal Moravec]
git: https://gitlab.lws.mit.etn/infra/munki_report_parser
keywords: [Munkireport]
...

This file describes scripts to get selected parameters from the munkireport API
in the JSON format and to parse the output for better readability.

---

# Requirments

Script `munki_parse_json.py` requires `python3` and python `requests` library.

# Categories

Exported json contains following values:

```
rec[0] -> SLA -> "munkireport.manifestname"
rec[1] -> Serial -> "reportdata.serial_number"
rec[2] -> Model -> "machine.machine_model"
rec[3] -> Device type -> "machine.machine_name"
rec[4] -> Hostname -> "machine.computer_name"
rec[5] -> Name and surname -> "reportdata.long_usernae"
rec[6] -> Mountpoint -> "diskreport.mountpoint"
rec[7] -> Free space -> "diskreport.freespace"
rec[8] -> SMART -> "smart_stats.error_count"
rec[9] -> Battery -> "power.max_percent"
rec[10] -> Last checkin -> "reportdata.timestamp"
rec[11] -> Fan status -> "fan_temps.mssf"
rec[12] -> SIP status -> "security.sip"
rec[13] -> Power condition -> "power.condition"
rec[14] -> Battery cycle count -> "power.cycle_count"
```

# Conditions

Applied conditions:

- <= 30GB of local storage (value is stored in B)
- smart errors > 0
- <= 75% battery
- report time > 90 days
- fans error =='1'
- SIP disabled =="Disabled"
- battery power condition =="Service Battery"
- add battery cycle counter

# Exclude following machine groups

- logicworks
- logicworks_test
- triad
- sw
