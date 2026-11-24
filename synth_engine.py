from __future__ import annotations

import io
import math
import random
import shutil
import struct
import subprocess
import sys
import threading
import time
import wave

SAMPLE_RATE = 22050

NOTE_OFFSETS = {
    "C": -9, "C#": -8, "D": -7, "D#": -6, "E": -5, "F": -4,
    "F#": -3, "G": -2, "G#": -1, "A": 0, "A#": 1, "B": 2,
}


def hz(note: str) -> float:
    """Convert note names like 'A4' or 'G#4' to frequency in Hz ('-' = rest)."""
    if not note or note == "-":
        return 0.0
    name, octave = note[:-1], int(note[-1])
    semitones = NOTE_OFFSETS[name] + (octave - 4) * 12
    return round(440.0 * (2.0 ** (semitones / 12.0)), 2)


def _pulse(phase: float, duty: float = 0.25) -> float:
    return 1.0 if (phase % 1.0) < duty else -1.0


def _triangle(phase: float) -> float:
    p = phase % 1.0
    return 4.0 * p - 1.0 if p < 0.5 else 3.0 - 4.0 * p


def render_track(
    steps: list[tuple[float, float, str]],
    step_dur: float = 0.16,
    master_vol: float = 0.28,
) -> bytes:
    """
    Render a multi-channel chiptune sequence into WAV bytes.
    Each step is (lead_hz, bass_hz, drum_type) where drum_type in {'kick', 'hat', ''}.
    """
    rng = random.Random(42)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        frames = bytearray()
        samples_per_step = int(SAMPLE_RATE * step_dur)

        for lead_hz, bass_hz, drum in steps:
            for i in range(samples_per_step):
                t = i / SAMPLE_RATE
                prog = i / samples_per_step
                attack = min(1.0, prog * 24.0)

                # 1. Lead 25% pulse with soft pluck decay
                lead_val = 0.0
                if lead_hz > 0:
                    env_l = math.exp(-3.2 * prog) * attack
                    lead_val = _pulse(lead_hz * t, 0.25) * env_l * 0.45

                # 2. Warm triangle sub-bass
                bass_val = 0.0
                if bass_hz > 0:
                    env_b = max(0.2, 1.0 - 0.5 * prog) * attack
                    bass_val = _triangle(bass_hz * t) * env_b * 0.55

                # 3. Retro drum hit
                drum_val = 0.0
                if drum == "kick" and prog < 0.35:
                    pitch_drop = 130.0 * math.exp(-18.0 * prog) + 42.0
                    drum_val = math.sin(2.0 * math.pi * pitch_drop * t) * math.exp(-10.0 * prog) * 0.65
                elif drum == "hat" and prog < 0.18:
                    drum_val = rng.uniform(-1.0, 1.0) * math.exp(-28.0 * prog) * 0.22

                mixed = max(-1.0, min(1.0, (lead_val + bass_val + drum_val) * master_vol))
                frames.extend(struct.pack("<h", int(mixed * 32767)))
        wf.writeframes(bytes(frames))
    return buf.getvalue()


def _compile(raw_steps: list[tuple[str, str, str]]) -> list[tuple[float, float, str]]:
    return [(hz(lead), hz(bass), drum) for lead, bass, drum in raw_steps]


def _vary(
    steps: list[tuple[float, float, str]],
    pass_num: int,
    drop_kick: bool = False,
) -> list[tuple[float, float, str]]:
    """Mutate repeated 16-step blocks so long arrangements evolve naturally."""
    out: list[tuple[float, float, str]] = []
    for i, (lead, bass, drum) in enumerate(steps):
        if pass_num % 2 == 1 and i >= 12 and lead > 0:
            lead = round(lead * 2.0, 2)
        if pass_num >= 2 and drum == "" and i % 2 == 1:
            drum = "hat"
        if drop_kick and drum == "kick":
            drum = "hat" if i % 4 == 0 else ""
        out.append((lead, bass, drum))
    return out


