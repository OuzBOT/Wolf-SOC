#!/usr/bin/env python3
"""
Wolf-SOC Interactive Tech Diagrams — Category-tabbed ASCII schematics & node quizzer.
All navigation is single-key arcade speed with synced 72-col frames and 8-bit audio.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

from synth_engine import BackgroundBeat, play_sfx
import ui_core as ui

LOCAL_DATA_DIR = Path(__file__).resolve().parent / "data"
DIAGRAMS_ROOT = LOCAL_DATA_DIR / "diagrams"
GLOSSARY_PATH = LOCAL_DATA_DIR / "glossary.json"

RST, BOLD, DIM = ui.RST, ui.BOLD, ui.DIM
CYAN, PINK, MINT, GOLD, RED, PURP = ui.CYAN, ui.PINK, ui.MINT, ui.GOLD, ui.RED, ui.PURP

getch = ui.getch
clear = ui.clear

# Map folder names cleanly into 4 compact category tabs (max 8 items per tab = single-key [1-8]!)
CATEGORY_TABS = [
    ("1", "Security Core", {"3_security_core"}, "CIA, Zero Trust, Threats, SOC & GRC"),
    ("2", "Networking", {"2_network_operations", "networking"}, "OSI, TCP Handshake, Routing & CLI"),
    ("3", "Electronics", {"1_electronics_fundamentals", "electronics"}, "Ohm's Law, Circuits, Logic & MCUs"),
    ("4", "Python & Ops", {"4_python_automation"}, "Data, Regex, Sockets & Subprocesses"),
]


def load_all_diagrams() -> list[dict]:
    items = []
    if not DIAGRAMS_ROOT.exists():
        return items
    for jf in sorted(DIAGRAMS_ROOT.rglob("*.json")):
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "art" in data and "nodes" in data:
                data["_category"] = jf.parent.name
                data["_file"] = jf.name
                items.append(data)
        except Exception:
            continue
    return items


def load_glossary() -> list[dict]:
    if not GLOSSARY_PATH.exists():
        return []
    try:
        data = json.loads(GLOSSARY_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _short_title(diag: dict) -> str:
    title = diag.get("title", diag.get("_file", "Schematic"))
    # Strip verbose prefixes like "Core Security Domain 1: " for crisp list rows
    if ":" in title and len(title.split(":", 1)[0]) <= 26:
        title = title.split(":", 1)[1].strip()
    return ui.truncate_vis(title, 46)


def play_diagram_quiz(
    diag: dict,
    muted: bool,
    bgm: BackgroundBeat | None = None,
) -> bool:
    nodes = diag.get("nodes", {})
    all_labels = [n.get("label", "") for n in nodes.values() if n.get("label")]
    rng = random.Random()
    ordered = sorted(nodes.items(), key=lambda kv: int(kv[0]) if kv[0].isdigit() else 99)

    for step_idx, (node_id, info) in enumerate(ordered, 1):
        target_label = info.get("label", f"Node {node_id}")
        distractors = [lbl for lbl in all_labels if lbl != target_label]
        rng.shuffle(distractors)
        choices = [target_label] + distractors[:3]
        rng.shuffle(choices)
        win_idx = choices.index(target_label)

        while True:
            clear()
            ui.header(
                f"DIAGRAM · {_short_title(diag)}",
                badge=f"(?{node_id}) {step_idx}/{len(ordered)}",
                muted=muted,
                bgm=bgm,
            )
            print()
            for line in diag.get("art", []):
                highlighted = line.replace(f"(?{node_id})", f"{BOLD}{PINK}(?{node_id}){RST}{CYAN}")
                print(f"  {CYAN}{highlighted}{RST}")

            print(f"\n  {BOLD}Identify node {PINK}(?{node_id}){RST}{BOLD}:{RST}")
            for i, c in enumerate(choices, 1):
                print(f"    {CYAN}[{i}]{RST} {ui.truncate_vis(c, 62)}")

            ui.footer([(f"1-{len(choices)}", "Pick"), ("V", "Vibe"), ("M", "Mute"), ("B", "Back")])

            ch = getch().lower()
            if ch == "m":
                muted = ui.toggle_mute(muted, bgm)
                continue
            if ch == "v":
                muted = ui.cycle_vibe(muted, bgm)
                play_sfx("blip", muted)
                continue
            if ch in {"b", "q"}:
                return muted
            if ch not in {str(i) for i in range(1, len(choices) + 1)}:
                continue

            if int(ch) - 1 == win_idx:
                play_sfx("good", muted)
                clear()
                ui.header(f"DIAGRAM · {_short_title(diag)}", badge="LOCKED IN", muted=muted, bgm=bgm)
                ui.wolf_say("happy", f"{MINT}{BOLD}✔ (?{node_id}) = {target_label}{RST}", f"{DIM}Nice eye!{RST}")
                print()
                facts: list[str] = []
                if info.get("what"):
                    facts.append(f"What: {info['what']}")
                tip = info.get("exam_facts") or info.get("mastery") or info.get("troubleshoot")
                if tip:
                    facts.append(f"Key Fact: {tip}")
                if facts:
                    ui.panel("STUDY CARD", facts, color=MINT)
                print(f"\n  {DIM}Press any key for next node...{RST}")
                getch()
                break
            else:
                play_sfx("bad", muted)
                clear()
                ui.header(f"DIAGRAM · {_short_title(diag)}", badge="RETRY", muted=muted, bgm=bgm)
                ui.wolf_say(
                    "study",
                    f"{RED}{BOLD}✘ Not quite!{RST}",
                    f"Look closely at {PINK}(?{node_id}){RST} on the diagram.",
                )
                print(f"\n  {DIM}Press any key to retry...{RST}")
                getch()

    play_sfx("fanfare", muted)
    return muted


def _run_category(
    label: str,
    items: list[dict],
    muted: bool,
    bgm: BackgroundBeat | None = None,
) -> bool:
    while True:
        clear()
        ui.header(f"DIAGRAMS · {label}", badge=f"{len(items)} decks", muted=muted, bgm=bgm)
        ui.wolf_say("study", f"{BOLD}{label}{RST}", f"{DIM}Pick a schematic — single key, no Enter needed!{RST}")
        print()
        for idx, d in enumerate(items[:9], 1):
            nodes_n = len(d.get("nodes", {}))
            print(f"  {CYAN}[{idx}]{RST} {BOLD}{ui.pad_vis(_short_title(d), 48)}{RST} {DIM}{nodes_n} nodes{RST}")

        ui.footer([(f"1-{min(9, len(items))}", "Open"), ("V", "Vibe"), ("M", "Mute"), ("B", "Tabs")])
        ch = getch().lower()
        if ch in {"b", "q"}:
            return muted
        if ch == "m":
            muted = ui.toggle_mute(muted, bgm)
            continue
        if ch == "v":
            muted = ui.cycle_vibe(muted, bgm)
            play_sfx("blip", muted)
            continue
        if ch.isdigit() and 1 <= int(ch) <= min(9, len(items)):
            play_sfx("blip", muted)
            muted = play_diagram_quiz(items[int(ch) - 1], muted, bgm)


def run_menu(muted: bool = False, bgm: BackgroundBeat | None = None) -> bool:
    diagrams = load_all_diagrams()
    total_nodes = sum(len(d["nodes"]) for d in diagrams)

    while True:
        clear()
        ui.header("WOLF-SOC · TECH DIAGRAMS", badge=f"{len(diagrams)} schematics", muted=muted, bgm=bgm)
        ui.wolf_say(
            "study",
            f"{BOLD}Interactive ASCII Blueprints{RST}",
            f"{DIM}{len(diagrams)} schematics · {total_nodes} quiz nodes — pick a tab!{RST}",
        )
        print()

        tab_buckets: dict[str, tuple[str, list[dict]]] = {}
        for key, name, folders, desc in CATEGORY_TABS:
            bucket = [d for d in diagrams if d.get("_category") in folders]
            tab_buckets[key] = (name, bucket)
            count_tag = f"{GOLD}({len(bucket)}){RST}"
            print(f"  {CYAN}[{key}]{RST} {BOLD}{ui.pad_vis(name, 15)}{RST} {ui.pad_vis(count_tag, 4)}  {DIM}{desc}{RST}")

        ui.footer([("1-4", "Category"), ("V", "Vibe"), ("M", "Mute"), ("B", "Back")])
        ch = getch().lower()
        if ch in {"b", "q"}:
            return muted
        if ch == "m":
            muted = ui.toggle_mute(muted, bgm)
        elif ch == "v":
            muted = ui.cycle_vibe(muted, bgm)
            play_sfx("blip", muted)
        elif ch in tab_buckets and tab_buckets[ch][1]:
            play_sfx("blip", muted)
            name, bucket = tab_buckets[ch]
            muted = _run_category(name, bucket, muted, bgm)


def main() -> None:
    run_menu(muted=False, bgm=None)


if __name__ == "__main__":
    bgm = BackgroundBeat()
    bgm.start()
    sys.stdout.write("\033[?1049h\033[?25l")
    sys.stdout.flush()
    try:
        run_menu(muted=False, bgm=bgm)
    finally:
        bgm.stop()
        sys.stdout.write("\033[?25h\033[?1049l")
        sys.stdout.flush()
