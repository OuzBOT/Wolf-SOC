#!/usr/bin/env python3
"""
Wolf-SOC Visual Stick-Figure Mini-Labs (Pure stdlib, 72-col aligned UI).
Interactive ASCII scenes where your choices visibly change the world state.
"""

from __future__ import annotations

from synth_engine import BackgroundBeat, play_sfx
import ui_core as ui

RST, BOLD, DIM = ui.RST, ui.BOLD, ui.DIM
CYAN, PINK, MINT, GOLD, RED, PURP = ui.CYAN, ui.PINK, ui.MINT, ui.GOLD, ui.RED, ui.PURP

# Patchable hooks for unit tests
getch = ui.getch
clear = ui.clear

LABS: list[dict] = [
    {
        "id": 1,
        "title": "Physical Mantrap & Tailgating Gate",
        "tag": "Domain 1.2",
        "briefing": (
            "An employee badges into the server room. A visitor holding coffee boxes "
            "walks right behind them without swiping a badge."
        ),
        "scene_before": [
            " EMPLOYEE   TAILGATER     [BADGE READER]      SERVER ROOM",
            "    O           O              [o]            +----------+",
            "   /|\\         /|\\[BOX]   |  DOOR: OPEN  |    | [RACK-1] |",
            "   / \\         / \\ --->   |              |    | [RACK-2] |",
            " ==========================================================",
        ],
        "scene_after_ok": [
            " EMPLOYEE   VISITOR       [MANTRAP LOCKED]    SERVER ROOM",
            "    O           O              [X]            +----------+",
            "   /|\\         /|\\[BOX]   | == LOCKED == |    | [RACK-1] |",
            "   / \\         / \\ STOP!  | [LOGGED #42] |    | [RACK-2] |",
            " ==========================================================",
        ],
        "scene_after_bad": [
            "            INTRUDER!     [DOOR UNGUARDED]    SERVER ROOM",
            "                O              [!]            +----------+",
            "               /|\\[USB]   |  DOOR: OPEN  |    | [RACK-1] |",
            "               / \\ --->   |  NO ALERT!   |    | [PWNED!] |",
            " ==========================================================",
        ],
        "prompt": "What action do you take at the mantrap vestibule?",
        "choices": [
            (
                "Enforce single-badge mantrap interlock & escort visitor to reception",
                True,
                "Mantraps and access control vestibules physically isolate one person per badge scan, stopping tailgating/piggybacking cold.",
            ),
            (
                "Hold the door open so they don't drop the coffee boxes",
                False,
                "Politeness is the #1 social engineering lever for tailgating. Never allow unbadged entry into restricted zones.",
            ),
            (
                "Let them in and ask for their name later",
                False,
                "Once an unauthorized person reaches the racks, a rogue USB implant or console hijack takes under 15 seconds.",
            ),
        ],
    },
    {
        "id": 2,
        "title": "SSH Brute-Force & Perimeter Shield",
        "tag": "Domain 2.4",
        "briefing": (
            "Your SIEM lights up: 203.0.113.4 is firing 400 SSH login attempts/sec "
            "at WEB-01 across the perimeter firewall."
        ),
        "scene_before": [
            " ATTACKER       INTERNET          FIREWALL        SOC DESK",
            "    O        ==> SSH SYN ==>     [  PASS  ]           O",
            "   /|\\ [113] ==> SSH SYN ==>     [PORT  22]  --->    /|\\[PC]",
            "   / \\       ==> SSH SYN ==>     [OPEN ALL]          / \\",
            " ==========================================================",
        ],
        "scene_after_ok": [
            " ATTACKER       INTERNET          FIREWALL        SOC DESK",
            "    O        ==> SSH SYN => X    [##DENY##]           O",
            "   /|\\ [113] ==> SSH SYN => X    [FW  DROP]  SAFE!   \\|/[OK]",
            "   / \\       ==> SSH SYN => X    [KEY-ONLY]          / \\",
            " ==========================================================",
        ],
        "scene_after_bad": [
            " ATTACKER       INTERNET          FIREWALL        SOC DESK",
            "    O        =============>      [OPEN 22!]           O",
            "   /|\\ [ROOT]== SHELL ====>      [NO BLOCK]  ALERT!  /_\\[?!]",
            "   / \\                                               / \\",
            " ==========================================================",
        ],
        "prompt": "Which containment step locks down the perimeter immediately?",
        "choices": [
            (
                "Block 203.0.113.4 at firewall + enforce key-only SSH auth",
                True,
                "Blocking the malicious source IP at the perimeter stops the flood immediately, and disabling password auth kills credential brute-force.",
            ),
            (
                "Reboot WEB-01 without changing firewall or SSH rules",
                False,
                "As soon as WEB-01 boots back up, the automated brute-force script resumes hitting port 22.",
            ),
            (
                "Move SSH to port 2222 and leave root password login enabled",
                False,
                "Security through obscurity (port change alone) takes a port scanner seconds to bypass.",
            ),
        ],
    },
    {
        "id": 3,
        "title": "ESD Grounding & Parallel DMM Check",
        "tag": "Bench Safety",
        "briefing": (
            "You need to measure the 12V rail on an exposed motherboard using a "
            "Digital Multimeter (DMM) without zapping CMOS chips."
        ),
        "scene_before": [
            " TECH (UNGROUNDED)       WORKBENCH             DMM METER",
            "        O               +---------+           +---------+",
            "       /|\\ [STATIC!]    |  [PCB]  |           | 00.0 V  |",
            "       / \\              |[ESD MAT]|           |[10A][V] |",
            " ==========================================================",
        ],
        "scene_after_ok": [
            " TECH (GROUNDED)         WORKBENCH             DMM METER",
            "        O               +---------+           +---------+",
            "       /|\\-[1MΩ]--+     |[PCB 12V]|=========> | 12.04 V |",
            "       / \\        |     |[ESD MAT]| PARALLEL  |[V/Ω][C] |",
            " ================[GND]=====================================",
        ],
        "scene_after_bad": [
            " TECH (ZAP! 3000V)       WORKBENCH             DMM METER",
            "       \\O/ *SPARK!*     +---------+           +---------+",
            "        |               |[FRIED!] |           |FUSE OUT!|",
            "       / \\              |[ESD MAT]|           |  [10A]  |",
            " ==========================================================",
        ],
        "prompt": "What is the safe order of operations on the bench?",
        "choices": [
            (
                "Wear 1MΩ ESD strap to earth ground, probe in Parallel (V/Ω + COM)",
                True,
                "Grounding via a 1MΩ resistor safely bleeds static charge, and Voltage is always measured in parallel using V/Ω and COM jacks.",
            ),
            (
                "Touch board first, then put DMM in Series on 10A jack to read Volts",
                False,
                "Placing an ammeter (10A jack) across a power rail shorts the supply and blows the DMM fuse, while ungrounded touch causes ESD damage.",
            ),
            (
                "Stand on carpet without a wrist strap so you stay insulated",
                False,
                "Walking on carpet builds up thousands of volts of static charge that discharges straight into sensitive ICs.",
            ),
        ],
    },
    {
        "id": 4,
        "title": "Dropped USB Drive in Parking Lot",
        "tag": "Domain 2.2",
        "briefing": (
            "On your way into work, you spot a shiny USB drive labeled "
            "'EXEC_BONUS_2026.xlsx' lying near the front walkway."
        ),
        "scene_before": [
            " ANALYST      PARKING LOT              CORP BUILDING",
            "    O                                +-----------------+",
            "   /|\\         [USB: BONUS]          |  [PROD PC]      |",
            "   / \\                               |  [SANDBOX LAB]  |",
            " ==========================================================",
        ],
        "scene_after_ok": [
            " ANALYST      PARKING LOT              CORP BUILDING",
            "                                     +-----------------+",
            "                (CLEAR)              |  [PROD PC: SAFE]|",
            "                                O -> |  [SANDBOX: HID!]|",
            " ==========================================================",
        ],
        "scene_after_bad": [
            " ANALYST      PARKING LOT              CORP BUILDING",
            "                                     +-----------------+",
            "                (CLEAR)         O -> |  [PROD PC: BAD!]|",
            "                               /|\\   |  BadUSB Inject! |",
            " ==========================================================",
        ],
        "prompt": "How do you handle the mystery USB drive?",
        "choices": [
            (
                "Bag it and hand it to IR/Security for air-gapped Sandbox analysis",
                True,
                "USB baiting often uses BadUSB HID keystroke injection. Only an isolated, non-networked sandbox should inspect untrusted media.",
            ),
            (
                "Plug it into your work laptop with antivirus running to check owner",
                False,
                "HID spoofing devices masquerade as a USB keyboard and type malicious commands faster than AV prompts.",
            ),
            (
                "Plug it into a lobby kiosk PC just to inspect the file names",
                False,
                "Lobby kiosks are often connected to internal VLANs or share credentials—never plug untrusted media into any live host.",
            ),
        ],
    },
]


