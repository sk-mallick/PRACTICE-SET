#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════╗
║   EnglishJibi — Set Splitter                 ║
║   Splits data/<subject>/<level>/set.json     ║
║   into set1.json, set2.json, …               ║
╠══════════════════════════════════════════════╣
║  Install deps (once):                        ║
║    pip install questionary colorama          ║
║  Run:                                        ║
║    python split_sets.py                      ║
╚══════════════════════════════════════════════╝
"""

import os
import sys
import json
import re

try:
    import questionary
    from questionary import Style as QStyle, Choice
    import colorama
    from colorama import Fore, Style
    colorama.init(autoreset=True)
except ImportError:
    print("\n  Missing dependencies. Run:\n")
    print("    pip install questionary colorama\n")
    sys.exit(1)

# ── Style ─────────────────────────────────────────────────────────────────────

Q_STYLE = QStyle([
    ("qmark",       "fg:#f59e0b bold"),
    ("question",    "fg:#f1f5f9 bold"),
    ("answer",      "fg:#34d399 bold"),
    ("pointer",     "fg:#f59e0b bold"),
    ("highlighted", "fg:#f59e0b bold"),
    ("selected",    "fg:#34d399"),
    ("instruction", "fg:#64748b"),
    ("text",        "fg:#e2e8f0"),
    ("disabled",    "fg:#475569 italic"),
])

W = 52

# ── Print helpers ─────────────────────────────────────────────────────────────

def banner():
    print(f"\n{Fore.YELLOW}{'═' * W}")
    print(f"  EnglishJibi  ·  Set Splitter")
    print(f"{'═' * W}{Style.RESET_ALL}\n")

def rule(title=""):
    bar = f"─ {title} " + "─" * (W - len(title) - 3) if title else "─" * W
    print(f"\n{Fore.YELLOW}{bar}{Style.RESET_ALL}\n")

def ok(msg):   print(f"  {Fore.GREEN}✓{Style.RESET_ALL}  {msg}")
def info(msg): print(f"  {Fore.CYAN}→{Style.RESET_ALL}  {msg}")
def warn(msg): print(f"  {Fore.YELLOW}⚠{Style.RESET_ALL}  {msg}")
def err(msg):  print(f"  {Fore.RED}✗{Style.RESET_ALL}  {msg}")
def dim(msg):  print(f"  {Fore.WHITE}{Style.DIM}{msg}{Style.RESET_ALL}")

def abort(msg="Aborted."):
    print(f"\n  {Fore.RED}{msg}{Style.RESET_ALL}\n")
    sys.exit(0)

# ── Helpers ───────────────────────────────────────────────────────────────────

def ask_select(prompt, choices):
    val = questionary.select(prompt, choices=choices, style=Q_STYLE).ask()
    if val is None:
        abort()
    return val

def ask_int(prompt, default="25"):
    while True:
        raw = questionary.text(prompt, default=str(default), style=Q_STYLE).ask()
        if raw is None:
            abort()
        raw = raw.strip()
        if raw.isdigit() and int(raw) > 0:
            return int(raw)
        err("Enter a positive integer.")

def ask_confirm(prompt, default=True):
    val = questionary.confirm(prompt, default=default, style=Q_STYLE).ask()
    if val is None:
        abort()
    return val

# ── Config.js patcher ─────────────────────────────────────────────────────────

def patch_config_sets(config_path, new_sets):
    """Updates the `sets: N` line in config.js without touching anything else."""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
        patched = re.sub(r'(\bsets\s*:\s*)\d+', rf'\g<1>{new_sets}', content)
        if patched != content:
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(patched)
            ok(f"config.js  →  sets updated to {new_sets}")
        else:
            warn("config.js  →  `sets` field not found; update it manually")
    except Exception as e:
        warn(f"Could not patch config.js: {e}")

# ── Scanner ───────────────────────────────────────────────────────────────────

LEVEL_ORDER = ["pre-primary", "primary", "middle", "high"]

def scan_data_folder():
    """Returns dict: { subject: [level, ...] } — only where set.json exists."""
    base = "data"
    if not os.path.isdir(base):
        err("No 'data/' folder found. Run this script from your PRACTICE-SET root.")
        sys.exit(1)

    tree = {}
    for subject in sorted(os.listdir(base)):
        subj_path = os.path.join(base, subject)
        if not os.path.isdir(subj_path):
            continue
        levels = []
        for level in LEVEL_ORDER:
            lvl_path = os.path.join(subj_path, level)
            if os.path.isfile(os.path.join(lvl_path, "set.json")):
                levels.append(level)
        if levels:
            tree[subject] = levels

    return tree

# ── Write setN.json files ─────────────────────────────────────────────────────

def write_set_file(path, questions):
    with open(path, "w", encoding="utf-8") as f:
        f.write("[\n")
        for idx, q in enumerate(questions):
            line = json.dumps(q, ensure_ascii=False, separators=(',', ':'))
            f.write(f"  {line}")
            f.write(",\n" if idx < len(questions) - 1 else "\n")
        f.write("]")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    banner()

    tree = scan_data_folder()

    if not tree:
        err("No set.json files found inside data/. Add questions first.")
        sys.exit(1)

    # ── STEP 1: Subject ───────────────────────────────────────────────────────
    rule("STEP 1  Select Subject")

    subject = ask_select(
        "Which subject?",
        choices=[Choice(s.upper(), value=s) for s in sorted(tree)]
    )

    # ── STEP 2: Level ─────────────────────────────────────────────────────────
    rule("STEP 2  Select Level")

    level = ask_select(
        "Which level?",
        choices=[Choice(l.capitalize(), value=l) for l in tree[subject]]
    )

    # ── Load set.json ─────────────────────────────────────────────────────────
    folder      = os.path.join("data", subject, level)
    master_path = os.path.join(folder, "set.json")
    config_path = os.path.join(folder, "config.js")

    print()
    info(f"Reading  {master_path}")

    try:
        with open(master_path, "r", encoding="utf-8") as f:
            questions = json.load(f)
    except json.JSONDecodeError as e:
        err(f"set.json has invalid JSON: {e}")
        sys.exit(1)

    total_q = len(questions)

    if total_q == 0:
        err("set.json is empty. Add questions first.")
        sys.exit(1)

    info(f"Total questions found:  {Fore.YELLOW}{total_q}{Style.RESET_ALL}")

    # ── STEP 3: Questions per set ─────────────────────────────────────────────
    rule("STEP 3  Split Configuration")

    qps        = ask_int("Questions per set", default=25) # type: ignore
    total_sets = (total_q + qps - 1) // qps   # ceiling division
    last_set_q = total_q - (total_sets - 1) * qps

    print()
    info(
        f"Will create  {Fore.YELLOW}{total_sets} set(s){Style.RESET_ALL}  "
        f"({qps} questions each"
        + (f", last set has {last_set_q}" if last_set_q != qps else "")
        + ")"
    )
    info(f"Files :  set1.json  →  set{total_sets}.json")
    info(f"Folder:  {folder}/")

    # Warn about existing files to be overwritten
    existing = [
        f"set{i+1}.json"
        for i in range(total_sets)
        if os.path.exists(os.path.join(folder, f"set{i+1}.json"))
    ]
    if existing:
        print()
        warn(f"{len(existing)} existing file(s) will be overwritten:")
        for name in existing[:5]:
            dim(f"  {folder}/{name}")
        if len(existing) > 5:
            dim(f"  … and {len(existing) - 5} more")

    print()
    if not ask_confirm("Proceed with split?"):
        abort("Cancelled. Nothing was written.")

    # ── STEP 4: Write ─────────────────────────────────────────────────────────
    rule("STEP 4  Writing Files")

    for i in range(total_sets):
        subset    = questions[i * qps : (i + 1) * qps]
        file_path = os.path.join(folder, f"set{i+1}.json")
        write_set_file(file_path, subset)
        ok(f"set{i+1}.json  ({len(subset)} questions)")

    # Auto-patch config.js sets count
    print()
    if os.path.isfile(config_path):
        patch_config_sets(config_path, total_sets)
    else:
        warn("config.js not found — remember to update `sets` manually")

    # ── Done ──────────────────────────────────────────────────────────────────
    print(f"\n{Fore.GREEN}{'═' * W}")
    print(f"  ✅  Done!  {total_sets} set(s) written to  {folder}/")
    print(f"{'═' * W}{Style.RESET_ALL}\n")

# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n  {Fore.YELLOW}Interrupted.{Style.RESET_ALL}\n")
        sys.exit(0)
