"""
CopyPastePlus
-------------
A calm, Claude-inspired interface for typing paragraphs into any app
(Google Docs, forms, etc.) with realistic human pacing and typos.

Features:
  - Start / Pause / Resume / Erase buttons
  - Live-adjustable WPM and typo rate (takes effect mid-type)
  - Warm, paper-inspired palette

Requirements:
    python -m pip install pyautogui

Usage:
    python CopyPastePlusV2.py
"""

import tkinter as tk
from tkinter import scrolledtext
import pyautogui
import time
import random
import threading


# ---------- CLAUDE-INSPIRED PALETTE ----------
BG_CREAM      = "#F5F0E8"
BG_PAPER      = "#FAF6EF"
TEXT_DARK     = "#2B2A28"
TEXT_MUTED    = "#6B6A66"
ACCENT_CORAL  = "#D97757"
ACCENT_CORAL_HOVER = "#C56647"
ACCENT_WARM   = "#E8DFCF"
ACCENT_WARM_HOVER = "#DCD1BD"
ACCENT_AMBER  = "#E0A458"
ACCENT_AMBER_HOVER = "#CE9345"
BORDER_SOFT   = "#D9D1C2"
SLIDER_TROUGH = "#C9BEA8"   # deeper warm tan — visible slider channel
DISABLED_GRAY = "#A8A39A"
# ---------------------------------------------

ADJACENT = {
    'a': 'sqwz', 'b': 'vghn', 'c': 'xdfv', 'd': 'serfcx', 'e': 'wrsdf',
    'f': 'drtgvc', 'g': 'ftyhbv', 'h': 'gyujnb', 'i': 'ujko', 'j': 'huiknm',
    'k': 'jiolm', 'l': 'kop', 'm': 'njk', 'n': 'bhjm', 'o': 'iklp',
    'p': 'ol', 'q': 'wa', 'r': 'edft', 's': 'awedxz', 't': 'rfgy',
    'u': 'yhji', 'v': 'cfgb', 'w': 'qase', 'x': 'zsdc', 'y': 'tghu',
    'z': 'asx',
}


def get_typo(char):
    lower = char.lower()
    if lower in ADJACENT:
        wrong = random.choice(ADJACENT[lower])
        return wrong.upper() if char.isupper() else wrong
    return None


def type_char(char):
    if char == '\n':
        pyautogui.press('enter')
    elif char == '\t':
        pyautogui.press('tab')
    else:
        pyautogui.write(char, interval=0)


def paused_sleep(seconds, control):
    """Sleep that responds to pause and stop flags."""
    remaining = seconds
    while remaining > 0:
        if control["stop"]:
            return
        while control["pause"] and not control["stop"]:
            time.sleep(0.05)
        step = min(0.05, remaining)
        time.sleep(step)
        remaining -= step


def type_text_humanly(text, control):
    """
    control dict:
      stop: bool, pause: bool, wpm: int, typo_chance: float (0-1)
    """
    def human_delay():
        base = 60.0 / (control["wpm"] * 5)
        return base * random.uniform(0.6, 1.4)

    i = 0
    at_line_start = True

    while i < len(text):
        if control["stop"]:
            return
        while control["pause"] and not control["stop"]:
            time.sleep(0.05)

        char = text[i]

        if at_line_start:
            remainder = text[i:]
            bullet_match = None
            for marker in ['• ', '◦ ', '▪ ', '- ', '* ', '— ', '– ']:
                if remainder.startswith(marker):
                    bullet_match = marker
                    break
            if not bullet_match:
                j = 0
                while j < len(remainder) and remainder[j].isdigit():
                    j += 1
                if j > 0 and j < len(remainder) - 1 and remainder[j] in '.)' and remainder[j+1] == ' ':
                    bullet_match = remainder[:j+2]

            if bullet_match:
                for b_char in bullet_match:
                    if control["stop"]:
                        return
                    while control["pause"] and not control["stop"]:
                        time.sleep(0.05)
                    type_char(b_char)
                    paused_sleep(human_delay(), control)
                i += len(bullet_match)
                at_line_start = False
                continue

        if char.isalpha() and random.random() < control["typo_chance"]:
            wrong = get_typo(char)
            if wrong:
                type_char(wrong)
                paused_sleep(human_delay(), control)

                extra_chars_before_noticing = 0
                if random.random() < 0.3 and i + 1 < len(text) and text[i+1].isalpha():
                    type_char(text[i+1])
                    paused_sleep(human_delay(), control)
                    extra_chars_before_noticing = 1

                paused_sleep(random.uniform(0.15, 0.4), control)

                for _ in range(1 + extra_chars_before_noticing):
                    if control["stop"]:
                        return
                    pyautogui.press('backspace')
                    paused_sleep(random.uniform(0.04, 0.09), control)

                paused_sleep(random.uniform(0.05, 0.15), control)

                if extra_chars_before_noticing:
                    type_char(char)
                    paused_sleep(human_delay(), control)
                    i += 1
                    at_line_start = False
                    continue

        type_char(char)

        if char in '.!?':
            paused_sleep(random.uniform(0.25, 0.5), control)
        elif char == ',':
            paused_sleep(random.uniform(0.1, 0.2), control)
        elif char == '\n':
            paused_sleep(random.uniform(0.1, 0.25), control)
            at_line_start = True
            i += 1
            continue
        elif char == ' ':
            paused_sleep(human_delay() * 1.2, control)
        else:
            paused_sleep(human_delay(), control)

        at_line_start = False
        i += 1


