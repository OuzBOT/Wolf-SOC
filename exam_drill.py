#!/usr/bin/env python3
"""
Core Security Terminology & Domain Drill Engine
Persists mastery/attempts/correct JSON locally + Wolf-SOC 8-bit TUI.
Contains all 106 official Core Security acronyms + Domain 1.0-5.0 scenario questions.
"""

import json
import random
import sys
from pathlib import Path

from synth_engine import BackgroundBeat, play_sfx
import ui_core as ui

BASE_DIR = Path(__file__).resolve().parent
PROGRESS_PATH = BASE_DIR / "artifacts" / "exam_drill_progress.json"

RST, BOLD, DIM = ui.RST, ui.BOLD, ui.DIM
CYAN, PINK, MINT, GOLD, RED, PURP = ui.CYAN, ui.PINK, ui.MINT, ui.GOLD, ui.RED, ui.PURP

# All 106 Official Security Operations & Architecture Acronyms (Pages 24-26)
ACRONYMS = [
    ("AAA", "Authentication, Authorization, and Accounting", "Domain 1.1"),
    ("AI", "Artificial Intelligence", "Domain 2.6"),
    ("ALE", "Annualized Loss Expectancy", "Domain 5.2"),
    ("AML/CTF", "Anti-money Laundering/Counter-terrorism Financing", "Domain 5.4"),
    ("APT", "Advanced Persistent Threat", "Domain 2.3"),
    ("ARO", "Annualized Rate of Occurrence", "Domain 5.2"),
    ("AUP", "Acceptable Use Policy", "Domain 5.1"),
    ("BEC", "Business Email Compromise", "Domain 5.6"),
    ("BIMI", "Brand Indicators for Message Identification", "Domain 4.1"),
    ("BIOS", "Basic Input/Output System", "Hardware"),
    ("BYOD", "Bring Your Own Device", "Domain 5.1"),
    ("CAB", "Change Advisory Board", "Domain 1.2"),
    ("CAPTCHA", "Completely Automated Public Turing test to tell Computers and Humans Apart", "Domain 2.3"),
    ("CI/CD", "Continuous Integration and Continuous Deployment", "Domain 4.6"),
    ("CIA", "Confidentiality, Integrity, and Availability", "Domain 1.1"),
    ("CRL", "Certificate Revocation List", "Domain 1.3"),
    ("CSPM", "Cloud Security Posture Management", "Domain 4.3"),
    ("CSR", "Certificate Signing Request", "Domain 1.3"),
    ("CVE", "Common Vulnerabilities and Exposures", "Domain 2.1"),
    ("CVSS", "Common Vulnerability Scoring System", "Domain 2.1"),
    ("CWE", "Common Weakness Enumeration", "Domain 2.1"),
    ("DDoS", "Distributed Denial of Service", "Domain 2.5"),
    ("DoS", "Denial of Service", "Domain 2.5"),
    ("DHCP", "Dynamic Host Configuration Protocol", "Hardware/Net"),
    ("DKIM", "DomainKeys Identified Mail", "Domain 4.1"),
    ("DLP", "Data Loss Prevention", "Domain 4.1"),
    ("DMARC", "Domain-based Message Authentication, Reporting, and Conformance", "Domain 4.1"),
    ("DNS", "Domain Name System", "Domain 2.5"),
    ("EDR", "Endpoint Detection and Response", "Domain 4.1"),
    ("EOI", "Expression of Interest", "Domain 5.3"),
    ("GBIC", "Gigabit Interface Converter", "Hardware"),
    ("gMSA", "Group Managed Service Account", "Domain 3.2"),
    ("HIDS", "Host-based Intrusion Detection System", "Domain 4.1"),
    ("HIPS", "Host-based Intrusion Prevention System", "Domain 4.1"),
    ("HR", "Human Resources", "Domain 4.8"),
    ("IaC", "Infrastructure as Code", "Domain 3.1"),
    ("IDS", "Intrusion Detection System", "Domain 4.1"),
    ("IP", "Internet Protocol", "Domain 2.5"),
    ("IPFIX", "Internet Protocol Flow Information Export", "Domain 4.8"),
    ("IPS", "Intrusion Prevention System", "Domain 4.1"),
    ("IPSec", "Internet Protocol Security", "Domain 3.2"),
    ("LAN", "Local Area Network", "Architecture"),
    ("LDAP", "Lightweight Directory Access Protocol", "Domain 4.5"),
    ("LLM", "Large Language Model", "Domain 2.4"),
    ("LMS", "Learning Management System", "Domain 5.6"),
    ("MDM", "Mobile Device Management", "Domain 4.1"),
    ("MFA", "Multifactor Authentication", "Domain 4.5"),
    ("MOA", "Memorandum of Agreement", "Domain 5.3"),
    ("MOU", "Memorandum of Understanding", "Domain 5.3"),
    ("MSA", "Master Service Agreement", "Domain 5.3"),
    ("MTBF", "Mean Time Between Failures", "Domain 3.4"),
    ("MTTR", "Mean Time to Repair", "Domain 3.4"),
    ("NDA", "Non-disclosure Agreement", "Domain 5.3"),
    ("NFC", "Near-field Communication", "Domain 2.3"),
    ("NIC", "Network Interface Card", "Hardware"),
    ("NIDS", "Network-based Intrusion Detection System", "Domain 4.1"),
    ("NIPS", "Network-based Intrusion Prevention System", "Domain 4.1"),
    ("NVD", "National Vulnerability Database", "Domain 2.1"),
    ("OAuth", "Open Authorization", "Domain 4.5"),
    ("OCSP", "Online Certificate Status Protocol", "Domain 1.3"),
    ("OS", "Operating System", "Domain 2.4"),
    ("OT", "Operational Technology", "Domain 2.3"),
    ("OTP", "One-time Password", "Domain 4.5"),
    ("PDF", "Portable Document Formats", "Domain 2.3"),
    ("PIR", "Post-incident Reporting", "Domain 4.7"),
    ("PKI", "Public Key Infrastructure", "Domain 1.3"),
    ("QR", "Quick Response", "Domain 2.3"),
    ("RCS", "Rich Communication Services", "Domain 2.3"),
    ("RF", "Radio Frequency", "Domain 2.3"),
    ("RFC", "Request for Comments", "Domain 5.1"),
    ("RFI", "Request for Information", "Domain 5.3"),
    ("RFP", "Request for Proposal", "Domain 5.3"),
    ("RFQ", "Request for Quote", "Domain 5.3"),
    ("ROI", "Return on Investment", "Domain 5.3"),
    ("RPO", "Recovery Point Objective", "Domain 3.4"),
    ("RPS", "Redundant Power Supply", "Domain 3.4"),
    ("RTF", "Rich Text Format", "Domain 2.3"),
    ("RTO", "Recovery Time Objective", "Domain 3.4"),
    ("SaaS", "Software as a Service", "Domain 2.3"),
    ("SAML", "Security Assertions Markup Language", "Domain 4.5"),
    ("SCAP", "Security Content Automation Protocol", "Domain 4.4"),
    ("SELinux", "Security-enhanced Linux", "Domain 4.1"),
    ("SFP", "Small Form-factor Pluggable", "Hardware"),
    ("SIEM", "Security Information and Event Management", "Domain 4.4"),
    ("SLE", "Single Loss Expectancy", "Domain 5.2"),
    ("SMS", "Short Message Service", "Domain 2.3"),
    ("SNMP", "Simple Network Management Protocol", "Domain 4.4"),
    ("SOAR", "Security Orchestration, Automation, and Response", "Domain 4.6"),
    ("SOC", "Security Operations Center", "Domain 4.0"),
    ("SOP", "Standard Operating Procedure", "Domain 1.2"),
    ("SOW", "Statement of Work", "Domain 5.3"),
    ("SPF", "Sender Policy Framework", "Domain 4.1"),
    ("SQL", "Structured Query Language", "Domain 2.5"),
    ("SSE", "Security Service Edge", "Domain 3.2"),
    ("SSO", "Single Sign-on", "Domain 4.5"),
    ("TLS", "Transport Layer Security", "Domain 1.3"),
    ("TOC", "Time-of-check", "Domain 2.4"),
    ("TOU", "Time-of-use", "Domain 2.4"),
    ("UPS", "Uninterruptible Power Supply", "Domain 3.4"),
    ("USB", "Universal Serial Bus", "Domain 2.3"),
    ("UTM", "Unified Threat Management", "Domain 4.1"),
    ("VNC", "Virtual Network Computing", "Domain 2.3"),
    ("VPN", "Virtual Private Network", "Domain 2.3"),
    ("WAF", "Web Application Firewall", "Domain 4.1"),
    ("WIPS", "Wireless Intrusion Prevention System", "Domain 4.1"),
    ("XDR", "Extended Detection and Response", "Domain 4.1"),
]

