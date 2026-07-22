#!/usr/bin/env python3
"""
System Timestamp Utility for Document Now Skill
Extracts local and UTC system date and time stamps for standardized progress tracking documentation,
file naming, registry logs, and git commit messages.
"""

import datetime
import json
import sys

def get_system_timestamps():
    now_local = datetime.datetime.now().astimezone()
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    
    file_prefix = now_local.strftime("%Y-%m-%d_%H%M")
    git_prefix = now_local.strftime("%Y-%m-%d %a %H%M")
    human_date_time = now_local.strftime("%A, %d %B %Y, %I:%M %p (local time)")
    date_only = now_local.strftime("%Y-%m-%d")
    time_only_24h = now_local.strftime("%H:%M")
    iso_utc = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    return {
        "file_prefix": file_prefix,
        "git_prefix": git_prefix,
        "human_date_time": human_date_time,
        "date_only": date_only,
        "time_only_24h": time_only_24h,
        "iso_utc": iso_utc,
        "raw_local_iso": now_local.isoformat()
    }

if __name__ == "__main__":
    timestamps = get_system_timestamps()
    print(json.dumps(timestamps, indent=2))
