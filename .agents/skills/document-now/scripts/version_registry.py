#!/usr/bin/env python3
"""
Portable Version Registry Utility for Document Now Skill
Scans progress tracking logs, auto-bootstraps missing progress folders and registry files,
maintains version_registry.json & Version_Registry.md, validates codename uniqueness,
provides unused Ndebele codename suggestions, and computes next version numbers across any project workspace.
"""

import os
import sys
import json
import re
import glob
import subprocess

def find_project_root():
    """Dynamically finds the project root directory by searching for .git, progress tracking, or walking up."""
    for idx, arg in enumerate(sys.argv):
        if arg == "--project-root" and idx + 1 < len(sys.argv):
            return os.path.abspath(sys.argv[idx + 1])

    cwd = os.getcwd()
    curr = cwd
    while True:
        if os.path.exists(os.path.join(curr, ".git")) or os.path.exists(os.path.join(curr, "progress tracking")):
            return curr
        parent = os.path.dirname(curr)
        if parent == curr:
            break
        curr = parent
        
    return cwd

PROJECT_ROOT = find_project_root()
PROGRESS_DIR = os.path.join(PROJECT_ROOT, "progress tracking")
REGISTRY_JSON = os.path.join(PROGRESS_DIR, "version_registry.json")
REGISTRY_MD = os.path.join(PROGRESS_DIR, "Version_Registry.md")

# Built-in Ndebele Vocabulary Suggestion Engine
NDEBELE_DICTIONARY = [
    {"codename": "Isisekelo", "meaning": "Foundation / Base"},
    {"codename": "Inqubo", "meaning": "Process / Methodology"},
    {"codename": "Umnyango", "meaning": "Gateway / Entrance"},
    {"codename": "Umklamo", "meaning": "Design / Blueprint"},
    {"codename": "Ingatsha", "meaning": "Branch / Module"},
    {"codename": "Umfanekiso", "meaning": "Visualization / Picture"},
    {"codename": "Izidingo", "meaning": "Requirements / Needs"},
    {"codename": "Qaphela", "meaning": "Caution / Security Guard"},
    {"codename": "Ukonga", "meaning": "Optimization / Saving"},
    {"codename": "Umdwebo", "meaning": "Diagram / Drawing"},
    {"codename": "Ukunisela", "meaning": "Irrigation / Refresh"},
    {"codename": "Ukunciphisa", "meaning": "Reduction / Simplification"},
    {"codename": "Izixhobo", "meaning": "Tools / Hardware"},
    {"codename": "Ukuhlola", "meaning": "Testing / Evaluation"},
    {"codename": "Ukuphepha", "meaning": "Safety / Security Protection"},
    {"codename": "Umbiko", "meaning": "Report / Summary"},
    {"codename": "Ukuhlela", "meaning": "Planning / Architecture"},
    {"codename": "Ukusebenza", "meaning": "Implementation / Work"},
    {"codename": "Ukuqinisekisa", "meaning": "Verification / Validation"},
    {"codename": "Ukucinisa", "meaning": "Strengthening / Robustness"},
    {"codename": "Ukulonda", "meaning": "Preserving / Safe Keeping"},
    {"codename": "Ukuthuthuka", "meaning": "Progress / Growth"},
    {"codename": "Ukuhlanganisa", "meaning": "Integration / Fusion"},
    {"codename": "Ukusungula", "meaning": "Innovation / Invention"},
    {"codename": "Ukuhlonipha", "meaning": "Compliance / Respect"},
    {"codename": "Ukukhanya", "meaning": "Clarity / Illumination"},
    {"codename": "Ukwanelisa", "meaning": "Satisfaction / Completion"},
    {"codename": "Ukudlulisa", "meaning": "Transmission / Synchronization"},
    {"codename": "Ukuvula", "meaning": "Access / Opening"},
    {"codename": "Ukuxhumana", "meaning": "Networking / Connectivity"}
]

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

def parse_semver(ver_str):
    try:
        parts = [int(p) for p in ver_str.split(".")]
        while len(parts) < 3:
            parts.append(0)
        return parts
    except Exception:
        return [0, 0, 0]

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
                data = sorted(existing_vers.values(), key=lambda x: parse_semver(x["version"]))
                return data
        except Exception:
            pass
            
    scanned = sorted(scanned, key=lambda x: parse_semver(x["version"]))
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

def suggest_codenames(count=5):
    """Suggests unused Ndebele codenames from the built-in vocabulary."""
    registry = load_registry()
    used_clean = {item["codename"].strip().lower() for item in registry}
    
    suggestions = []
    for entry in NDEBELE_DICTIONARY:
        if entry["codename"].strip().lower() not in used_clean:
            suggestions.append(entry)
            if len(suggestions) >= count:
                break
                
    return suggestions

def get_next_version():
    """Calculates the next version number string."""
    registry = load_registry()
    if not registry:
        return "1.0.0"
        
    latest = registry[-1]["version"]
    parts = parse_semver(latest)
    parts[-1] += 1
    return f"{parts[0]}.{parts[1]}.{parts[2]}"

def bootstrap_workspace():
    """Ensures progress tracking directory and registry files exist."""
    created_dir = False
    if not os.path.exists(PROGRESS_DIR):
        os.makedirs(PROGRESS_DIR, exist_ok=True)
        created_dir = True
        
    registry = load_registry()
    
    # Check git initialization
    git_initialized = False
    try:
        res = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=PROJECT_ROOT, capture_output=True, text=True)
        if res.returncode == 0 and "true" in res.stdout:
            git_initialized = True
    except Exception:
        pass
        
    return {
        "project_root": PROJECT_ROOT,
        "progress_dir": PROGRESS_DIR,
        "created_progress_dir": created_dir,
        "registry_count": len(registry),
        "next_version": get_next_version() if registry else "1.0.0",
        "suggested_codename": suggest_codenames(1)[0] if suggest_codenames(1) else {"codename": "Isisekelo", "meaning": "Foundation"},
        "git_initialized": git_initialized
    }

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
        print(json.dumps({"usage": "python version_registry.py [bootstrap|list|check <name>|suggest|next-version|register <ver> <name> <meaning> <date> <file>]"}, indent=2))
        sys.exit(0)

    cmd = sys.argv[1].lower()
    if cmd == "bootstrap":
        print(json.dumps(bootstrap_workspace(), indent=2))
    elif cmd == "list":
        print(json.dumps(load_registry(), indent=2))
    elif cmd == "check" and len(sys.argv) >= 3:
        print(json.dumps(check_codename_unique(sys.argv[2]), indent=2))
    elif cmd == "suggest":
        count = int(sys.argv[2]) if len(sys.argv) >= 3 and sys.argv[2].isdigit() else 5
        print(json.dumps(suggest_codenames(count), indent=2))
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
