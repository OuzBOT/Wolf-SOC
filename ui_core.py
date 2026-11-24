#!/usr/bin/env python3
"""
Shared terminal UI primitives for Wolf-SOC.

Guarantees exact visual-width box alignment (including wide Unicode glyphs),
a single consistent ASCII Wolf mascot, clean text wrapping, and synced audio badges.
"""

from __future__ import annotations

import re
import sys
import textwrap
import unicodedata

RST = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[38;5;51m"
PINK = "\033[38;5;213m"
MINT = "\033[38;5;121m"
GOLD = "\033[38;5;221m"
RED = "\033[38;5;203m"
PURP = "\033[38;5;141m"

BOX_WIDTH = 72
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def char_width(ch: str) -> int:
    if unicodedata.combining(ch):
        return 0
    if unicodedata.east_asian_width(ch) in {"W", "F"}:
        return 2
    return 1


def vis_len(text: str) -> int:
    """Visual terminal column width ignoring ANSI color codes."""
    return sum(char_width(ch) for ch in strip_ansi(text))


def truncate_vis(text: str, max_width: int) -> str:
    """Truncate plain text cleanly to fit within max_width terminal columns."""
    if vis_len(text) <= max_width:
        return text
    if max_width <= 1:
        return text[:max_width]
    out: list[str] = []
    width = 0
    for ch in text:
        cw = char_width(ch)
        if width + cw > max_width - 1:
            break
        out.append(ch)
        width += cw
    return "".join(out) + "…"


def pad_vis(text: str, width: int, align: str = "left") -> str:
    """Pad an ANSI-styled string to exact terminal column width."""
    vlen = vis_len(text)
    if vlen >= width:
        return text
    pad = " " * (width - vlen)
    if align == "right":
        return pad + text
    if align == "center":
        left = (width - vlen) // 2
        right = width - vlen - left
        return (" " * left) + text + (" " * right)
    return text + pad


def clear() -> None:
    sys.stdout.write("\033[H\033[2J\033[3J")
    sys.stdout.flush()


def getch() -> str:
    """Read a single keypress without Enter, swallowing multi-byte arrow sequences."""
    if sys.platform == "win32":
        import msvcrt  # type: ignore[import-not-found]

        ch = msvcrt.getwch()
        if ch == "\x03":
            raise KeyboardInterrupt
        if ch in {"\x00", "\xe0"}:
            code = msvcrt.getwch()
            return {"H": "UP", "P": "DOWN", "M": "RIGHT", "K": "LEFT"}.get(code, "")
        return ch
    import select
    import termios
    import tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x03":
            raise KeyboardInterrupt
        if ch == "\x1b":
            seq = ""
            while select.select([fd], [], [], 0.02)[0]:
                nxt = sys.stdin.read(1)
                seq += nxt
                if nxt.isalpha() or nxt == "~":
                    break
            return {"[A": "UP", "[B": "DOWN", "[C": "RIGHT", "[D": "LEFT"}.get(seq, "\x1b" if not seq else "")
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def bar(done: int, total: int, width: int = 18, color: str = MINT) -> str:
    pct = int(round(100 * done / max(1, total)))
    filled = max(0, min(width, int(round(width * done / max(1, total)))))
    return f"{color}{'█' * filled}{DIM}{'░' * (width - filled)}{RST} {BOLD}{done}/{total}{RST} {DIM}({pct}%){RST}"


def pct_bar(pct: int, width: int = 18, color: str = MINT) -> str:
    filled = max(0, min(width, int(round(width * pct / 100))))
    return f"{color}{'█' * filled}{DIM}{'░' * (width - filled)}{RST} {BOLD}{pct:3d}%{RST}"


def wolf_art(mood: str = "idle") -> list[str]:
    faces = {
        "idle":  (f"{CYAN}  /\\_/\\  {RST}", f"{CYAN} ( {BOLD}•w•{RST}{CYAN} ) {RST}", f"{CYAN}  /   \\  {RST}"),
        "happy": (f"{MINT}  /\\_/\\  {RST}", f"{MINT} ( {BOLD}^w^{RST}{MINT} ) {RST}", f"{MINT}  /   \\  {RST}"),
        "hype":  (f"{GOLD}  /\\_/\\  {RST}", f"{GOLD} ( {BOLD}★w★{RST}{GOLD}  {RST}", f"{GOLD}  /   \\  {RST}"),
        "study": (f"{GOLD}  /\\_/\\  {RST}", f"{GOLD} ( {BOLD}ÒwÓ{RST}{GOLD} ) {RST}", f"{GOLD}  / 📖\\  {RST}"),
        "alert": (f"{RED}  /\\_/\\  {RST}", f"{RED} ( {BOLD}>A<{RST}{RED} ) {RST}", f"{RED}  /   \\  {RST}"),
        "sad":   (f"{RED}  /\\_/\\  {RST}", f"{RED} ( {BOLD}T_T{RST}{RED} ) {RST}", f"{RED}  ~   ~  {RST}"),
    }
    return list(faces.get(mood, faces["idle"]))


def audio_badge(muted: bool, bgm: object | None = None) -> str:
    if muted:
        return f"{RED}x MUTE{RST}"
    track = getattr(bgm, "track_name", "CHILL") if bgm is not None else "CHILL"
    return f"{MINT}♪ {track}{RST}"


def render_header(
    title: str,
    badge: str = "",
    muted: bool = False,
    bgm: object | None = None,
    width: int = BOX_WIDTH,
) -> list[str]:
    """Return exact-width 3-line rounded header box."""
    inner = width - 2
    snd = audio_badge(muted, bgm)
    right_parts = [p for p in [badge, snd] if p]
    right_str = f" {DIM}│{RST} ".join(right_parts)
    right_w = vis_len(right_str)
    max_title_w = max(8, inner - right_w - 3)
    clean_title = truncate_vis(strip_ansi(title), max_title_w)
    left_str = f"{BOLD}{CYAN}{clean_title}{RST}"
    gap = max(1, inner - 2 - vis_len(left_str) - right_w)
    mid = f"{PURP}│{RST} {left_str}{' ' * gap}{right_str} {PURP}│{RST}"
    top = f"{PURP}╭{'─' * inner}╮{RST}"
    bot = f"{PURP}╰{'─' * inner}╯{RST}"
    return [top, mid, bot]


def header(
    title: str,
    badge: str = "",
    muted: bool = False,
    bgm: object | None = None,
    width: int = BOX_WIDTH,
) -> None:
    for line in render_header(title, badge=badge, muted=muted, bgm=bgm, width=width):
        print(line)


def wolf_say(mood: str, line1: str, line2: str = "", line3: str = "") -> None:
    """Print the 3-line ASCII Wolf mascot alongside up to 3 compact dialogue lines."""
    w = wolf_art(mood)
    print(f" {w[0]}  {line1}")
    print(f" {w[1]}  {line2}")
    print(f" {w[2]}  {line3}")


def render_panel(
    title: str,
    lines: list[str],
    color: str = CYAN,
    width: int = BOX_WIDTH,
) -> list[str]:
    """Render an exact-width rounded box with automatic wrapping for plain lines."""
    inner = width - 2
    content_w = inner - 2
    label = f" {title} " if title else ""
    label_w = vis_len(label)
    dash_count = max(0, inner - 1 - label_w)
    top = f"{color}╭─{BOLD}{label}{RST}{color}{'─' * dash_count}╮{RST}"
    out = [top]
    for raw in lines:
        if "\x1b[" in raw:
            # Styled line: pad exact width without breaking escape codes
            if vis_len(raw) <= content_w:
                out.append(f"{color}│{RST} {pad_vis(raw, content_w)} {color}│{RST}")
            else:
                # Fall back to wrapping stripped text cleanly if overly long
                for chunk in textwrap.wrap(strip_ansi(raw), width=content_w) or [""]:
                    out.append(f"{color}│{RST} {pad_vis(chunk, content_w)} {color}│{RST}")
        else:
            wrapped = textwrap.wrap(raw, width=content_w) if raw else [""]
            for chunk in wrapped:
                out.append(f"{color}│{RST} {pad_vis(chunk, content_w)} {color}│{RST}")
    out.append(f"{color}╰{'─' * inner}╯{RST}")
    return out


def panel(
    title: str,
    lines: list[str],
    color: str = CYAN,
    width: int = BOX_WIDTH,
) -> None:
    for line in render_panel(title, lines, color=color, width=width):
        print(line)


def divider(label: str = "", color: str = PURP, width: int = BOX_WIDTH) -> None:
    if not label:
        print(f"{color}{'─' * width}{RST}")
        return
    prefix = f"── {label} "
    rem = max(0, width - vis_len(prefix))
    print(f"{color}{prefix}{'─' * rem}{RST}")


def footer(keys: list[tuple[str, str]]) -> None:
    """Compact uniform bottom hotkey bar."""
    parts = [f"{CYAN}[{k}]{RST} {DIM}{desc}{RST}" for k, desc in keys]
    print("\n  " + "  ".join(parts))


def toggle_mute(muted: bool, bgm: object | None = None) -> bool:
    muted = not muted
    if bgm is not None:
        bgm.muted = muted
        if muted and hasattr(bgm, "kill_active"):
            bgm.kill_active()
    return muted


def cycle_vibe(muted: bool, bgm: object | None = None) -> bool:
    """Switch BGM track (unmuting automatically if muted) and return updated muted flag."""
    if bgm is not None and hasattr(bgm, "cycle_track"):
        bgm.cycle_track()
        if muted:
            muted = False
            bgm.muted = False
    return muted