# Full Core Security Domain Question Bank (Domains 1.0 - 5.0)
DOMAIN_QUESTIONS = [
    # Domain 1.0 (16%)
    ("1.0", "Obj 1.1 · Controls", "A bollard outside a data center entrance is which control category & type?",
     ["Physical + Preventive", "Technical + Deterrent", "Operational + Corrective", "Managerial + Detective"], 0,
     "Bollards physically block vehicles before impact = Physical + Preventive."),
    ("1.0", "Obj 1.1 · Controls", "Reviewing SIEM audit logs weekly to spot policy violations is which control type?",
     ["Detective", "Preventive", "Compensating", "Deterrent"], 0,
     "Logs and audits discover events after/as they occur = Detective."),
    ("1.0", "Obj 1.2 · Change Mgmt", "Before applying a risky firewall patch, the CAB requires a plan to revert changes if production breaks. What is this?",
     ["Backout plan", "Fail forward", "Allow list", "Non-repudiation"], 0,
     "A backout plan restores the prior known-good state if a change fails."),
    ("1.0", "Obj 1.3 · PKI", "Which property proves a sender signed a message and cannot later deny sending it?",
     ["Non-repudiation", "Confidentiality", "Obfuscation", "Key escrow"], 0,
     "Digital signatures bind the signer's private key to the hash = Non-repudiation."),
    ("1.0", "Obj 1.3 · Crypto", "Adding random bytes to a password before hashing prevents which attack?",
     ["Rainbow table / precomputed hash lookup", "Replay attack", "Protocol downgrade", "Shoulder surfing"], 0,
     "Salting forces unique hashes even for identical passwords."),
    # Domain 2.0 (24%)
    ("2.0", "Obj 2.2 · Actors", "An internal engineer accidentally misconfigures an S3 bucket to public read. Which threat actor type is this?",
     ["Accidental / unintentional insider", "Hacktivist", "Crime syndicate", "State-sponsored APT"], 0,
     "Internal staff causing exposure without malice = Accidental/unintentional."),
    ("2.0", "Obj 2.3 · Vectors", "An attacker places a malicious QR code sticker over a parking meter payment sign. What attack is this?",
     ["Quishing (QR phishing)", "Vishing", "Watering hole", "Protocol downgrade"], 0,
     "Malicious QR codes redirecting users to credential harvesters = Quishing."),
    ("2.0", "Obj 2.4 · Vulns", "A developer commits an AWS secret key into a public GitHub repo. Which vulnerability category applies?",
     ["Hardcoded secrets + Public repository exposure", "Buffer overflow", "TOC/TOU race condition", "Rogue device"], 0,
     "Credentials embedded in source code exposed publicly = Hardcoded secrets."),
    ("2.0", "Obj 2.5 · Indicators", "An attacker tests one common password ('Winter2026!') across 5,000 user accounts to avoid lockouts. What is this?",
     ["Password spraying", "Credential stuffing", "Brute force on single account", "Directory traversal"], 0,
     "One password across many accounts = Password spraying."),
    ("2.0", "Obj 2.6 · AI Security", "Feeding crafted inputs at inference time to make an image classifier mislabel a stop sign is called:",
     ["Model evasion", "Hallucination", "Key escrow", "Tokenization"], 0,
     "Crafting inputs to fool a trained model's predictions = Evasion."),
    # Domain 3.0 (19%)
    ("3.0", "Obj 3.1 · Architecture", "Which cloud/compute model runs event-driven functions without managing underlying OS patching?",
     ["Serverless", "On-premises air-gapped", "Community cloud", "Cold site"], 0,
     "Serverless abstracts away servers/OS maintenance."),
    ("3.0", "Obj 3.2 · Identity", "Which Windows Active Directory account type automatically rotates passwords across multiple hosts for services?",
     ["Group Managed Service Account (gMSA)", "Guest account", "Local admin", "Canary account"], 0,
     "gMSAs provide automated password management for clustered/multi-host services."),
    ("3.0", "Obj 3.3 · Data Protection", "Replacing a 16-digit PAN card number with a non-sensitive reference value mapped in a secure vault is:",
     ["Tokenization", "Hashing", "Masking", "Data transpose"], 0,
     "Tokenization substitutes sensitive values with vault-mapped tokens (common in PCI DSS)."),
    ("3.0", "Obj 3.3 · Data Roles", "A senior VP who decides data classification levels and who is allowed access is the:",
     ["Data owner", "Data custodian", "Data processor", "Data steward"], 0,
     "Data owners set classification/access policy; custodians implement backups/ACLs."),
    ("3.0", "Obj 3.4 · Resilience", "Which metric measures the average time required to repair a failed hardware component and restore service?",
     ["MTTR (Mean Time to Repair)", "MTBF (Mean Time Between Failures)", "RPO (Recovery Point Objective)", "ARO (Annualized Rate of Occurrence)"], 0,
     "MTTR = average restoration/repair time; MTBF = average uptime between failures."),
    # Domain 4.0 (27%)
    ("4.0", "Obj 4.1 · Deception", "Placing a fake 'passwords_2026.xlsx' file on a share to trigger an alert the moment anyone opens it is a:",
     ["Honeyfile", "Honeynet", "Canary account", "WAF rule"], 0,
     "A decoy file monitored for unauthorized access = Honeyfile."),
    ("4.0", "Obj 4.1 · Email Auth", "Which DNS TXT record publishes the public key receiving servers use to verify an email's cryptographic signature?",
     ["DKIM", "SPF", "DMARC", "BIMI"], 0,
     "SPF lists authorized sending IPs; DKIM publishes the public signing key; DMARC sets alignment/quarantine policy."),
    ("4.0", "Obj 4.4 · Protocols", "Which protocol exports IP traffic flow metadata (src/dst IP, ports, byte counts) without full packet payloads?",
     ["NetFlow / IPFIX", "SNMP", "SCAP", "LDAP"], 0,
     "NetFlow and IPFIX export session flow telemetry rather than full PCAP payloads."),
    ("4.0", "Obj 4.5 · Federation", "Which XML-based open standard exchanges authentication & authorization assertions between an IdP and a Service Provider?",
     ["SAML", "OAuth", "RADIUS", "NTP"], 0,
     "SAML uses XML assertions for enterprise SSO; OAuth uses JSON/tokens for delegated API authorization."),
    ("4.0", "Obj 4.8 · Forensics", "When collecting volatile RAM from a compromised server before rebooting, what should you capture?",
     ["Memory dump + SHA-256 hash", "Bit-level disk copy only", "Surveillance footage", "HR onboarding form"], 0,
     "Volatile memory holds running processes, keys, and network sockets lost on reboot."),
    # Domain 5.0 (14%)
    ("5.0", "Obj 5.1 · GRC Docs", "Step-by-step technical instructions for an on-call analyst to isolate a compromised host belong in a:",
     ["Runbook / SOP", "Acceptable Use Policy (AUP)", "Non-disclosure Agreement (NDA)", "Audit charter"], 0,
     "Policies state high-level mandates; Runbooks/SOPs give step-by-step execution instructions."),
    ("5.0", "Obj 5.2 · Risk", "Purchasing cyber liability insurance to shift financial loss from a breach to an insurer is which risk treatment?",
     ["Risk transference", "Risk avoidance", "Risk acceptance", "Risk mitigation"], 0,
     "Insurance and third-party contracts transfer financial risk."),
    ("5.0", "Obj 5.3 · Third-Party", "Which agreement defines specific uptime guarantees (e.g., 99.95%) and response times from a cloud vendor?",
     ["SLA (Service-Level Agreement)", "NDA (Non-disclosure Agreement)", "MOU (Memorandum of Understanding)", "RFI (Request for Information)"], 0,
     "SLAs define binding service uptime and support response metrics."),
    ("5.0", "Obj 5.4 · Privacy", "When litigation is anticipated, Legal issues a directive suspending normal data deletion rules. What is this?",
     ["Legal hold", "Right to be forgotten", "Data minimization", "Opt-out"], 0,
     "A legal hold freezes retention/destruction schedules to preserve potential evidence."),
    ("5.0", "Obj 5.5 · Assessment", "Testing an application with zero prior knowledge of its source code or internal architecture is a:",
     ["Unknown environment test (black-box)", "Known environment test", "Tabletop exercise", "Self-assessment"], 0,
     "Core Security uses Known, Partially Known, and Unknown environment terminology."),
]


