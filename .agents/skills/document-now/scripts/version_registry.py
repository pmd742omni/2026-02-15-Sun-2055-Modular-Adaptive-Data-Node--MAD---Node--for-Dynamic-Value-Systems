#!/usr/bin/env python3
"""
Version Registry Utility for Document Now Skill
Scans progress tracking logs, maintains version_registry.json & Version_Registry.md,
validates uniqueness of proposed Ndebele codenames via Python code, and computes next version numbers.
"""

import os
import sys
import json
import re
import glob

# Determine project paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
AGENTS_DIR = os.path.dirname(os.path.dirname(SKILL_DIR))
PROJECT_ROOT = os.path.dirname(AGENTS_DIR)
PROGRESS_DIR = os.path.join(PROJECT_ROOT, "progress tracking")
REGISTRY_JSON = os.path.join(PROGRESS_DIR, "version_registry.json")
REGISTRY_MD = os.path.join(PROGRESS_DIR, "Version_Registry.md")

def scan_progress_files():
    """Scans all markdown files in progress tracking/ to extract version records."""
    entries = []
    if not os.path.exists(PROGRESS_DIR):
        return entries

    files = glob.glob(os.path.join(PROGRESS_DIR, "*.md"))
    for filepath in sorted(files):
        filename = os.path.basename(filepath)
        if filename.startswith("Version_Registry") or filename.startswith("version_registry"):
            continue
            
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        version_match = re.search(r"##\s+Version\s+([\d\.]+)\s+[\(]?([A-Za-z0-9_-]+)[\)]?", content, re.IGNORECASE)
        date_match = re.search(r"##\s+Date\s+&\s+Time\s*\n+([^\n]+)", content, re.IGNORECASE)
        codename_match = re.search(r"\*\s+\*\*Codename\*\*:\s*([A-Za-z0-9_-]+)(?:\s*\(([^\)]+)\))?", content, re.IGNORECASE)

        if version_match:
            ver_num = version_match.group(1).strip()
            codename = version_match.group(2).strip()
            date_str = date_match.group(1).strip() if date_match else "N/A"
            meaning = codename_match.group(2).strip() if codename_match and codename_match.group(2) else ""

            entries.append({
                "version": ver_num,
                "codename": codename,
                "meaning": meaning,
                "date": date_str,
                "file": filename
            })

    return entries

def load_registry():
    """Loads registry from JSON file or rescans if missing."""
    scanned = scan_progress_files()
    
    if os.path.exists(REGISTRY_JSON):
        try:
            with open(REGISTRY_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
                existing_vers = {item["version"]: item for item in data}
                for item in scanned:
                    existing_vers[item["version"]] = item
                
                def parse_ver(ver_str):
                    try:
                        return [int(p) for p in ver_str.split(".")]
                    except Exception:
                        return [0, 0, 0]
                        
                data = sorted(existing_vers.values(), key=lambda x: parse_ver(x["version"]))
                return data
        except Exception:
            pass
            
    def parse_ver(ver_str):
        try:
            return [int(p) for p in ver_str.split(".")]
        except Exception:
            return [0, 0, 0]
            
    scanned = sorted(scanned, key=lambda x: parse_ver(x["version"]))
    save_registry(scanned)
    return scanned

def save_registry(entries):
    """Saves registry entries to version_registry.json and Version_Registry.md."""
    if not os.path.exists(PROGRESS_DIR):
        os.makedirs(PROGRESS_DIR, exist_ok=True)

    with open(REGISTRY_JSON, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)

    md_content = "# Version and Codename Registry\n\n"
    md_content += "| Version | Ndebele Codename | Meaning / Translation | Date & Time | Progress File |\n"
    md_content += "| :--- | :--- | :--- | :--- | :--- |\n"
    for item in entries:
        file_link = f"[{item['file']}](./{item['file']})"
        md_content += f"| **{item['version']}** | `{item['codename']}` | {item.get('meaning', 'N/A')} | {item['date']} | {file_link} |\n"

    with open(REGISTRY_MD, "w", encoding="utf-8") as f:
        f.write(md_content)

def check_codename_unique(proposed_codename):
    """Checks if a proposed codename is unique across all registered versions."""
    registry = load_registry()
    proposed_clean = proposed_codename.strip().lower()
    
    for item in registry:
        if item["codename"].strip().lower() == proposed_clean:
            return {
                "unique": False,
                "message": f"CONFLICT: Codename '{proposed_codename}' was already used in Version {item['version']} ({item['file']})!",
                "used_in": item
            }
            
    return {
        "unique": True,
        "message": f"SUCCESS: Codename '{proposed_codename}' is unique and available."
    }

def get_next_version():
    """Calculates the next version number string."""
    registry = load_registry()
    if not registry:
        return "1.0.0"
        
    latest = registry[-1]["version"]
    parts = [int(p) for p in latest.split(".")]
    parts[-1] += 1
    return f"{parts[0]}.{parts[1]}.{parts[2]}"

def register_version(ver_num, codename, meaning, date_str, filename):
    """Registers a new version entry into the registry."""
    check_res = check_codename_unique(codename)
    if not check_res["unique"]:
        print(json.dumps(check_res, indent=2))
        sys.exit(1)
        
    registry = load_registry()
    new_entry = {
        "version": ver_num,
        "codename": codename,
        "meaning": meaning,
        "date": date_str,
        "file": filename
    }
    registry.append(new_entry)
    save_registry(registry)
    return {"status": "registered", "entry": new_entry}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"usage": "python version_registry.py [list|check <name>|next-version|register <ver> <name> <meaning> <date> <file>]"}, indent=2))
        sys.exit(0)

    cmd = sys.argv[1].lower()
    if cmd == "list":
        print(json.dumps(load_registry(), indent=2))
    elif cmd == "check" and len(sys.argv) >= 3:
        print(json.dumps(check_codename_unique(sys.argv[2]), indent=2))
    elif cmd == "next-version":
        print(json.dumps({"next_version": get_next_version()}, indent=2))
    elif cmd == "register" and len(sys.argv) >= 6:
        ver = sys.argv[2]
        name = sys.argv[3]
        meaning = sys.argv[4]
        date_str = sys.argv[5]
        file_name = sys.argv[6] if len(sys.argv) >= 7 else "N/A"
        print(json.dumps(register_version(ver, name, meaning, date_str, file_name), indent=2))
    else:
        print(json.dumps({"error": f"Unknown command or invalid arguments for '{cmd}'"}, indent=2))