class HumanTyperApp:
    def __init__(self, root):
        self.root = root
        self.control = {
            "stop": False,
            "pause": False,
            "wpm": 120,
            "typo_chance": 0.02,
        }
        self.typing_thread = None
        self.is_typing = False
        self._typed_text = ""
        self._typing_start_time = None

        root.title("CopyPastePlus")
        root.geometry("640x720")
        root.configure(bg=BG_CREAM)
        root.minsize(520, 620)

        container = tk.Frame(root, bg=BG_CREAM)
        container.pack(fill="both", expand=True, padx=28, pady=24)

        tk.Label(
            container, text="CopyPastePlus",
            font=("Helvetica", 22), bg=BG_CREAM, fg=TEXT_DARK,
        ).pack(anchor="w")

        tk.Label(
            container,
            text="Paste a paragraph. Click Start. Switch to your doc.",
            font=("Helvetica", 11), bg=BG_CREAM, fg=TEXT_MUTED,
        ).pack(anchor="w", pady=(2, 18))

        # IMPORTANT: pack bottom elements FIRST with side="bottom" so they
        # always claim their space. The text area then expands into what's left.

        # Tip line (bottom-most)
        tk.Label(
            container,
            text="Tip: press  Esc  at any time to instantly stop typing.",
            font=("Helvetica", 9), bg=BG_CREAM, fg=TEXT_MUTED, anchor="w",
        ).pack(side="bottom", fill="x", pady=(2, 0))

        # Status
        self.status = tk.Label(
            container, text="Ready.",
            font=("Helvetica", 10), bg=BG_CREAM, fg=TEXT_MUTED, anchor="w",
        )
        self.status.pack(side="bottom", fill="x", pady=(14, 4))

        # Buttons
        buttons = tk.Frame(container, bg=BG_CREAM)
        buttons.pack(side="bottom", fill="x", pady=(16, 0))

        self.erase_btn = self._make_button(
            buttons, "Erase", self.erase_text,
            bg=ACCENT_WARM, hover=ACCENT_WARM_HOVER, fg=TEXT_DARK,
        )
        self.erase_btn.pack(side="left")

        self.pause_btn = self._make_button(
            buttons, "Pause", self.toggle_pause,
            bg=ACCENT_AMBER, hover=ACCENT_AMBER_HOVER, fg="white",
        )
        # Hidden until typing starts — created but not packed

        self.start_btn = self._make_button(
            buttons, "Start typing", self.start_typing,
            bg=ACCENT_CORAL, hover=ACCENT_CORAL_HOVER, fg="white",
        )
        self.start_btn.pack(side="right")

        # Sliders helper text
        tk.Label(
            container,
            text="Sliders update live — adjust speed and typos while typing.",
            font=("Helvetica", 9), bg=BG_CREAM, fg=TEXT_MUTED, anchor="w",
        ).pack(side="bottom", fill="x", pady=(2, 0))

        # Sliders — wrapped in a card so they stand out from the cream BG
        slider_card = tk.Frame(
            container, bg=BG_PAPER,
            highlightthickness=1, highlightbackground=BORDER_SOFT,
        )
        slider_card.pack(side="bottom", fill="x", pady=(16, 6))

        sliders = tk.Frame(slider_card, bg=BG_PAPER)
        sliders.pack(fill="x", padx=18, pady=14)

        tk.Label(
            sliders, text="Speed",
            font=("Helvetica", 10, "bold"), bg=BG_PAPER, fg=TEXT_DARK, width=6, anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self.wpm_var = tk.IntVar(value=120)
        self.wpm_label = tk.Label(
            sliders, text="120 wpm",
            font=("Helvetica", 11, "bold"), bg=BG_PAPER, fg=ACCENT_CORAL, width=9, anchor="e",
        )
        self.wpm_label.grid(row=0, column=2, padx=(10, 0), sticky="e")

        wpm_slider = tk.Scale(
            sliders, from_=40, to=250, orient="horizontal",
            variable=self.wpm_var, showvalue=False,
            bg=BG_PAPER, fg=TEXT_DARK,
            troughcolor=SLIDER_TROUGH, activebackground=ACCENT_CORAL_HOVER,
            highlightthickness=0, bd=1, sliderrelief="raised",
            sliderlength=26, length=200, width=16,
            command=self.on_wpm_change,
        )
        wpm_slider.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        tk.Label(
            sliders, text="Typos",
            font=("Helvetica", 10, "bold"), bg=BG_PAPER, fg=TEXT_DARK, width=6, anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(12, 0))

        self.typo_var = tk.DoubleVar(value=2.0)
        self.typo_label = tk.Label(
            sliders, text="2.0%",
            font=("Helvetica", 11, "bold"), bg=BG_PAPER, fg=ACCENT_CORAL, width=9, anchor="e",
        )
        self.typo_label.grid(row=1, column=2, padx=(10, 0), sticky="e", pady=(12, 0))

        typo_slider = tk.Scale(
            sliders, from_=0, to=15, resolution=0.5, orient="horizontal",
            variable=self.typo_var, showvalue=False,
            bg=BG_PAPER, fg=TEXT_DARK,
            troughcolor=SLIDER_TROUGH, activebackground=ACCENT_CORAL_HOVER,
            highlightthickness=0, bd=1, sliderrelief="raised",
            sliderlength=26, length=200, width=16,
            command=self.on_typo_change,
        )
        typo_slider.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(12, 0))

        sliders.columnconfigure(1, weight=1)

        # Text area (LAST so it expands into the remaining space)
        text_frame = tk.Frame(container, bg=BORDER_SOFT)
        text_frame.pack(fill="both", expand=True)

        self.text_area = scrolledtext.ScrolledText(
            text_frame,
            wrap="word",
            font=("Helvetica", 12),
            bg=BG_PAPER,
            fg=TEXT_DARK,
            insertbackground=TEXT_DARK,
            selectbackground=ACCENT_CORAL,
            selectforeground="white",
            bd=0,
            highlightthickness=1,
            highlightbackground=BORDER_SOFT,
            highlightcolor=ACCENT_CORAL,
            padx=14, pady=12,
            relief="flat",
        )
        self.text_area.pack(fill="both", expand=True, padx=1, pady=1)

        # Global Esc keybinding to abort typing
        root.bind("<Escape>", self._on_escape)

    def _on_escape(self, event=None):
        """Global Escape key — instantly stop typing if in progress."""
        if self.is_typing:
            self.control["stop"] = True
            self.control["pause"] = False
            self.set_status("Stopped (Esc pressed).")

    def on_wpm_change(self, v):
        wpm = int(float(v))
        self.wpm_label.config(text=f"{wpm} wpm")
        self.control["wpm"] = wpm

    def on_typo_change(self, v):
        rate = float(v)
        self.typo_label.config(text=f"{rate:.1f}%")
        self.control["typo_chance"] = rate / 100.0

    def _make_button(self, parent, text, command, bg, hover, fg):
        btn = tk.Label(
            parent, text=text,
            font=("Helvetica", 12),
            bg=bg, fg=fg,
            padx=22, pady=10,
            cursor="hand2",
        )
        btn._default_bg = bg
        btn._default_fg = fg
        btn._hover_bg = hover
        btn._command = command
        btn._enabled = True

        def on_enter(e):
            if btn._enabled:
                btn.config(bg=btn._hover_bg)

        def on_leave(e):
            if btn._enabled:
                btn.config(bg=btn._default_bg)

        def on_click(e):
            if btn._enabled:
                btn._command()

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        btn.bind("<Button-1>", on_click)
        return btn

    def _set_button_colors(self, btn, bg, hover, fg):
        btn._default_bg = bg
        btn._default_fg = fg
        btn._hover_bg = hover
        btn.config(bg=bg, fg=fg)

    def _set_button_enabled(self, btn, enabled):
        btn._enabled = enabled
        btn.config(cursor="hand2" if enabled else "arrow")
        if not enabled:
            btn.config(bg=DISABLED_GRAY, fg="white")
        else:
            btn.config(bg=btn._default_bg, fg=btn._default_fg)

    def erase_text(self):
        if self.is_typing:
            return
        self.text_area.delete("1.0", "end")
        self.set_status("Cleared.")

    def set_status(self, msg):
        self.status.config(text=msg)

    def toggle_pause(self):
        if not self.is_typing:
            return
        if self.control["pause"]:
            self.control["pause"] = False
            self.pause_btn.config(text="Pause")
            self._set_button_colors(self.pause_btn, ACCENT_AMBER, ACCENT_AMBER_HOVER, "white")
            self.set_status("Typing...")
        else:
            self.control["pause"] = True
            self.pause_btn.config(text="Resume")
            self._set_button_colors(self.pause_btn, ACCENT_CORAL, ACCENT_CORAL_HOVER, "white")
            self.set_status("Paused.")

    def start_typing(self):
        if self.is_typing:
            return

        text = self.text_area.get("1.0", "end-1c")
        if not text.strip():
            self.set_status("Nothing to type — paste some text first.")
            return

        self.control["wpm"] = self.wpm_var.get()
        self.control["typo_chance"] = self.typo_var.get() / 100.0
        self.control["stop"] = False
        self.control["pause"] = False

        self.is_typing = True
        self._typed_text = text
        self._typing_start_time = None

        # Disable start + erase, show pause
        self._set_button_enabled(self.start_btn, False)
        self.start_btn.config(text="Typing...")
        self._set_button_enabled(self.erase_btn, False)

        # Show pause button next to erase
        self.pause_btn.pack(side="left", padx=(10, 0), before=self.start_btn)

        # Window stays open — user can see countdown and progress
        self.countdown(5)

    def countdown(self, remaining):
        if not self.is_typing:
            return  # was cancelled
        if remaining > 0:
            self.set_status(
                f"Click into your doc — typing starts in {remaining}..."
            )
            self.root.after(1000, self.countdown, remaining - 1)
        else:
            self._typing_start_time = time.time()
            self.set_status("Typing...")
            self.typing_thread = threading.Thread(
                target=self._run_typing, daemon=True,
            )
            self.typing_thread.start()
            # Start the live progress updater
            self.root.after(250, self._update_progress)

    def _estimate_total_seconds(self):
        """Estimate total typing time based on current WPM and text length."""
        char_count = len(self._typed_text)
        wpm = self.control["wpm"]
        # Approx: 5 chars per word + small overhead for typos and punctuation pauses
        chars_per_second = wpm * 5 / 60
        base = char_count / chars_per_second
        typo_overhead = char_count * self.control["typo_chance"] * 0.5
        return base + typo_overhead

    def _format_time(self, seconds):
        seconds = max(0, int(round(seconds)))
        if seconds < 60:
            return f"{seconds}s"
        m = seconds // 60
        s = seconds % 60
        return f"{m}m {s}s"

    def _update_progress(self):
        """Periodically update the status with elapsed/remaining time."""
        if not self.is_typing or self._typing_start_time is None:
            return

        if self.control["pause"]:
            # While paused, don't update the timer
            self.root.after(250, self._update_progress)
            return

        elapsed = time.time() - self._typing_start_time
        total = self._estimate_total_seconds()
        remaining = max(0, total - elapsed)

        self.set_status(
            f"Typing...   elapsed: {self._format_time(elapsed)}   "
            f"·   ~{self._format_time(remaining)} remaining"
        )

        self.root.after(250, self._update_progress)

    def _run_typing(self):
        pyautogui.PAUSE = 0
        try:
            type_text_humanly(self._typed_text, self.control)
            self.root.after(0, self._typing_done, "Done.")
        except pyautogui.FailSafeException:
            self.root.after(0, self._typing_done, "Stopped (mouse corner).")
        except Exception as e:
            self.root.after(0, self._typing_done, f"Error: {e}")

    def _typing_done(self, msg):
        # Add elapsed time to the final message if we have it
        if self._typing_start_time is not None and msg == "Done.":
            elapsed = time.time() - self._typing_start_time
            msg = f"Done. Typed in {self._format_time(elapsed)}."

        self.is_typing = False
        self.control["pause"] = False
        self._typing_start_time = None
        self.set_status(msg)

        self._set_button_enabled(self.start_btn, True)
        self._set_button_colors(self.start_btn, ACCENT_CORAL, ACCENT_CORAL_HOVER, "white")
        self.start_btn.config(text="Start typing")

        self._set_button_enabled(self.erase_btn, True)
        self._set_button_colors(self.erase_btn, ACCENT_WARM, ACCENT_WARM_HOVER, TEXT_DARK)

        # Hide pause button and reset its state
        self.pause_btn.pack_forget()
        self.pause_btn.config(text="Pause")
        self._set_button_colors(self.pause_btn, ACCENT_AMBER, ACCENT_AMBER_HOVER, "white")


def main():
    root = tk.Tk()
    app = HumanTyperApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()