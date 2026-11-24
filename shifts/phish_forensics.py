#!/usr/bin/env python3
"""
RetailPOS-Lab SOC Desk — Shift #2: Phishing Header & Payload Triage (0 MB VRAM)
Models:
  - Email authentication checks (SPF, DKIM, DMARC, Return-Path vs From)
  - Lookalike domain & credential-harvesting URL inspection
  - Mailbox purge + IOC block + targeted awareness follow-up
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = (BASE_DIR.parent if BASE_DIR.name == "shifts" else BASE_DIR) / "artifacts"

EMAILS = [
    {
        "id": "EML-201",
        "reported_by": "store-ops-manager@retailpos-lab.example",
        "subject": "URGENT: POS Gateway Certificate Expiring in 2 Hours — Re-authenticate",
        "from_header": "POS Support <support@retailpos-gateway.example>",
        "reply_to": "ops-reset@mail-verify-gateway.example",
        "return_path": "bounce@mail-verify-gateway.example",
        "spf": "FAIL (ip 198.51.100.56 not permitted)",
        "dkim": "NONE",
        "dmarc": "FAIL",
        "body_link": "https://retailpos-gateway.example.login-auth-check.example/sso",
        "verdict": "CREDENTIAL_PHISH",
    },
    {
        "id": "EML-202",
        "reported_by": "finance-ap@retailpos-lab.example",
        "subject": "Monthly PayProcessor Settlement Statement — November",
        "from_header": "PayProcessor Notifications <notifications@payprocessor.example>",
        "reply_to": "notifications@payprocessor.example",
        "return_path": "bounces+4412@payprocessor.example",
        "spf": "PASS (payprocessor.example)",
        "dkim": "PASS (s=202409, d=payprocessor.example)",
        "dmarc": "PASS",
        "body_link": "https://dashboard.payprocessor.example/payouts",
        "verdict": "LEGITIMATE_VENDOR",
    },
    {
        "id": "EML-203",
        "reported_by": "hr-coordinator@retailpos-lab.example",
        "subject": "Updated Direct Deposit Form.pdf.html",
        "from_header": "Payroll Admin <payroll@retailpos-lab.example>",
        "reply_to": "payroll@retailpos-lab.example",
        "return_path": "mailer@external-vps-881.example",
        "spf": "SOFTFAIL (spoofed internal domain)",
        "dkim": "FAIL",
        "dmarc": "FAIL",
        "attachment": "Direct_Deposit_Form.pdf.html (SHA256: 9f86d081884c7d659a2feaa0c55ad015)",
        "verdict": "HTML_SMUGGLING_MALWARE",
    },
]


def banner(text: str) -> None:
    print("\n" + "=" * 68)
    print(f"  {text}")
    print("=" * 68)


def run_drill() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    score = 0
    timeline = []

    banner("RETAILPOS SOC DESK — SHIFT #2: PHISHING QUEUE TRIAGE")
    for e in EMAILS:
        print(f"[{e['id']}] Reported by: {e['reported_by']}")
        for k, v in e.items():
            if k not in {"id", "reported_by", "verdict"}:
                print(f"    {k}: {v}")
        print()

    # PHASE 1: HEADER & PAYLOAD CLASSIFICATION (45 pts)
    banner("PHASE 1: EMAIL HEADER & URL FORENSICS")
    print("Classify each reported email:")
    print("  1 = Legitimate Vendor Email (Close ticket, thank reporter)")
    print("  2 = Credential Phishing (Lookalike domain + failed SPF/DMARC)")
    print("  3 = HTML Smuggling / Spoofed Internal Sender (Quarantine & block)\n")

    expected = {"EML-201": "2", "EML-202": "1", "EML-203": "3"}
    for e in EMAILS:
        ans = input(f"Verdict for {e['id']} [1/2/3]: ").strip()
        if ans == expected[e["id"]]:
            print(f"  [+] Correct: {e['verdict']}")
            score += 15
            timeline.append(f"TRIAGE {e['id']}: Verified {e['verdict']}")
        else:
            print(f"  [-] Missed {e['id']} (Expected {expected[e['id']]})")
            timeline.append(f"TRIAGE {e['id']}: Misclassified ({ans})")

    # PHASE 2: CONTAINMENT & MAILBOX PURGE (30 pts)
    banner("PHASE 2: CONTAINMENT (Enterprise-Wide Exposure Check)")
    print("EML-201 and EML-203 are confirmed malicious. What is your next step?")
    print("  1 = Reply to the attacker asking who sent it")
    print("  2 = Search mail logs for all recipients, purge from all inboxes, block sender domains/URLs, check proxy/DNS logs for clicks")
    print("  3 = Only delete the email from the single user who reported it")
    c_ans = input("\nSelect Containment step [1/2/3]: ").strip()

    if c_ans == "2":
        print("  [+] All recipient mailboxes purged, IOCs blocked at secure email gateway & DNS, clickers identified.")
        score += 30
        timeline.append("CONTAIN: Purged EML-201/EML-203 org-wide, blocked IOCs, checked DNS/proxy click logs")
    else:
        print("  [!] Other employees still have the phish sitting in their inbox!")
        timeline.append("CONTAIN: Incomplete containment left other mailboxes exposed")

    # PHASE 3: REMEDIATION & AWARENESS FOLLOW-UP (25 pts)
    banner("PHASE 3: USER REMEDIATION & PHISHING PROGRAM METRICS")
    print("Proxy logs show 1 store manager clicked the EML-201 SSO link and entered credentials.")
    print("What do you execute?")
    print("  1 = Revoke active SSO/OAuth sessions, force password/MFA reset, and assign targeted phishing awareness module")
    print("  2 = Publicly shame the store manager in the company-wide Slack channel")
    r_ans = input("\nSelect Remediation action [1/2]: ").strip()

    if r_ans == "1":
        print("  [+] Session tokens revoked, credentials rotated, constructive targeted training assigned.")
        score += 25
        timeline.append("REMEDIATE: Revoked SSO tokens, reset credentials, enrolled user in targeted refresher")
    else:
        print("  [-] Shaming users stops employees from reporting suspicious emails in the future!")
        timeline.append("REMEDIATE: Counterproductive awareness response")

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest = hashlib.sha256(json.dumps(EMAILS, sort_keys=True).encode("utf-8")).hexdigest()
    report_path = ARTIFACTS_DIR / "PHISHING_REPORT.md"
    lines = [
        f"# Phishing Investigation Report — RetailPOS-Lab ({ts})",
        "",
        f"- **Analyst Score:** `{score}/100`",
        f"- **Evidence Payload SHA-256 (in-memory email fixture):** `{digest}`",
        "",
        "## Action Timeline",
    ] + [f"- {step}" for step in timeline]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    banner(f"SHIFT #2 COMPLETE — SCORE: {score}/100")
    print(f"Phishing report saved to: {report_path}\n")


if __name__ == "__main__":
    run_drill()
