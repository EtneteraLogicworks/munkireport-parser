# Munkireport parser

Tool to create user-readable reports of selected paramaters from
munkireport API.


## Requirments

See `requirments.txt` for required python3 packages


## Categories

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


## Conditions

Applied conditions:

- <= 20GB of local storage (value is stored in B)
- smart errors > 0
- <= 75% battery
- report time > 90 days
- fans error =='1'
- SIP disabled =="Disabled"
- battery power condition =="Service Battery"
- add battery cycle counter
