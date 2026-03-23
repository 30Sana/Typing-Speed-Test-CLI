#!/usr/bin/env python3
"""
typer — a terminal typing speed test
"""

import time
import json
import random
import os
import sys
import tty
import termios
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.rule import Rule

console = Console()

SCORES_FILE = Path.home() / ".typer_scores.json"

# ---------------------------------------------------------------------------
# Word lists
# ---------------------------------------------------------------------------

EASY_WORDS = [
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "it",
    "for", "not", "on", "with", "he", "as", "you", "do", "at", "this",
    "but", "his", "by", "from", "they", "we", "say", "her", "she", "or",
    "an", "will", "my", "one", "all", "would", "there", "their", "what",
    "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
    "when", "make", "can", "like", "time", "no", "just", "him", "know",
    "take", "people", "into", "year", "your", "good", "some", "could",
    "them", "see", "other", "than", "then", "now", "look", "only", "come",
    "its", "over", "think", "also", "back", "after", "use", "two", "how",
    "our", "work", "first", "well", "way", "even", "new", "want", "any",
]

MEDIUM_WORDS = [
    "python", "keyboard", "monitor", "program", "function", "variable",
    "terminal", "browser", "network", "storage", "process", "package",
    "algorithm", "database", "language", "software", "hardware", "system",
    "element", "module", "object", "method", "string", "integer", "boolean",
    "library", "install", "execute", "compile", "syntax", "comment", "import",
    "random", "request", "response", "server", "client", "socket", "buffer",
    "thread", "async", "stream", "parser", "render", "deploy", "version",
    "commit", "branch", "merge", "clone", "fetch", "remote", "origin",
    "docker", "container", "image", "volume", "network", "service", "config",
]

HARD_WORDS = [
    "asynchronous", "polymorphism", "encapsulation", "inheritance", "abstraction",
    "infrastructure", "authentication", "authorization", "cryptography", "serialization",
    "deserialization", "implementation", "configuration", "optimization", "virtualization",
    "containerization", "microservices", "orchestration", "parallelization", "recursion",
    "documentation", "vulnerability", "architecture", "dependencies", "refactoring",
    "interpolation", "concatenation", "multiplication", "disambiguation", "synchronization",
    "initialization", "decompression", "transformation", "classification", "visualization",
    "environment", "permissions", "transaction", "middleware", "repository",
]

DIFFICULTIES = {
    "easy":   (EASY_WORDS,   25),
    "medium": (MEDIUM_WORDS, 25),
    "hard":   (HARD_WORDS,   20),
}

# ---------------------------------------------------------------------------
# Score persistence
# ---------------------------------------------------------------------------

def load_scores():
    if SCORES_FILE.exists():
        try:
            return json.loads(SCORES_FILE.read_text())
        except Exception:
            pass
    return []