# 1. Extended 384-step (~65s) A-minor cyber-wolf soundtrack
def _build_chill() -> list[tuple[float, float, str]]:
    intro = _compile([
        ("-",  "A2", "hat"), ("-",  "A2", ""),    ("E4", "A2", "hat"), ("-",  "A2", ""),
        ("-",  "F2", "hat"), ("-",  "F2", ""),    ("C4", "F2", "hat"), ("-",  "F2", ""),
        ("-",  "C3", "hat"), ("-",  "C3", ""),    ("G4", "C3", "hat"), ("-",  "C3", ""),
        ("-",  "G2", "hat"), ("-",  "G2", "hat"), ("D4", "G2", "hat"), ("E4", "G2", "hat"),
    ])
    verse = _compile([
        ("A4", "A2", "kick"), ("-",  "A2", "hat"), ("C5", "A2", "hat"), ("E5", "A2", "hat"),
        ("D5", "F2", "kick"), ("-",  "F2", "hat"), ("C5", "F2", "hat"), ("A4", "F2", "hat"),
        ("G4", "C3", "kick"), ("-",  "C3", "hat"), ("B4", "C3", "hat"), ("D5", "C3", "hat"),
        ("C5", "G2", "kick"), ("B4", "G2", "hat"), ("A4", "G2", "hat"), ("G4", "G2", "hat"),
    ])
    hook = _compile([
        ("A5", "A2", "kick"), ("G5", "A2", "hat"), ("E5", "A2", "kick"), ("C5", "A2", "hat"),
        ("D5", "F2", "kick"), ("E5", "F2", "hat"), ("F5", "F2", "kick"), ("A5", "F2", "hat"),
        ("G5", "C3", "kick"), ("E5", "C3", "hat"), ("D5", "C3", "kick"), ("C5", "C3", "hat"),
        ("D5", "G2", "kick"), ("E5", "G2", "hat"), ("G5", "G2", "kick"), ("E5", "G2", "hat"),
    ])
    bridge = _compile([
        ("F5", "D2", "kick"), ("-",  "D2", "hat"), ("E5", "D2", "hat"), ("D5", "D2", "hat"),
        ("C5", "A2", "kick"), ("-",  "A2", "hat"), ("B4", "A2", "hat"), ("A4", "A2", "hat"),
        ("A4", "F2", "kick"), ("C5", "F2", "hat"), ("E5", "F2", "hat"), ("F5", "F2", "hat"),
        ("E5", "E2", "kick"), ("D5", "E2", "hat"), ("C5", "E2", "kick"), ("B4", "E2", "hat"),
    ])
    turnaround = _compile([
        ("C5", "A2", "kick"), ("B4", "A2", "hat"), ("A4", "A2", "hat"), ("G4", "A2", "hat"),
        ("F4", "F2", "kick"), ("A4", "F2", "hat"), ("C5", "F2", "hat"), ("E5", "F2", "hat"),
        ("D5", "E2", "kick"), ("C5", "E2", "hat"), ("B4", "E2", "hat"), ("G#4", "E2", "hat"),
        ("A4", "E2", "kick"), ("B4", "E2", "hat"), ("C5", "E2", "kick"), ("E5", "E2", "hat"),
    ])
    # 24 bars x 16 steps = 384 steps (~65.3 seconds)
    return (
        _vary(intro, 0) + _vary(intro, 1)
        + _vary(verse, 0) + _vary(verse, 1) + _vary(verse, 2) + _vary(verse, 3)
        + _vary(hook, 0) + _vary(hook, 1) + _vary(hook, 2) + _vary(hook, 3)
        + _vary(bridge, 0, drop_kick=True) + _vary(bridge, 1, drop_kick=True)
        + _vary(bridge, 2) + _vary(bridge, 3)
        + _vary(verse, 1, drop_kick=True) + _vary(verse, 2, drop_kick=True)
        + _vary(hook, 0) + _vary(hook, 1) + _vary(hook, 2) + _vary(hook, 3)
        + _vary(turnaround, 0) + _vary(turnaround, 1)
        + _vary(intro, 1) + _vary(turnaround, 2)
    )


