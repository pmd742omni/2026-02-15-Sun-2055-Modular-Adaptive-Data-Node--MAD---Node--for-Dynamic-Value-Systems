#!/usr/bin/env python3
"""
Chapter Development System Timestamp Utility
Extracts the exact local system machine date and time for standardized chapter file naming.
Uses real datetime.datetime.now().astimezone() without artificial offsets or random numbers.
"""

import datetime
import json
import sys

def get_chapter_timestamp():
    now_local = datetime.datetime.now().astimezone()
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    
    date_str = now_local.strftime("%Y-%m-%d")
    time_str = now_local.strftime("%H%M")
    time_display = now_local.strftime("%H:%M")
    
    filename_prefix = f"{date_str} {time_str}"
    
    return {
        "filename_prefix": filename_prefix,
        "date_only": date_str,
        "time_hhmm": time_str,
        "time_display": time_display,
        "iso_local": now_local.isoformat(),
        "iso_utc": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    }

if __name__ == "__main__":
    ts = get_chapter_timestamp()
    print(json.dumps(ts, indent=2))