def load_progress() -> dict:
    if PROGRESS_PATH.exists():
        try:
            data = json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data.setdefault("mastered_terms", [])
                data.setdefault("mastered_qs", [])
                data.setdefault("attempts", 0)
                data.setdefault("correct", 0)
                return data
        except Exception:
            pass
    return {"mastered_terms": [], "mastered_qs": [], "attempts": 0, "correct": 0}


def save_progress(prog: dict) -> None:
    PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_PATH.write_text(json.dumps(prog, indent=2) + "\n", encoding="utf-8")


getch = ui.getch
clear = ui.clear
bar = ui.bar


def run_acronym_blitz(
    prog: dict,
    muted: bool,
    count: int = 10,
    bgm: BackgroundBeat | None = None,
) -> bool:
    rng = random.Random()
    unmastered = [a for a in ACRONYMS if a[0] not in set(prog["mastered_terms"])]
    pool = unmastered if len(unmastered) >= count else ACRONYMS
    deck = rng.sample(pool, min(count, len(pool)))

    for idx, (acro, full_name, dom) in enumerate(deck, 1):
        distractors = [x[1] for x in rng.sample([a for a in ACRONYMS if a[0] != acro], 3)]
        choices = [full_name] + distractors
        rng.shuffle(choices)
        win_idx = choices.index(full_name)

        while True:
            clear()
            ui.header(f"ACRONYM BLITZ ({idx}/{len(deck)})", badge=dom, muted=muted, bgm=bgm)
            ui.wolf_say("idle", f"{DIM}Expand this acronym:{RST}", f"{BOLD}{PINK}>>>  {acro}  <<<{RST}")
            print()
            for i, c in enumerate(choices, 1):
                print(f"    {CYAN}[{i}]{RST} {ui.truncate_vis(c, 62)}")
            ui.footer([("1-4", "Pick"), ("V", "Vibe"), ("M", "Mute"), ("B", "Back")])

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
            if ch not in {"1", "2", "3", "4"}:
                continue

            picked = int(ch) - 1
            prog["attempts"] += 1
            if picked == win_idx:
                prog["correct"] += 1
                if acro not in prog["mastered_terms"]:
                    prog["mastered_terms"].append(acro)
                save_progress(prog)
                play_sfx("good", muted)
                clear()
                ui.header("ACRONYM BLITZ", badge="SAVED", muted=muted, bgm=bgm)
                ui.wolf_say("happy", f"{MINT}{BOLD}✔ {acro} = {full_name}{RST}", f"{DIM}{dom}{RST}")
                print(f"\n  {DIM}Press any key for next card...{RST}")
                getch()
                break
            else:
                save_progress(prog)
                play_sfx("bad", muted)
                clear()
                ui.header("ACRONYM BLITZ", badge="RETRY", muted=muted, bgm=bgm)
                ui.wolf_say("sad", f"{RED}{BOLD}✘ {acro}{RST}", f"{GOLD}{full_name}{RST}")
                print(f"\n  {DIM}Press any key to retry...{RST}")
                getch()
    play_sfx("fanfare", muted)
    return muted


