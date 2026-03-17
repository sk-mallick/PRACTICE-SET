#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════╗
║   EnglishJibi — Topic Setup Wizard           ║
║   Creates data/<topic>/<level>/ folders      ║
║   + config.js + set.json for each level      ║
╠══════════════════════════════════════════════╣
║  Install deps (once):                        ║
║    pip install questionary colorama          ║
║  Run:                                        ║
║    python setup_topic.py                     ║
╚══════════════════════════════════════════════╝
"""

import os
import sys

# ── Dependency check ──────────────────────────────────────────────────────────
try:
    import questionary
    from questionary import Style as QStyle, Choice
    import colorama
    from colorama import Fore, Style, Back
    colorama.init(autoreset=True)
except ImportError:
    print("\n  Missing dependencies. Run:\n")
    print("    pip install questionary colorama\n")
    sys.exit(1)

# ── Constants ─────────────────────────────────────────────────────────────────

LEVEL_ORDER  = ["pre-primary", "primary", "middle", "high"]
LEVEL_LABEL  = {"pre-primary": "PP", "primary": "P", "middle": "M", "high": "H"}
LEVEL_FULL   = {"pre-primary": "Pre-Primary", "primary": "Primary",
                "middle": "Middle", "high": "High"}

# ── Questionary style ─────────────────────────────────────────────────────────

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

# ── Print helpers ─────────────────────────────────────────────────────────────

W = 52  # box width

def banner():
    print(f"\n{Fore.YELLOW}{'═' * W}")
    print(f"  EnglishJibi  ·  Topic Setup Wizard")
    print(f"{'═' * W}{Style.RESET_ALL}\n")

def rule(title=""):
    bar = f"─ {title} " + "─" * (W - len(title) - 3) if title else "─" * W
    print(f"\n{Fore.YELLOW}{bar}{Style.RESET_ALL}\n")

def ok(msg):
    print(f"  {Fore.GREEN}✓{Style.RESET_ALL}  {msg}")

def info(msg):
    print(f"  {Fore.CYAN}→{Style.RESET_ALL}  {msg}")

def dim(msg):
    print(f"  {Fore.WHITE}{Style.DIM}{msg}{Style.RESET_ALL}")

def sub(msg):
    print(f"\n  {Fore.MAGENTA}▸ {msg}{Style.RESET_ALL}")

def abort(msg="Aborted."):
    print(f"\n  {Fore.RED}{msg}{Style.RESET_ALL}\n")
    sys.exit(0)

# ── Config.js generator ───────────────────────────────────────────────────────

def make_config_js(cfg: dict) -> str:
    """Produces a clean ES module export default { ... }"""
    lines = ["export default {"]
    for k, v in cfg.items():
        if isinstance(v, str):
            lines.append(f'    {k}: "{v}",')
        else:
            lines.append(f'    {k}: {v},')
    lines.append("}")
    return "\n".join(lines) + "\n"

# ── Input helpers ─────────────────────────────────────────────────────────────

def ask_text(prompt, instruction="", default=None):
    kwargs = dict(style=Q_STYLE)
    if instruction:
        kwargs["instruction"] = instruction
    if default is not None:
        kwargs["default"] = default
    val = questionary.text(prompt, **kwargs).ask()
    if val is None:
        abort()
    return val.strip()

def ask_int(prompt, default="25"):
    while True:
        raw = ask_text(prompt, default=default)
        if raw.isdigit() and int(raw) > 0:
            return int(raw)
        print(f"  {Fore.RED}Enter a positive integer.{Style.RESET_ALL}")

def ask_select(prompt, choices):
    val = questionary.select(prompt, choices=choices, style=Q_STYLE).ask()
    if val is None:
        abort()
    return val

def ask_checkbox(prompt, choices):
    val = questionary.checkbox(prompt, choices=choices, style=Q_STYLE).ask()
    if val is None:
        abort()
    return val

def ask_confirm(prompt, default=True):
    val = questionary.confirm(prompt, default=default, style=Q_STYLE).ask()
    if val is None:
        abort()
    return val

# ── Main wizard ───────────────────────────────────────────────────────────────

def main():
    banner()

    # ── Choices (defined here so imports are guaranteed) ─────────────────────
    ENGINE_CHOICES = [
        Choice("MCQ  (Multiple Choice Questions)", value="mcq"),
        Choice("Fill (Fill in the Blank)",          value="fill"),
    ]
    ICON_CHOICES = [
        Choice("📖  book",  value="book"),
        Choice("⏱  time",  value="time"),
        Choice("📋  list",  value="list"),
        Choice("💬  chat",  value="chat"),
    ]

    # ── STEP 1: Topic name ────────────────────────────────────────────────────
    rule("STEP 1  Topic Folder")

    topic = ask_text(
        "Topic folder name",
        instruction="e.g.  tenses · sva · narration · voice · articles"
    ).lower().replace(" ", "-")

    if not topic:
        abort("No topic entered.")

    data_path = os.path.join("data", topic)
    info(f"Will create under:  {Fore.CYAN}{data_path}/{Style.RESET_ALL}")

    # ── STEP 2: Level selection ───────────────────────────────────────────────
    rule("STEP 2  Select Levels")
    dim("Space = toggle   ·   Enter = confirm")
    print()

    raw_levels = ask_checkbox(
        "Which levels to create?",
        choices=[
            Choice("Pre-Primary", value="pre-primary"),
            Choice("Primary",     value="primary"),
            Choice("Middle",      value="middle"),
            Choice("High",        value="high"),
        ]
    )

    if not raw_levels:
        abort("No levels selected.")

    # Keep canonical order
    levels = [l for l in LEVEL_ORDER if l in raw_levels]

    # Auto-assign order (1-based, based on position in selection)
    order_map = {lvl: i + 1 for i, lvl in enumerate(levels)}

    print()
    for lvl in levels:
        info(f"{LEVEL_FULL[lvl]:<14}  order = {order_map[lvl]}  "
             f"label = {LEVEL_LABEL[lvl]}")

    # ── STEP 3: Common config ─────────────────────────────────────────────────
    rule("STEP 3  Common Configuration")
    dim("These values apply to all selected levels")
    print()

    title         = ask_text("Card title",
                             instruction="e.g.  Tenses  /  Subject-Verb Agreement")
    engine        = ask_select("Engine type", ENGINE_CHOICES)
    icon          = ask_select("Card icon",   ICON_CHOICES)
    header_title  = ask_text("Header title",
                             instruction="e.g.  TIME & TENSE PRACTICE")
    subtitle_pfx  = ask_text("Header subtitle prefix",
                             default="By Chiranjibi Sir")
    pdf_header    = ask_text("PDF header",
                             instruction="e.g.  Time & Tense")

    # ── STEP 4: Per-level details ─────────────────────────────────────────────
    rule("STEP 4  Per-Level Details")

    level_data = {}
    for lvl in levels:
        sub(f"{LEVEL_FULL[lvl]} Level")
        sets = ask_int("  Number of sets        ", default="1")
        qps  = ask_int("  Questions per set     ", default="25")
        level_data[lvl] = {"sets": sets, "qps": qps}

    # ── STEP 5: Preview ───────────────────────────────────────────────────────
    rule("STEP 5  Preview")

    print(f"  {Fore.WHITE}Topic  {Style.RESET_ALL}  {Fore.CYAN}data/{topic}/{Style.RESET_ALL}")
    print(f"  {Fore.WHITE}Title  {Style.RESET_ALL}  {title}")
    print(f"  {Fore.WHITE}Engine {Style.RESET_ALL}  {engine.upper()}   Icon: {icon}")
    print()

    col_w = max(len(LEVEL_FULL[l]) for l in levels) + 2
    for lvl in levels:
        d = level_data[lvl]
        lbl = LEVEL_LABEL[lvl]
        desc = f"{d['sets']} Sets • {d['qps']} Questions Each - {lbl}"
        print(
            f"  {Fore.YELLOW}{LEVEL_FULL[lvl]:<{col_w}}{Style.RESET_ALL}"
            f"  order={order_map[lvl]}   {Fore.WHITE}{desc}{Style.RESET_ALL}"
        )

    print()
    dim(f"Files to be created per level:  config.js  +  set.json")
    print()

    if not ask_confirm("Create folders and files now?"):
        abort("Cancelled. Nothing was written.")

    # ── STEP 6: Create files ──────────────────────────────────────────────────
    rule("STEP 6  Creating Files")

    created = []

    for lvl in levels:
        d     = level_data[lvl]
        lbl   = LEVEL_LABEL[lvl]
        desc  = f"{d['sets']} Sets • {d['qps']} Questions Each - {lbl}"

        folder = os.path.join("data", topic, lvl)
        os.makedirs(folder, exist_ok=True)

        cfg = {
            "order":                order_map[lvl],
            "title":                title,
            "description":          desc,
            "engine":               engine,
            "icon":                 icon,
            "sets":                 d["sets"],
            "level":                lbl,
            "headerTitle":          header_title,
            "headerSubtitlePrefix": subtitle_pfx,
            "pdfheader":            pdf_header,
        }

        # config.js
        config_path = os.path.join(folder, "config.js")
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(make_config_js(cfg))

        # empty master set.json
        set_path = os.path.join(folder, "set.json")
        with open(set_path, "w", encoding="utf-8") as f:
            f.write("[]\n")

        ok(f"{folder}/  →  config.js  +  set.json")
        created.append(folder)

    # ── Done ──────────────────────────────────────────────────────────────────
    print(f"\n{Fore.GREEN}{'═' * W}")
    print(f"  ✅  Done!  {len(created)} level(s) set up under  data/{topic}/")
    print(f"{'═' * W}{Style.RESET_ALL}\n")

    print(f"  {Fore.YELLOW}Next steps:{Style.RESET_ALL}")
    print(f"  1. Fill  {Fore.CYAN}data/{topic}/<level>/set.json{Style.RESET_ALL}  with questions")
    print(f"  2. Run   {Fore.CYAN}CODE.TXT{Style.RESET_ALL}  splitter → generates set1.json, set2.json …")
    print(f"  3. Add   {Fore.CYAN}'{topic}'{Style.RESET_ALL}  to  js/index-loader.js  → SUBJECTS array")
    print()

# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n  {Fore.YELLOW}Interrupted. Nothing was written.{Style.RESET_ALL}\n")
        sys.exit(0)