def run_single_lab(
    lab: dict,
    muted: bool = False,
    bgm: BackgroundBeat | None = None,
) -> bool:
    """Run one interactive visual stick-figure mini-lab."""
    state = "before"  # "before", "ok", "bad"
    feedback = ""
    while True:
        clear()
        mood = "study" if state == "before" else ("hype" if state == "ok" else "alert")
        ui.header(f"MINI-LAB {lab['id']} · {lab['title']}", badge=lab["tag"], muted=muted, bgm=bgm)
        ui.wolf_say(
            mood,
            f"{BOLD}{lab['title']}{RST}",
            f"{DIM}{ui.truncate_vis(lab['briefing'], 56)}{RST}",
        )
        print()

        if state == "before":
            scene = lab["scene_before"]
            sc_color = CYAN
            panel_title = "LIVE SCENE"
        elif state == "ok":
            scene = lab["scene_after_ok"]
            sc_color = MINT
            panel_title = "SCENE SECURED"
        else:
            scene = lab["scene_after_bad"]
            sc_color = RED
            panel_title = "INCIDENT TRIGGERED"

        ui.panel(panel_title, [f"{sc_color}{ln}{RST}" for ln in scene], color=sc_color)
        print()

        if state == "before":
            print(f"  {BOLD}{lab['prompt']}{RST}")
            for idx, (label, _, _) in enumerate(lab["choices"], 1):
                print(f"    {CYAN}[{idx}]{RST} {ui.truncate_vis(label, 62)}")
            ui.footer([("1-3", "Act"), ("V", "Vibe"), ("M", "Mute"), ("B", "Back")])

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
            if ch in {"1", "2", "3"}:
                _, is_ok, msg = lab["choices"][int(ch) - 1]
                feedback = msg
                if is_ok:
                    state = "ok"
                    play_sfx("good", muted)
                else:
                    state = "bad"
                    play_sfx("bad", muted)
        elif state == "ok":
            ui.panel("OBJECTIVE COMPLETE", [feedback], color=MINT)
            ui.footer([("R", "Replay"), ("Any Key", "Continue")])
            ch = getch().lower()
            if ch == "r":
                state = "before"
                continue
            return muted
        else:
            ui.panel("WHAT WENT WRONG", [feedback], color=GOLD)
            print(f"\n  {DIM}Press any key to rewind the scene and try again...{RST}")
            getch()
            state = "before"