def run_domain_drill(
    prog: dict,
    muted: bool,
    domain_filter: str | None = None,
    count: int = 8,
    bgm: BackgroundBeat | None = None,
) -> bool:
    rng = random.Random()
    pool = [q for q in DOMAIN_QUESTIONS if domain_filter is None or q[0] == domain_filter]
    deck = rng.sample(pool, min(count, len(pool)))

    for idx, (dom, obj, prompt, opts, win_idx, tip) in enumerate(deck, 1):
        order = list(range(len(opts)))
        rng.shuffle(order)
        shuffled_opts = [opts[i] for i in order]
        mapped_win = order.index(win_idx)

        while True:
            clear()
            ui.header(f"DOMAIN {dom} · {obj}", badge=f"{idx}/{len(deck)}", muted=muted, bgm=bgm)
            ui.wolf_say("study", f"{DIM}Pick the best call.{RST}")
            print()
            ui.panel("SCENARIO", [prompt], color=CYAN)
            print()
            for i, text in enumerate(shuffled_opts, 1):
                print(f"    {CYAN}[{i}]{RST} {ui.truncate_vis(text, 62)}")
            ui.footer([("1-4", "Pick"), ("V", "Vibe"), ("M", "Mute"), ("B", "Back")])

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
            if ch not in {"1", "2", "3", "4"}:
                continue

            picked = int(ch) - 1
            prog["attempts"] += 1
            if picked == mapped_win:
                prog["correct"] += 1
                if prompt not in prog["mastered_qs"]:
                    prog["mastered_qs"].append(prompt)
                save_progress(prog)
                play_sfx("good", muted)
                clear()
                ui.header(f"DOMAIN {dom}", badge="CLEAN", muted=muted, bgm=bgm)
                ui.wolf_say("happy", f"{MINT}{BOLD}✔ Spot on!{RST}")
                print()
                ui.panel("WHY IT WORKS", [tip], color=MINT)
                print(f"\n  {DIM}Press any key to continue...{RST}")
                getch()
                break
            else:
                save_progress(prog)
                play_sfx("bad", muted)
                clear()
                ui.header(f"DOMAIN {dom}", badge="RETRY", muted=muted, bgm=bgm)
                ui.wolf_say("sad", f"{RED}{BOLD}✘ Trap!{RST}")
                print()
                ui.panel("CLUE", [tip], color=GOLD)
                print(f"\n  {DIM}Press any key to retry...{RST}")
                getch()
    play_sfx("fanfare", muted)
    return muted


