#!/bin/bash
MUNKI_GET_JSON="/Users/tomasjamrich/gitlab_lw/munki_report_parser/munki_get_json.sh"
MUNKI_PARSE_JSON="/Users/tomasjamrich/gitlab_lw/munki_report_parser/munki_parse_json.py"

. "$MUNKI_GET_JSON"

python3 "$MUNKI_PARSE_JSON" >munki_report_data.txt