# 2. Extended 384-step (~88s) Cozy Study Lo-Fi soundtrack
def _build_lofi() -> list[tuple[float, float, str]]:
    intro = _compile([
        ("E5", "C3", ""),     ("-",  "C3", ""),    ("G5", "C3", "hat"), ("-",  "C3", ""),
        ("C5", "A2", ""),     ("-",  "A2", ""),    ("E5", "A2", "hat"), ("-",  "A2", ""),
        ("A4", "F2", ""),     ("-",  "F2", ""),    ("C5", "F2", "hat"), ("-",  "F2", ""),
        ("B4", "G2", ""),     ("-",  "G2", ""),    ("D5", "G2", "hat"), ("E5", "G2", ""),
    ])
    verse = _compile([
        ("C5", "C3", "kick"), ("E5", "C3", ""),    ("G5", "C3", "hat"), ("B5", "C3", ""),
        ("A4", "A2", "kick"), ("C5", "A2", ""),    ("E5", "A2", "hat"), ("G5", "A2", ""),
        ("F4", "F2", "kick"), ("A4", "F2", ""),    ("C5", "F2", "hat"), ("E5", "F2", ""),
        ("G4", "G2", "kick"), ("B4", "G2", ""),    ("D5", "G2", "hat"), ("E5", "G2", ""),
    ])
    hook = _compile([
        ("E5", "C3", "kick"), ("G5", "C3", "hat"), ("B5", "C3", "hat"), ("D6", "C3", ""),
        ("C5", "A2", "kick"), ("E5", "A2", "hat"), ("G5", "A2", "hat"), ("B5", "A2", ""),
        ("A4", "F2", "kick"), ("C5", "F2", "hat"), ("E5", "F2", "hat"), ("G5", "F2", ""),
        ("B4", "G2", "kick"), ("D5", "G2", "hat"), ("E5", "G2", "hat"), ("G5", "G2", ""),
    ])
    bridge = _compile([
        ("D5", "D2", "kick"), ("F5", "D2", ""),    ("A5", "D2", "hat"), ("C6", "D2", ""),
        ("G5", "G2", "kick"), ("F5", "G2", ""),    ("E5", "G2", "hat"), ("D5", "G2", ""),
        ("E5", "E2", "kick"), ("G5", "E2", ""),    ("B5", "E2", "hat"), ("D6", "E2", ""),
        ("A4", "A2", "kick"), ("C5", "A2", ""),    ("E5", "A2", "hat"), ("G5", "A2", ""),
    ])
    turnaround = _compile([
        ("F4", "F2", "kick"), ("A4", "F2", ""),    ("C5", "F2", "hat"), ("E5", "F2", ""),
        ("G4", "G2", "kick"), ("B4", "G2", ""),    ("D5", "G2", "hat"), ("F5", "G2", ""),
        ("E5", "G2", "kick"), ("D5", "G2", ""),    ("B4", "G2", "hat"), ("G4", "G2", ""),
        ("A4", "G2", "kick"), ("B4", "G2", "hat"), ("D5", "G2", "kick"), ("B4", "G2", "hat"),
    ])
    # 24 bars x 16 steps = 384 steps (~88.3 seconds)
    return (
        _vary(intro, 0) + _vary(intro, 1)
        + _vary(verse, 0) + _vary(verse, 1) + _vary(verse, 2) + _vary(verse, 3)
        + _vary(hook, 0) + _vary(hook, 1) + _vary(hook, 2) + _vary(hook, 3)
        + _vary(bridge, 0, drop_kick=True) + _vary(bridge, 1, drop_kick=True)
        + _vary(bridge, 2) + _vary(bridge, 3)
        + _vary(verse, 1, drop_kick=True) + _vary(verse, 2, drop_kick=True)
        + _vary(hook, 0) + _vary(hook, 1) + _vary(hook, 2) + _vary(hook, 3)
        + _vary(turnaround, 0) + _vary(turnaround, 1)
        + _vary(intro, 1) + _vary(turnaround, 2)
    )