def run_menu(
    muted: bool = False,
    bgm: BackgroundBeat | None = None,
) -> bool:
    """Interactive selector for all visual stick-figure mini-labs."""
    while True:
        clear()
        ui.header("WOLF-SOC · VISUAL MINI-LABS", badge=f"{len(LABS)} Scenes", muted=muted, bgm=bgm)
        ui.wolf_say(
            "idle",
            f"{BOLD}Interactive ASCII Scenes (O /|\\ /\\){RST}",
            f"{DIM}Pick a lab, choose a response, and watch the scene react live.{RST}",
        )
        print()

        for lab in LABS:
            title_pad = ui.pad_vis(lab["title"], 42)
            print(f"  {CYAN}[{lab['id']}]{RST} {BOLD}{title_pad}{RST} {DIM}│ {lab['tag']}{RST}")

        ui.footer([(f"1-{len(LABS)}", "Enter Lab"), ("V", "Vibe"), ("M", "Mute"), ("B", "Back")])

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
        if ch.isdigit() and 1 <= int(ch) <= len(LABS):
            play_sfx("blip", muted)
            muted = run_single_lab(LABS[int(ch) - 1], muted=muted, bgm=bgm)


if __name__ == "__main__":
    import sys

    sys.stdout.write("\033[?1049h\033[?25l")
    sys.stdout.flush()
    try:
        run_menu(muted=True)
    finally:
        sys.stdout.write("\033[?25h\033[?1049l")
        sys.stdout.flush()
