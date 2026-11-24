# Future Log

Simple backlog of planned ideas for future Wolf-SOC releases (not yet implemented).

## Ideas

- **Final Boss Fight -> Fresh Playthrough:** Unlock a final multi-stage SOC boss encounter after completing all campaign tiers, culminating in an optional confirmed fresh playthrough (resetting training progress while preserving saved incident reports).
- **Multilingual Support & Auto-Detection:** Add localized UI/training strings with automatic system locale detection and an in-app language switcher.
- **International Electrical Standards & Regional Differences:** Expand electronics drills and reference diagrams to cover international wiring color codes, mains voltage/frequency standards (e.g., 120V/60Hz vs. 230V/50Hz), and regional safety norms (NEC/IEC).
- **Metric & Imperial Unit Support:** Support toggling between metric (SI) and imperial units across electrical, thermal, and hardware calculations.
- **Optional Kubernetes Fishbowl Bridge (Post-v1.0.0):** Add an optional, read-only importer to replay signed HMAC-SHA256 JSON telemetry reports exported from a standalone offline single-node `k3s` fishbowl sandbox (default-deny `NetworkPolicy` sinkhole, decoy credential bait, and out-of-band host eBPF/Tetragon or `auditd` logs) as live-capture SIEM triage scenarios—keeping Wolf-SOC itself 100% standalone with zero cluster dependencies.