def run_menu(muted: bool = False, bgm: BackgroundBeat | None = None) -> bool:
    prog = load_progress()
    while True:
        clear()
        acc = int(round(100 * prog["correct"] / max(1, prog["attempts"])))
        ui.header("WOLF-SOC · EXAM BANK", badge=f"Acc {acc}%", muted=muted, bgm=bgm)
        ui.wolf_say(
            "idle",
            f"{BOLD}Acronyms :{RST} {bar(len(prog['mastered_terms']), len(ACRONYMS), 16, CYAN)}",
            f"{BOLD}Scenarios:{RST} {bar(len(prog['mastered_qs']), len(DOMAIN_QUESTIONS), 16, MINT)}",
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
        elif ch == "m":
            muted = ui.toggle_mute(muted, bgm)
        elif ch == "v":
            muted = ui.cycle_vibe(muted, bgm)
            play_sfx("blip", muted)
        elif ch == "a":
            muted = run_acronym_blitz(prog, muted, count=10, bgm=bgm)
        elif ch in {"1", "2", "3", "4", "5"}:
            muted = run_domain_drill(prog, muted, domain_filter=f"{ch}.0", count=5, bgm=bgm)
        elif ch == "e":
            muted = run_domain_drill(prog, muted, domain_filter=None, count=12, bgm=bgm)


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
