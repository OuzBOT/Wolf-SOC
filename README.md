# Wolf-SOC — Offline Terminal Security Trainer & 8-Bit Cyber-Deck

> **Orderly, not boring.** A 100% standalone, zero-dependency Python terminal security trainer with an expressive ASCII Wolf coach, pure-stdlib 8-bit chiptune synth, interactive ASCII schematics, visual stick-figure mini-labs, and synthetic SOC shift simulators.

```text
  /\_/\     WOLF-SOC · STANDALONE SECURITY TRAINER
 ( ★w★ )    Pure Python 3.10+ Stdlib · 0 pip installs · 100% Offline
  /   \
```

---

## What's Inside

1. **Cyber Campaign (`academy_campaign.py` + `domain_modules.py`)** — 6-tier interactive incident response, PKI, AI-security, and risk-math campaign.
2. **Exam & Acronym Bank (`exam_drill.py`)** — 106-acronym spaced-repetition blitz + 5-domain scenario bank with **Wolf Coach** plain-English terminology pauses and 3-strike ASCII schematic breakdowns.
3. **Interactive Tech Diagrams (`diagram_trainer.py`)** — 22 interactive ASCII schematics across Electronics, Networking, Core Security, and Python Automation.
4. **Visual Stick-Figure Mini-Labs (`mini_lab.py`)** — 4 live ASCII scenes (Mantrap/Tailgating, SSH Brute-Force, ESD/DMM Safety, Dropped USB) where your choices visibly change the scene.
5. **RetailPOS-Lab SOC Shift Simulators (`shifts/siem_triage.py`, `shifts/phish_forensics.py`)** — SIEM/EDR triage and SPF/DKIM/DMARC phishing forensics shifts that emit SHA-256 chain-of-custody reports.
6. **Pure-Stdlib 8-Bit Synth (`synth_engine.py`)** — 3-channel procedural PCM chiptune engine (`CHILL` / `LO-FI` / `BOSS` tracks, switchable live with `[V]`, mute with `[M]`, works silently on headless terminals).

---

## Quickstart

```bash
# 1. Launch Wolf-SOC (Python 3.10+, zero pip installs)
python3 wolf_soc.py

# 2. Run built-in asset & environment diagnostics
python3 wolf_soc.py --debug --check

# 3. Verify application and data integrity
sha256sum -c MANIFEST.sha256
```

---

## Repository Structure

```text
wolf-soc/
├── README.md                  # Overview & quickstart
├── CHANGELOG.md               # Dated release & patch history
├── MANIFEST.sha256            # SHA-256 verification manifest for application and data files
├── LICENSE                    # MIT License
├── .gitignore                 # Excludes caches & local progress saves
├── wolf_soc.py                # Main unified TUI launcher, Wolf Coach & diagnostics
├── ui_core.py                 # Exact 72-column terminal UI primitives & Wolf mascot
├── academy_campaign.py        # 6-tier campaign & boss fights
├── domain_modules.py          # Standalone security domain curriculum modules
├── exam_drill.py              # 106-acronym & 5-domain drill bank
├── diagram_trainer.py         # Interactive ASCII schematic renderer & node quizzer
├── mini_lab.py                # 4 visual stick-figure mini-labs
├── synth_engine.py            # Zero-dependency PCM 8-bit chiptune & SFX synthesizer
├── shifts/
│   ├── siem_triage.py         # RetailPOS-Lab SIEM/EDR triage & SHA-256 custody simulator
│   └── phish_forensics.py     # RetailPOS-Lab email header (SPF/DKIM/DMARC) forensics lab
└── data/                      # Self-contained JSON diagrams, glossary & alert fixtures
```

*All scenarios and indicators are 100% synthetic (RFC 5737 test IP ranges `192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24` and RFC 2606 `.example` domains). Educational study content is independent and not affiliated with any certification body.*
