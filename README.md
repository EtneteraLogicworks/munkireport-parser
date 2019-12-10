---
title: "Munkireport parser"
author: [Tomáš Jamrich]
git: https://gitlab.lws.mit.etn/tomas.jamrich/munki_report_parser
keywords: [Munkireport]
...

This file describes scripts to get selected parameters from the munkireport API
in the JSON format and to parse the output for better readability.

---

Categories
------

Exported json contains following values:

`rec[0] -> SLA -> "munkireport.manifestname"`  
`rec[1] -> Serial -> "reportdata.serial_number"`  
`rec[2] -> Model -> "machine.machine_model"`  
`rec[3] -> Device type -> "machine.machine_name"`  
`rec[4] -> Hostname -> "machine.computer_name",`  
`rec[5] -> Name and surname -> "reportdata.long_username"`  
`rec[6] -> Mountpoint -> "diskreport.mountpoint"`  
`rec[7] -> Free space -> "diskreport.freespace"`  
`rec[8] -> SMART -> "smart_stats.error_count"`  
`rec[9] -> Battery -> "power.max_percent"`  
`rec[10] -> Last checkin -> "reportdata.timestamp"`  

Conditions
------

Conditions that are applied to values stored in json:

> <= 30GB of local storage (value stored in B)  
  `int(rec[7]) <= 32212254720`  
> smart errors  
  `int(rec[8]) > 0`  
> <= 75% battery  
  `int(rec[9]) <= 75`  
> timestamp > 90 days  
  `(time.time() - int(rec[10]))/86400 > 90`  

Display error text if conditions do not pass, else display the value in given
fomat

`"NoFreeSpaceData" if rec[7] == None else float(rec[7])/1073741824.0`  
`"NoSmartData" if rec[8] == None else int(rec[8])`  
`"NoBatteryData" if rec[9] == None else int(rec[9])`  
`"NoTimestamp" if rec[10] == None else time.ctime(int(rec[10]))`  