# 3. Extended 512-step (~61s) E-minor Boss Rush soundtrack
def _build_boss() -> list[tuple[float, float, str]]:
    intro = _compile([
        ("E4", "E3", "kick"), ("-",  "E3", "hat"), ("B4", "E3", "kick"), ("-",  "E3", "hat"),
        ("E4", "D3", "kick"), ("-",  "D3", "hat"), ("A4", "D3", "kick"), ("-",  "D3", "hat"),
        ("E4", "C3", "kick"), ("-",  "C3", "hat"), ("G4", "C3", "kick"), ("-",  "C3", "hat"),
        ("F#4", "B2", "kick"), ("G4", "B2", "hat"), ("A4", "B2", "kick"), ("B4", "B2", "hat"),
    ])
    verse = _compile([
        ("E5", "E3", "kick"), ("G5", "E3", "hat"), ("B5", "E3", "kick"), ("G5", "E3", "hat"),
        ("A5", "D3", "kick"), ("G5", "D3", "hat"), ("E5", "D3", "kick"), ("D5", "D3", "hat"),
        ("C5", "C3", "kick"), ("E5", "C3", "hat"), ("G5", "C3", "kick"), ("E5", "C3", "hat"),
        ("D5", "B2", "kick"), ("E5", "B2", "hat"), ("F#5", "B2", "kick"), ("B5", "B2", "hat"),
    ])
    hook = _compile([
        ("E6", "E3", "kick"), ("D6", "E3", "hat"), ("B5", "E3", "kick"), ("G5", "E3", "hat"),
        ("F#5", "D3", "kick"), ("A5", "D3", "hat"), ("D6", "D3", "kick"), ("A5", "D3", "hat"),
        ("G5", "C3", "kick"), ("E5", "C3", "hat"), ("C5", "C3", "kick"), ("G5", "C3", "hat"),
        ("F#5", "B2", "kick"), ("G5", "B2", "hat"), ("A5", "B2", "kick"), ("B5", "B2", "hat"),
    ])
    bridge = _compile([
        ("C5", "C3", "kick"), ("E5", "C3", "hat"), ("G5", "C3", "kick"), ("C6", "C3", "hat"),
        ("B5", "G2", "kick"), ("G5", "G2", "hat"), ("D5", "G2", "kick"), ("B4", "G2", "hat"),
        ("A4", "A2", "kick"), ("C5", "A2", "hat"), ("E5", "A2", "kick"), ("A5", "A2", "hat"),
        ("B5", "B2", "kick"), ("A5", "B2", "hat"), ("G5", "B2", "kick"), ("F#5", "B2", "hat"),
    ])
    turnaround = _compile([
        ("E5", "E3", "kick"), ("B4", "E3", "hat"), ("G4", "E3", "kick"), ("E4", "E3", "hat"),
        ("F#4", "B2", "kick"), ("A4", "B2", "hat"), ("B4", "B2", "kick"), ("D#5", "B2", "hat"),
        ("E5", "B2", "kick"), ("F#5", "B2", "hat"), ("G5", "B2", "kick"), ("A5", "B2", "hat"),
        ("B5", "B2", "kick"), ("C6", "B2", "hat"), ("D6", "B2", "kick"), ("D#6", "B2", "hat"),
    ])
    # 32 bars x 16 steps = 512 steps (~61.4 seconds)
    return (
        _vary(intro, 0) + _vary(intro, 1)
        + _vary(verse, 0) + _vary(verse, 1) + _vary(verse, 2) + _vary(verse, 3)
        + _vary(hook, 0) + _vary(hook, 1) + _vary(hook, 2) + _vary(hook, 3)
        + _vary(bridge, 0, drop_kick=True) + _vary(bridge, 1, drop_kick=True)
        + _vary(bridge, 2) + _vary(bridge, 3)
        + _vary(verse, 0) + _vary(verse, 1) + _vary(verse, 2) + _vary(verse, 3)
        + _vary(hook, 0) + _vary(hook, 1) + _vary(hook, 2) + _vary(hook, 3)
        + _vary(bridge, 2, drop_kick=True) + _vary(bridge, 3, drop_kick=True)
        + _vary(hook, 0) + _vary(hook, 1) + _vary(hook, 2) + _vary(hook, 3)
        + _vary(turnaround, 0) + _vary(turnaround, 1) + _vary(turnaround, 2) + _vary(turnaround, 3)
    )


CHILL_STEPS = _build_chill()
LOFI_STEPS = _build_lofi()
BOSS_STEPS = _build_boss()

BGM_STEPS = CHILL_STEPS

BGM_TRACK_NAMES = ("CHILL", "LO-FI", "BOSS")
_BGM_SPECS: dict[str, tuple[list[tuple[float, float, str]], float, float]] = {
    "CHILL": (CHILL_STEPS, 0.17, 0.22),
    "LO-FI": (LOFI_STEPS,  0.23, 0.18),
    "BOSS":  (BOSS_STEPS,  0.12, 0.24),
}