def save_score(wpm: float, accuracy: float, difficulty: str):
    scores = load_scores()
    scores.append({
        "wpm":        round(wpm, 1),
        "accuracy":   round(accuracy, 1),
        "difficulty": difficulty,
        "date":       datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    scores = sorted(scores, key=lambda x: x["wpm"], reverse=True)[:20]
    SCORES_FILE.write_text(json.dumps(scores, indent=2))
    return scores

# ---------------------------------------------------------------------------
# Input reading (single char, no enter needed)
# ---------------------------------------------------------------------------

def read_char():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        # Handle escape sequences (arrows etc) — swallow them
        if ch == "\x1b":
            sys.stdin.read(2)
            return None
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def render_test(words: list, typed: str, current_word_idx: int, mistakes: int, elapsed: float):
    console.clear()

    # Stats bar
    wpm = 0.0
    if elapsed > 0 and current_word_idx > 0:
        wpm = (current_word_idx / elapsed) * 60

    stats = Table.grid(padding=(0, 4))
    stats.add_column(justify="center")
    stats.add_column(justify="center")
    stats.add_column(justify="center")

    stats.add_row(
        Text(f"{wpm:.0f} wpm", style="bold bright_cyan"),
        Text(f"{mistakes} mistakes", style="bold red" if mistakes > 0 else "bold green"),
        Text(f"{elapsed:.1f}s", style="bold yellow"),
    )

    console.print()
    console.print(Panel(stats, border_style="grey30", padding=(0, 2)))
    console.print()

    # Word display — show a window of words around current position
    line = Text()
    window_start = max(0, current_word_idx - 10)
    window_end   = min(len(words), window_start + 30)

    for i in range(window_start, window_end):
        word = words[i]
        if i < current_word_idx:
            # Already typed
            line.append(word, style="green")
        elif i == current_word_idx:
            # Currently typing — compare typed against word
            for j, ch in enumerate(word):
                if j < len(typed):
                    if typed[j] == ch:
                        line.append(ch, style="bold white underline")
                    else:
                        line.append(ch, style="bold red underline")
                else:
                    line.append(ch, style="bold white underline")
            # Show extra typed chars as red
            if len(typed) > len(word):
                line.append("_" * (len(typed) - len(word)), style="bold red underline")
        else:
            line.append(word, style="dim")
        line.append(" ")

    console.print(Panel(line, border_style="bright_blue", padding=(1, 2)))
    console.print()
    console.print("[dim]  space = next word  •  ctrl+c = quit[/dim]")

# ---------------------------------------------------------------------------
# Results screen
# ---------------------------------------------------------------------------

def show_results(wpm: float, accuracy: float, difficulty: str, elapsed: float, mistakes: int):
    scores = save_score(wpm, accuracy, difficulty)

    console.clear()
    console.print()
    console.rule("[bold bright_cyan]Results[/bold bright_cyan]", style="bright_cyan")
    console.print()

    # Main stats
    grid = Table.grid(padding=(0, 6))
    grid.add_column(justify="center")
    grid.add_column(justify="center")
    grid.add_column(justify="center")
    grid.add_column(justify="center")

    grid.add_row(
        Text(f"{wpm:.1f}\n[dim]wpm[/dim]",           style="bold bright_cyan",  justify="center"),
        Text(f"{accuracy:.1f}%\n[dim]accuracy[/dim]", style="bold green",        justify="center"),
        Text(f"{elapsed:.1f}s\n[dim]time[/dim]",      style="bold yellow",       justify="center"),
        Text(f"{mistakes}\n[dim]mistakes[/dim]",       style="bold red" if mistakes else "bold green", justify="center"),
    )

    console.print(Panel(grid, border_style="bright_cyan", padding=(1, 4)))
    console.print()

    # Personal best check
    if scores and scores[0]["wpm"] == round(wpm, 1):
        console.print("  [bold yellow]🏆 New personal best![/bold yellow]")
        console.print()

    # Leaderboard
    console.rule("[bold]Best Scores[/bold]", style="grey30")
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold", show_edge=False, padding=(0,2))
    table.add_column("#",          width=4,  style="dim")
    table.add_column("WPM",        width=8,  style="bold bright_cyan")
    table.add_column("Accuracy",   width=10, style="green")
    table.add_column("Difficulty", width=10)
    table.add_column("Date",       width=18, style="dim")

    for i, s in enumerate(scores[:10], 1):
        table.add_row(
            str(i),
            str(s["wpm"]),
            f"{s['accuracy']}%",
            s["difficulty"],
            s["date"],
        )

    console.print(table)
    console.print()
    console.print("[dim]  press any key to play again  •  ctrl+c to quit[/dim]")
    read_char()

# ---------------------------------------------------------------------------
# Main game loop
# ---------------------------------------------------------------------------

def play(difficulty: str):
    word_list, count = DIFFICULTIES[difficulty]
    words = random.sample(word_list, min(count, len(word_list)))
    words = words * 3  # repeat to make it longer

    typed        = ""
    current_idx  = 0
    mistakes     = 0
    total_chars  = 0
    wrong_chars  = 0
    start_time   = None

    render_test(words, typed, current_idx, mistakes, 0.0)

    while current_idx < len(words):
        ch = read_char()
        if ch is None:
            continue
        if ch == "\x03":   # ctrl+c
            raise KeyboardInterrupt
        if ch == "\x7f":   # backspace
            if typed:
                typed = typed[:-1]
        elif ch == " ":
            if typed:
                if start_time is None:
                    start_time = time.time()
                target = words[current_idx]
                total_chars += len(target)
                for a, b in zip(typed, target):
                    if a != b:
                        wrong_chars += 1
                if len(typed) > len(target):
                    wrong_chars += len(typed) - len(target)
                if typed != target:
                    mistakes += 1
                current_idx += 1
                typed = ""
        else:
            if start_time is None and ch.isprintable():
                start_time = time.time()
            if ch.isprintable():
                typed += ch

        elapsed = (time.time() - start_time) if start_time else 0.0
        render_test(words, typed, current_idx, mistakes, elapsed)

    elapsed  = (time.time() - start_time) if start_time else 1.0
    wpm      = (current_idx / elapsed) * 60
    accuracy = max(0.0, (1 - wrong_chars / max(total_chars, 1)) * 100)

    show_results(wpm, accuracy, difficulty, elapsed, mistakes)

# ---------------------------------------------------------------------------
# Menu
# ---------------------------------------------------------------------------

def menu():
    scores = load_scores()
    best   = f"{scores[0]['wpm']} wpm" if scores else "none yet"

    console.clear()
    console.print()
    console.print(Panel(
        "[bold bright_cyan]typer[/bold bright_cyan]\n[dim]a terminal typing speed test[/dim]",
        border_style="bright_cyan",
        padding=(1, 4),
        expand=False,
    ))
    console.print()
    console.print(f"  Personal best: [bold yellow]{best}[/bold yellow]")
    console.print()
    console.print("  Select difficulty:")
    console.print("   [bold]1[/bold]  Easy    [dim](common words)[/dim]")
    console.print("   [bold]2[/bold]  Medium  [dim](tech words)[/dim]")
    console.print("   [bold]3[/bold]  Hard    [dim](long words)[/dim]")
    console.print()
    console.print("  [dim]ctrl+c to quit[/dim]")
    console.print()

    while True:
        ch = read_char()
        if ch == "1":   return "easy"
        if ch == "2":   return "medium"
        if ch == "3":   return "hard"
        if ch == "\x03": raise KeyboardInterrupt

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    try:
        while True:
            difficulty = menu()
            play(difficulty)
    except KeyboardInterrupt:
        console.print("\n[dim]bye![/dim]\n")

if __name__ == "__main__":
    main()