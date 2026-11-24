# Changelog

All notable changes to **Wolf-SOC** are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-11-23

### Added
- Standalone pure-Python 3.10+ Wolf-SOC TUI (`wolf_soc.py`, `ui_core.py`) with exact 72-column alignment, `[R]` hot-reload, `[X]` confirmed training-progress reset (clears only `academy_progress.json` and `exam_drill_progress.json`, leaving saved reports and other files untouched), and `--debug --check` diagnostics.
- 6-tier Cyber Campaign (`academy_campaign.py`, standalone `domain_modules.py`).
- 106-acronym & 5-domain Exam Bank (`exam_drill.py`) with Wolf Coach plain-English terminology pauses and 3-strike ASCII schematic breakdowns.
- 22 interactive ASCII tech schematics (`diagram_trainer.py`, `data/diagrams/`, `data/glossary.json`).
- 4 Visual Stick-Figure Mini-Labs (`mini_lab.py`) with live reacting ASCII scenes.
- 2 RetailPOS-Lab SOC shift simulators (`shifts/siem_triage.py`, `shifts/phish_forensics.py`) emitting SHA-256 chain-of-custody reports.
- Pure-stdlib 3-channel 8-bit chiptune synth (`synth_engine.py`, `CHILL` / `LO-FI` / `BOSS`).
- `FUTURELOG.md` backlog tracking future ideas (starting with a final boss fight leading to a fresh playthrough).
- SHA-256 application and data integrity manifest (`MANIFEST.sha256`).

### Fixed
- **SIEM Incident Report Accuracy (`shifts/siem_triage.py`, `wolf_soc.py`):** Replaced hardcoded best-case `## Triage Summary` lines with `build_siem_triage_summary(...)` so generated reports accurately reflect the analyst's actual classifications, containment/custody choices, eradication outcome, hardening state, and any collateral POS impact.
- **Async SFX Subprocess Cleanup (`synth_engine.py`):** Reaped background `paplay`/`aplay` SFX child processes via a daemon waiter thread to avoid zombie processes on Linux/WSL.

### Security & Standalone Hygiene
- Verified 100% pure Python stdlib with zero external repository imports, zero external home-directory or `sys.path` mutations, and zero third-party runtime packages.
- Standardized all synthetic scenario indicators to RFC 5737 test IP ranges and RFC 2606 `.example` domains.