class _LazyTrackMap(dict):
    """Renders extended BGM WAV buffers on first access while exposing all track keys."""

    def __missing__(self, key: str) -> bytes:
        if key not in _BGM_SPECS:
            raise KeyError(key)
        steps, step_dur, master_vol = _BGM_SPECS[key]
        wav_bytes = render_track(steps, step_dur=step_dur, master_vol=master_vol)
        self[key] = wav_bytes
        return wav_bytes

    def __len__(self) -> int:
        return len(_BGM_SPECS)

    def __contains__(self, key: object) -> bool:
        return key in _BGM_SPECS

    def __iter__(self):
        return iter(_BGM_SPECS)

    def keys(self):
        return _BGM_SPECS.keys()

    def values(self):
        return [self[k] for k in _BGM_SPECS]

    def items(self):
        return [(k, self[k]) for k in _BGM_SPECS]


BGM_TRACKS: dict[str, bytes] = _LazyTrackMap()

SFX_PATTERNS = {
    "blip": [(880.0, 220.0, "hat")],
    "good": [
        (523.25, 130.81, "kick"),
        (659.25, 164.81, "hat"),
        (783.99, 196.00, "hat"),
        (1046.50, 261.63, "kick"),
    ],
    "bad": [
        (311.13, 155.56, "kick"),
        (293.66, 146.83, ""),
        (277.18, 138.59, ""),
        (261.63, 130.81, "kick"),
    ],
    "fanfare": [
        (523.25, 130.81, "kick"),
        (659.25, 164.81, "hat"),
        (783.99, 196.00, "kick"),
        (1046.50, 261.63, "hat"),
        (783.99, 196.00, "hat"),
        (1046.50, 261.63, "kick"),
    ],
}

BGM_WAV = BGM_TRACKS["CHILL"]
SFX_WAVS = {k: render_track(v, step_dur=0.10, master_vol=0.45) for k, v in SFX_PATTERNS.items()}


def _has_player() -> bool:
    if sys.platform == "win32":
        return True
    return bool(shutil.which("paplay") or shutil.which("aplay"))


def _play_wav_async(wav_bytes: bytes) -> None:
    if sys.platform == "win32":
        try:
            import winsound  # type: ignore[import-not-found]

            winsound.PlaySound(wav_bytes, winsound.SND_MEMORY | winsound.SND_ASYNC)
        except Exception:
            pass
        return
    player = shutil.which("paplay") or shutil.which("aplay")
    if not player:
        return
    try:
        cmd = [player] if player.endswith("paplay") else [player, "-q", "-"]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if p.stdin:
            p.stdin.write(wav_bytes)
            p.stdin.close()
        threading.Thread(target=p.wait, daemon=True).start()
    except Exception:
        pass


def play_sfx(name: str, muted: bool = False) -> None:
    if muted or name not in SFX_WAVS:
        return
    _play_wav_async(SFX_WAVS[name])


class BackgroundBeat:
    """Loops the selected 3-channel chiptune soundtrack in the background until stopped."""

    def __init__(self, track_name: str = "CHILL") -> None:
        self.enabled = True
        self.muted = False
        self._track_idx = BGM_TRACK_NAMES.index(track_name) if track_name in BGM_TRACK_NAMES else 0
        self._stop = threading.Event()
        self._proc: subprocess.Popen | None = None
        self._thread: threading.Thread | None = None

    @property
    def track_name(self) -> str:
        return BGM_TRACK_NAMES[self._track_idx]

    def cycle_track(self) -> str:
        self._track_idx = (self._track_idx + 1) % len(BGM_TRACK_NAMES)
        self.kill_active()
        return self.track_name

    def start(self) -> None:
        if not _has_player() or sys.platform == "win32":
            return
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self) -> None:
        player = shutil.which("paplay") or shutil.which("aplay")
        if not player:
            return
        cmd = [player] if player.endswith("paplay") else [player, "-q", "-"]
        while not self._stop.is_set():
            if not self.enabled or self.muted:
                time.sleep(0.1)
                continue
            try:
                wav_blob = BGM_TRACKS[self.track_name]
                self._proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                if self._proc.stdin:
                    self._proc.stdin.write(wav_blob)
                    self._proc.stdin.close()
                self._proc.wait()
            except Exception:
                time.sleep(0.25)

    def kill_active(self) -> None:
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.terminate()
            except Exception:
                pass

    def stop(self) -> None:
        self._stop.set()
