"""
setup_wizard/main.py
────────────────────
Proper multi-page Windows installer for ISO Manual Assistant.

Pages:
  1. Welcome
  2. Select AI Models
  3. Installation Options  (location + shortcuts)
  4. Ready to Install
  5. Installing            (live progress)
  6. Finish

Registry:
  Writes a complete HKCU uninstall entry so the app appears correctly in
  Settings → Apps → "Add or Remove Programs" with name, version, publisher,
  size, install date, and a working Uninstall button.
"""

import datetime
import os
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# ── Constants ─────────────────────────────────────────────────────────────────

APP_NAME       = "ISO Manual Assistant"
APP_VERSION    = "1.0.0"
APP_PUBLISHER  = "ISO Manual Assistant"

APP_DATA       = Path(os.environ.get("APPDATA",      Path.home())) / APP_NAME
DEFAULT_INSTALL= Path(os.environ.get("LOCALAPPDATA", Path.home())) / APP_NAME

START_MENU_DIR = (
    Path(os.environ.get("APPDATA", "")) /
    "Microsoft" / "Windows" / "Start Menu" / "Programs" / APP_NAME
)

# Source locations beside Setup.exe
_PKG           = Path(sys.executable).parent
APP_SRC_DIR    = _PKG / "ISO_Manual_Assistant"
VECTOR_DB_SRC  = _PKG / "vector_db"
UNINSTALLER_SRC= _PKG / "ISO_Manual_Assistant_Uninstall.exe"

MODELS = [
    # (id, label, size_str, default, required)
    ("nomic-embed-text", "nomic-embed-text", "~270 MB", True,  True ),
    ("qwen2.5:7b",       "Qwen 2.5 – 7B",   "~4.5 GB", True,  False),
    ("qwen3:8b",         "Qwen 3 – 8B",      "~5.0 GB", False, False),
    ("gemma3:4b",        "Gemma 3 – 4B",     "~2.5 GB", False, False),
    ("llama3.1:8b",      "Llama 3.1 – 8B",   "~4.7 GB", False, False),
]

MODEL_DESC = {
    "nomic-embed-text": "Required — used to index and search your ISO documents.",
    "qwen2.5:7b":       "Recommended LLM for answering questions. Good accuracy.",
    "qwen3:8b":         "Latest Qwen with built-in reasoning. Slower but sharper.",
    "gemma3:4b":        "Google's lightweight model. Fast on lower-end hardware.",
    "llama3.1:8b":      "Meta's open model. Well-rounded general performance.",
}

OLLAMA_URLS = [
    "https://ollama.com/download/OllamaSetup.exe",
    "https://github.com/ollama/ollama/releases/latest/download/OllamaSetup.exe",
]

# ── Palette ───────────────────────────────────────────────────────────────────

BG       = "#1a1a1a"
PANEL    = "#242424"
CARD     = "#2e2e2e"
FG       = "#eeeeee"
MUTED    = "#888888"
ACCENT   = "#6366f1"
ACCENT_H = "#7c7ff5"
SUCCESS  = "#4caf82"
DANGER   = "#e5533d"
LINE     = "#383838"

FONT     = "Segoe UI"

# ── Wizard ────────────────────────────────────────────────────────────────────

class SetupWizard(tk.Tk):
    W, H = 680, 520

    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} Setup")
        self.resizable(False, False)
        self.configure(bg=BG)
        self._center(self.W, self.H)

        # State
        self.install_dir   = tk.StringVar(value=str(DEFAULT_INSTALL))
        self.desktop_var   = tk.BooleanVar(value=True)
        self.startmenu_var = tk.BooleanVar(value=True)
        self.launch_var    = tk.BooleanVar(value=True)
        self.model_vars    = {
            mid: tk.BooleanVar(value=default)
            for mid, *_, default, _ in MODELS
        }

        self._pages: dict[str, tk.Frame] = {}
        self._current = ""
        self._install_thread = None

        self._build_skeleton()
        self._build_all_pages()
        self._show("welcome")

    # ── Window helpers ────────────────────────────────────────────────────────

    def _center(self, w, h):
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    # ── Skeleton (persistent chrome) ──────────────────────────────────────────

    def _build_skeleton(self):
        """Left sidebar banner + right content area + bottom nav bar."""

        # ── Left banner ───────────────────────────────────────────────────────
        self._sidebar = tk.Frame(self, bg=ACCENT, width=190)
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)

        tk.Label(
            self._sidebar, text="ISO\nManual\nAssistant",
            font=(FONT, 18, "bold"), bg=ACCENT, fg="#fff",
            justify="center",
        ).place(relx=0.5, rely=0.38, anchor="center")

        self._step_lbl = tk.Label(
            self._sidebar, text="", font=(FONT, 9),
            bg=ACCENT, fg="#c5c6ff",
            justify="center",
        )
        self._step_lbl.place(relx=0.5, rely=0.56, anchor="center")

        # Version watermark at bottom of sidebar
        tk.Label(
            self._sidebar, text=f"v{APP_VERSION}",
            font=(FONT, 9), bg=ACCENT, fg="#c5c6ff",
        ).place(relx=0.5, rely=0.94, anchor="center")

        # ── Right area ────────────────────────────────────────────────────────
        right = tk.Frame(self, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        # Page header — pack-based so it auto-sizes to content
        self._hdr_frame = tk.Frame(right, bg=PANEL)
        self._hdr_frame.pack(fill="x")

        self._title_lbl = tk.Label(
            self._hdr_frame, text="",
            font=(FONT, 13, "bold"), bg=PANEL, fg=FG, anchor="w",
        )
        self._title_lbl.pack(anchor="w", padx=24, pady=(14, 2))

        self._sub_lbl = tk.Label(
            self._hdr_frame, text="",
            font=(FONT, 10), bg=PANEL, fg=MUTED, anchor="w", wraplength=430,
            justify="left",
        )
        self._sub_lbl.pack(anchor="w", padx=24, pady=(0, 12))

        tk.Frame(right, bg=LINE, height=1).pack(fill="x")

        # Scrollable content area
        self._content = tk.Frame(right, bg=BG)
        self._content.pack(fill="both", expand=True)

        # Bottom nav bar
        tk.Frame(right, bg=LINE, height=1).pack(fill="x", side="bottom")
        nav = tk.Frame(right, bg=PANEL, height=52)
        nav.pack(fill="x", side="bottom")
        nav.pack_propagate(False)

        self._btn_cancel = tk.Button(
            nav, text="Cancel", width=10,
            bg=PANEL, fg=MUTED, activebackground=CARD, activeforeground=FG,
            font=(FONT, 10), relief="flat", cursor="hand2",
            command=self._on_cancel,
        )
        self._btn_cancel.pack(side="left", padx=12, pady=10)

        self._btn_back = tk.Button(
            nav, text="< Back", width=10,
            bg=CARD, fg=FG, activebackground=LINE, activeforeground=FG,
            font=(FONT, 10), relief="flat", cursor="hand2",
            command=self._on_back,
        )
        self._btn_back.pack(side="right", padx=(0, 8), pady=10)

        self._btn_next = tk.Button(
            nav, text="Next >", width=14,
            bg=ACCENT, fg="#fff", activebackground=ACCENT_H, activeforeground="#fff",
            font=(FONT, 10, "bold"), relief="flat", cursor="hand2",
            command=self._on_next,
        )
        self._btn_next.pack(side="right", padx=(0, 12), pady=10)

    # ── Page switching ────────────────────────────────────────────────────────

    def _show(self, name: str):
        if self._current and self._current in self._pages:
            self._pages[self._current].pack_forget()
        self._current = name
        pg = self._pages[name]
        pg.pack(fill="both", expand=True)

        cfg = self._page_config[name]
        self._title_lbl.config(text=cfg["title"])
        self._sub_lbl.config(text=cfg["sub"])
        self._step_lbl.config(text=cfg.get("step", ""))

        self._btn_back.config(state=cfg.get("back", "normal"))
        self._btn_next.config(
            text=cfg.get("next_label", "Next >"),
            state=cfg.get("next_state", "normal"),
            bg=cfg.get("next_bg", ACCENT),
        )
        self._btn_cancel.config(state=cfg.get("cancel", "normal"))

    # ── All pages ─────────────────────────────────────────────────────────────

    def _build_all_pages(self):
        self._page_config = {
            "welcome": {
                "title": f"Welcome to {APP_NAME} Setup",
                "sub":   "This wizard will install the application and configure AI models on your computer.",
                "step":  "Step 1 of 5\nWelcome",
                "back":  "disabled",
                "next_label": "Next >",
            },
            "models": {
                "title": "Select AI Models",
                "sub":   "Choose which AI models to download. You can add more inside the app later.",
                "step":  "Step 2 of 5\nSelect Models",
            },
            "options": {
                "title": "Installation Options",
                "sub":   "Choose where to install the app and which shortcuts to create.",
                "step":  "Step 3 of 5\nOptions",
            },
            "ready": {
                "title": "Ready to Install",
                "sub":   "Review your selections and click Install to begin.",
                "step":  "Step 4 of 5\nReady",
                "next_label": "  Install  ",
                "next_bg": SUCCESS,
            },
            "installing": {
                "title": "Installing…",
                "sub":   "Please wait while the app is installed and models are downloaded.",
                "step":  "Step 5 of 5\nInstalling",
                "back":  "disabled",
                "next_state": "disabled",
                "cancel": "disabled",
            },
            "finish": {
                "title": "Installation Complete",
                "sub":   f"{APP_NAME} has been installed successfully.",
                "step":  "✓ Done",
                "back":  "disabled",
                "next_label": "  Finish  ",
                "next_bg": SUCCESS,
                "cancel": "disabled",
            },
        }

        for name, builder in [
            ("welcome",    self._build_welcome),
            ("models",     self._build_models),
            ("options",    self._build_options),
            ("ready",      self._build_ready),
            ("installing", self._build_installing),
            ("finish",     self._build_finish),
        ]:
            frame = tk.Frame(self._content, bg=BG)
            self._pages[name] = frame
            builder(frame)

    # ── Page: Welcome ─────────────────────────────────────────────────────────

    def _build_welcome(self, f):
        pad = tk.Frame(f, bg=BG, padx=32, pady=28)
        pad.pack(fill="both", expand=True)

        tk.Label(pad,
                 text=f"Thank you for installing {APP_NAME}.",
                 font=(FONT, 12, "bold"), bg=BG, fg=FG).pack(anchor="w")

        body = (
            "This setup will:\n\n"
            "  •  Install the application to your computer\n"
            "  •  Download and configure Ollama (AI engine)\n"
            "  •  Download the AI models you select\n"
            "  •  Create shortcuts and register the app\n\n"
            "Click  Next  to continue."
        )
        tk.Label(pad, text=body, font=(FONT, 10), bg=BG, fg=MUTED,
                 justify="left", anchor="nw", wraplength=420).pack(anchor="w", pady=(12, 0))

        # Install location note
        note_f = tk.Frame(pad, bg=CARD, padx=14, pady=10)
        note_f.pack(fill="x", pady=(20, 0))
        tk.Label(note_f, text="ℹ  App will be installed to:",
                 font=(FONT, 9, "bold"), bg=CARD, fg=MUTED).pack(anchor="w")
        tk.Label(note_f, textvariable=self.install_dir,
                 font=("Consolas", 9), bg=CARD, fg=FG).pack(anchor="w")

    # ── Page: Models ──────────────────────────────────────────────────────────

    def _build_models(self, f):
        outer = tk.Frame(f, bg=BG, padx=28, pady=12)
        outer.pack(fill="both", expand=True)

        # Canvas + scrollbar so all models are reachable
        scroll_row = tk.Frame(outer, bg=BG)
        scroll_row.pack(fill="both", expand=True)

        sb = tk.Scrollbar(scroll_row, orient="vertical", bg=CARD,
                          troughcolor=BG, activebackground=LINE)
        sb.pack(side="right", fill="y")

        canvas = tk.Canvas(scroll_row, bg=BG, highlightthickness=0,
                           yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.config(command=canvas.yview)

        inner = tk.Frame(canvas, bg=BG)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_inner_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def _on_canvas_configure(e):
            canvas.itemconfig(win_id, width=e.width)
        inner.bind("<Configure>", _on_inner_configure)
        canvas.bind("<Configure>", _on_canvas_configure)

        # Mousewheel scroll (Windows)
        def _on_mousewheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        for mid, label, size, default, required in MODELS:
            card = tk.Frame(inner, bg=CARD, padx=14, pady=10)
            card.pack(fill="x", pady=4)

            top = tk.Frame(card, bg=CARD)
            top.pack(fill="x")

            var = self.model_vars[mid]
            cb = tk.Checkbutton(
                top, text=label, variable=var,
                bg=CARD, fg=FG, selectcolor="#444",
                activebackground=CARD, activeforeground=FG,
                font=(FONT, 11, "bold"), anchor="w",
                relief="flat",
                state="disabled" if required else "normal",
            )
            cb.pack(side="left")

            tags = tk.Frame(top, bg=CARD)
            tags.pack(side="right", padx=(0, 4))

            if required:
                self._tag(tags, "Required", "#e67e22", "#fff")
            self._tag(tags, size, CARD, MUTED, border=LINE)

            tk.Label(card, text=MODEL_DESC.get(mid, ""),
                     font=(FONT, 9), bg=CARD, fg=MUTED,
                     anchor="w", justify="left").pack(fill="x", pady=(4, 0))

        tk.Label(inner,
                 text="Additional models can be downloaded inside the app at any time.",
                 font=(FONT, 9), bg=BG, fg=MUTED).pack(anchor="w", pady=(8, 0))

    def _tag(self, parent, text, bg, fg, border=None):
        f = tk.Frame(parent, bg=border or bg,
                     padx=1 if border else 0, pady=1 if border else 0)
        f.pack(side="left", padx=3)
        tk.Label(f, text=text, font=(FONT, 8), bg=bg, fg=fg,
                 padx=6, pady=2).pack()

    # ── Page: Options ─────────────────────────────────────────────────────────

    def _build_options(self, f):
        pad = tk.Frame(f, bg=BG, padx=32, pady=20)
        pad.pack(fill="both", expand=True)

        # Install location
        tk.Label(pad, text="Installation folder",
                 font=(FONT, 10, "bold"), bg=BG, fg=FG).pack(anchor="w")
        tk.Label(pad,
                 text="The app will be installed here. You can change this if needed.",
                 font=(FONT, 9), bg=BG, fg=MUTED).pack(anchor="w", pady=(2, 8))

        dir_row = tk.Frame(pad, bg=BG)
        dir_row.pack(fill="x", pady=(0, 20))

        dir_entry = tk.Entry(
            dir_row, textvariable=self.install_dir,
            font=("Consolas", 10), bg=CARD, fg=FG,
            insertbackground=FG, relief="flat",
            highlightthickness=1, highlightbackground=LINE,
            highlightcolor=ACCENT,
        )
        dir_entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))

        tk.Button(
            dir_row, text="Browse…", width=9,
            bg=CARD, fg=FG, activebackground=LINE, activeforeground=FG,
            font=(FONT, 10), relief="flat", cursor="hand2",
            command=self._browse_dir,
        ).pack(side="left")

        # Shortcuts
        tk.Frame(pad, bg=LINE, height=1).pack(fill="x", pady=(0, 16))
        tk.Label(pad, text="Shortcuts",
                 font=(FONT, 10, "bold"), bg=BG, fg=FG).pack(anchor="w", pady=(0, 8))

        for var, text, sub in [
            (self.desktop_var,
             "Create a Desktop shortcut",
             "Adds a shortcut to your Desktop for quick access."),
            (self.startmenu_var,
             "Add to Start Menu",
             "Registers the app in the Start Menu and Windows Apps list."),
        ]:
            card = tk.Frame(pad, bg=CARD, padx=14, pady=10)
            card.pack(fill="x", pady=3)
            tk.Checkbutton(
                card, text=text, variable=var,
                bg=CARD, fg=FG, selectcolor="#444",
                activebackground=CARD, activeforeground=FG,
                font=(FONT, 10), anchor="w", relief="flat",
            ).pack(anchor="w")
            tk.Label(card, text=sub, font=(FONT, 9), bg=CARD, fg=MUTED,
                     anchor="w").pack(anchor="w", padx=(22, 0))

    def _browse_dir(self):
        chosen = filedialog.askdirectory(
            title="Choose installation folder",
            initialdir=self.install_dir.get(),
        )
        if chosen:
            self.install_dir.set(str(Path(chosen) / APP_NAME))

    # ── Page: Ready ───────────────────────────────────────────────────────────

    def _build_ready(self, f):
        self._ready_frame = f   # rebuilt on show
        # Actual content drawn in _refresh_ready()

    def _refresh_ready(self):
        for w in self._ready_frame.winfo_children():
            w.destroy()

        pad = tk.Frame(self._ready_frame, bg=BG, padx=32, pady=16)
        pad.pack(fill="both", expand=True)

        tk.Label(pad, text="The following will be installed:",
                 font=(FONT, 10, "bold"), bg=BG, fg=FG).pack(anchor="w", pady=(0, 12))

        install_path = Path(self.install_dir.get())

        rows = [
            ("App binaries",  str(install_path)),
            ("User data",     str(APP_DATA)),
            ("Models",        ", ".join(
                lbl for mid, lbl, *_ in MODELS
                if self.model_vars[mid].get()
            )),
        ]
        if self.desktop_var.get():
            rows.append(("Desktop shortcut", "✓"))
        if self.startmenu_var.get():
            rows.append(("Start Menu & Apps list", "✓"))

        for key, val in rows:
            row = tk.Frame(pad, bg=CARD, padx=14, pady=8)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=key, font=(FONT, 10, "bold"), bg=CARD, fg=FG,
                     width=22, anchor="w").pack(side="left")
            tk.Label(row, text=val, font=(FONT, 9), bg=CARD, fg=MUTED,
                     anchor="w", wraplength=260, justify="left").pack(side="left")

        tk.Label(pad,
                 text="Downloading AI models may take 10–40 minutes depending on your connection.",
                 font=(FONT, 9), bg=BG, fg=MUTED, wraplength=440,
                 justify="left").pack(anchor="w", pady=(14, 0))

    # ── Page: Installing ──────────────────────────────────────────────────────

    def _build_installing(self, f):
        pad = tk.Frame(f, bg=BG, padx=32, pady=20)
        pad.pack(fill="both", expand=True)

        # Step list
        self._step_items: dict[str, tk.Label] = {}
        steps = [
            ("binaries",   "Installing application files"),
            ("data",       "Creating data directories"),
            ("kb",         "Copying knowledge base"),
            ("ollama",     "Setting up Ollama"),
            ("models",     "Downloading AI models"),
            ("shortcuts",  "Creating shortcuts"),
            ("registry",   "Registering application"),
        ]
        step_frame = tk.Frame(pad, bg=BG)
        step_frame.pack(fill="x")

        for key, label in steps:
            row = tk.Frame(step_frame, bg=BG)
            row.pack(fill="x", pady=2)
            icon = tk.Label(row, text="○", font=(FONT, 11), bg=BG, fg=LINE, width=2)
            icon.pack(side="left")
            tk.Label(row, text=label, font=(FONT, 10), bg=BG, fg=MUTED,
                     anchor="w").pack(side="left", padx=(6, 0))
            self._step_items[key] = icon

        # Progress bar
        style = ttk.Style()
        style.theme_use("default")
        style.configure("I.Horizontal.TProgressbar",
                        troughcolor=CARD, background=ACCENT,
                        thickness=6, borderwidth=0)
        self._progress = ttk.Progressbar(
            pad, style="I.Horizontal.TProgressbar", mode="indeterminate")
        self._progress.pack(fill="x", pady=(16, 8))

        self._status_var = tk.StringVar(value="Starting…")
        tk.Label(pad, textvariable=self._status_var,
                 font=(FONT, 9), bg=BG, fg=MUTED).pack(anchor="w")

        # Log
        self._log_box = tk.Text(
            pad, height=5, bg="#111", fg="#aaa",
            font=("Consolas", 8), state="disabled",
            relief="flat", padx=8, pady=6, wrap="word",
        )
        self._log_box.pack(fill="x", pady=(10, 0))

    def _step_set(self, key: str, state: str):
        """state: pending | active | done | error"""
        icon, colour = {
            "pending": ("○", LINE),
            "active":  ("◉", ACCENT),
            "done":    ("✓", SUCCESS),
            "error":   ("✗", DANGER),
        }[state]
        lbl = self._step_items.get(key)
        if lbl:
            self.after(0, lambda: lbl.config(text=icon, fg=colour))

    def _log(self, msg: str):
        def _do():
            self._log_box.config(state="normal")
            self._log_box.insert("end", msg + "\n")
            self._log_box.see("end")
            self._log_box.config(state="disabled")
        self.after(0, _do)

    def _status(self, msg: str):
        self.after(0, lambda: self._status_var.set(msg))

    # ── Page: Finish ──────────────────────────────────────────────────────────

    def _build_finish(self, f):
        center = tk.Frame(f, bg=BG)
        center.place(relx=0.5, rely=0.46, anchor="center")

        tk.Label(center, text="✓", font=(FONT, 42), bg=BG, fg=SUCCESS).pack()
        tk.Label(center,
                 text=f"{APP_NAME} is installed!",
                 font=(FONT, 14, "bold"), bg=BG, fg=FG).pack(pady=(10, 4))
        tk.Label(center,
                 text="Click Finish to close this wizard.",
                 font=(FONT, 10), bg=BG, fg=MUTED).pack()

        cb_frame = tk.Frame(f, bg=BG)
        cb_frame.place(relx=0.5, rely=0.78, anchor="center")
        tk.Checkbutton(
            cb_frame, text=f"Launch {APP_NAME} now",
            variable=self.launch_var,
            bg=BG, fg=FG, selectcolor="#444",
            activebackground=BG, activeforeground=FG,
            font=(FONT, 10), relief="flat",
        ).pack()

    # ── Navigation ────────────────────────────────────────────────────────────

    _ORDER = ["welcome", "models", "options", "ready", "installing", "finish"]

    def _on_next(self):
        cur = self._current

        if cur == "models":
            llms = [m for m, lbl, *_, req in MODELS
                    if self.model_vars[m].get() and not req]
            if not llms:
                messagebox.showwarning(
                    "No LLM selected",
                    "Please select at least one language model (not counting nomic-embed-text).")
                return

        if cur == "ready":
            self._show("installing")
            self._progress.start(12)
            models = [m for m, var in self.model_vars.items() if var.get()]
            self._install_thread = threading.Thread(
                target=self._run_install, args=(models,), daemon=True)
            self._install_thread.start()
            return

        if cur == "finish":
            if self.launch_var.get():
                self._show_launch_screen()
            else:
                self.destroy()
            return

        idx = self._ORDER.index(cur)
        if cur == "ready":
            self._refresh_ready()
        next_page = self._ORDER[idx + 1]
        if next_page == "ready":
            self._refresh_ready()
        self._show(next_page)

    def _on_back(self):
        idx = self._ORDER.index(self._current)
        self._show(self._ORDER[idx - 1])

    def _on_cancel(self):
        if messagebox.askyesno("Cancel Setup",
                               "Are you sure you want to cancel installation?"):
            self.destroy()

    # ── Install logic ─────────────────────────────────────────────────────────

    def _run_install(self, models: list):
        install_path = Path(self.install_dir.get())
        installed_exe        = install_path / "ISO_Manual_Assistant.exe"
        installed_uninstaller= install_path / "ISO_Manual_Assistant_Uninstall.exe"

        try:
            # ── 1. App binaries ───────────────────────────────────────────────
            self._step_set("binaries", "active")
            self._status("Installing application files…")
            if not APP_SRC_DIR.exists():
                raise FileNotFoundError(
                    f"App folder not found next to Setup.exe:\n{APP_SRC_DIR}\n"
                    "Make sure the full package was extracted."
                )
            if install_path.exists():
                self._log("Removing previous installation…")
                shutil.rmtree(install_path)
            shutil.copytree(APP_SRC_DIR, install_path)
            if not installed_exe.exists():
                raise FileNotFoundError(f"Exe not found after copy: {installed_exe}")
            if UNINSTALLER_SRC.exists():
                shutil.copy2(UNINSTALLER_SRC, installed_uninstaller)
            self._step_set("binaries", "done")
            self._log(f"✓ App installed to {install_path}")

            # ── 2. Data dirs ──────────────────────────────────────────────────
            self._step_set("data", "active")
            self._status("Creating data directories…")
            APP_DATA.mkdir(parents=True, exist_ok=True)
            (APP_DATA / "data").mkdir(exist_ok=True)
            (APP_DATA / "data" / "approved_documents").mkdir(exist_ok=True)
            self._step_set("data", "done")

            # ── 3. Knowledge base ─────────────────────────────────────────────
            self._step_set("kb", "active")
            if VECTOR_DB_SRC.exists():
                self._status("Copying knowledge base…")
                dest = APP_DATA / "data" / "vector_db"
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(VECTOR_DB_SRC, dest)
                self._log("✓ Knowledge base copied.")
            else:
                self._log("— No pre-built KB found, skipping.")
            self._step_set("kb", "done")

            # ── 4. Ollama ─────────────────────────────────────────────────────
            self._step_set("ollama", "active")
            self._status("Checking Ollama…")
            ollama = self._ollama_exe()
            if ollama:
                self._log(f"✓ Ollama already installed.")
            else:
                self._log("Downloading Ollama…")
                self._download_ollama()
                ollama = self._ollama_exe() or "ollama"
            self._status("Starting Ollama service…")
            self._start_ollama(ollama)
            self._step_set("ollama", "done")

            # ── 5. Models ─────────────────────────────────────────────────────
            self._step_set("models", "active")
            for i, mid in enumerate(models, 1):
                self._status(f"Downloading model {i}/{len(models)}: {mid}")
                self._log(f"Pulling {mid}…")
                ok, err = self._pull_model(mid, ollama)
                if ok:
                    self._log(f"✓ {mid}")
                else:
                    self._log(f"⚠ {mid} failed: {err} — run: ollama pull {mid}")
            self._step_set("models", "done")

            # ── 6. Shortcuts ──────────────────────────────────────────────────
            self._step_set("shortcuts", "active")
            self._status("Creating shortcuts…")
            if self.desktop_var.get():
                self._create_shortcut(
                    installed_exe, install_path,
                    self._get_desktop() / f"{APP_NAME}.lnk",
                )
            if self.startmenu_var.get():
                START_MENU_DIR.mkdir(parents=True, exist_ok=True)
                self._create_shortcut(
                    installed_exe, install_path,
                    START_MENU_DIR / f"{APP_NAME}.lnk",
                )
            self._step_set("shortcuts", "done")
            self._log("✓ Shortcuts created.")

            # ── 7. Registry ───────────────────────────────────────────────────
            self._step_set("registry", "active")
            self._status("Registering application…")
            size_kb = self._dir_size_kb(install_path)
            self._write_registry(installed_exe, installed_uninstaller, install_path, size_kb)
            self._step_set("registry", "done")
            self._log("✓ Registered in Windows Apps list.")

            # ── Done ──────────────────────────────────────────────────────────
            self.after(0, lambda: self._progress.stop())
            self.after(0, lambda: self._progress.config(
                mode="determinate", value=100))
            self._status("✓ Installation complete!")
            time.sleep(0.6)
            self.after(0, lambda: self._show("finish"))

        except Exception as exc:
            self._step_set("binaries", "error") if True else None
            self._log(f"\n❌ Installation failed: {exc}")
            self._status(f"Error: {exc}")
            self.after(0, lambda: self._progress.stop())
            self.after(0, lambda: self._btn_next.config(
                state="normal", text="Retry", bg=DANGER,
                command=lambda: threading.Thread(
                    target=self._run_install, args=(models,), daemon=True
                ).start()
            ))

    # ── OS / install helpers ──────────────────────────────────────────────────

    def _ollama_exe(self) -> str | None:
        p = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe"
        if p.exists(): return str(p)
        return shutil.which("ollama")

    def _download_ollama(self):
        tmp = Path(os.environ.get("TEMP", "")) / "OllamaSetup.exe"
        ok = False
        for url in OLLAMA_URLS:
            try:
                self._log(f"  Downloading from {url}…")
                urllib.request.urlretrieve(url, tmp)
                if tmp.exists() and tmp.stat().st_size > 500_000:
                    ok = True; break
            except Exception as e:
                self._log(f"  Failed: {e}")
        if not ok:
            raise RuntimeError(
                "Could not download Ollama. "
                "Install manually from https://ollama.com then rerun Setup.")
        result = subprocess.run([str(tmp), "/VERYSILENT", "/NORESTART"])
        if result.returncode not in (0, 3010):
            raise RuntimeError(f"Ollama installer failed (code {result.returncode})")
        time.sleep(2)

    def _start_ollama(self, exe: str):
        subprocess.Popen([exe, "serve"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(4)

    def _pull_model(self, model_id: str, exe: str) -> tuple[bool, str]:
        try:
            r = subprocess.run([exe, "pull", model_id], capture_output=True)
            def _d(b): return (b or b"").decode("utf-8", errors="replace").strip()
            return r.returncode == 0, _d(r.stderr) or _d(r.stdout)
        except Exception as e:
            return False, str(e)

    @staticmethod
    def _get_desktop() -> Path:
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders")
            val, _ = winreg.QueryValueEx(key, "Desktop")
            winreg.CloseKey(key)
            p = Path(val)
            if p.exists(): return p
        except Exception:
            pass
        for c in [Path(os.environ.get("USERPROFILE", "")) / "Desktop",
                  Path.home() / "Desktop"]:
            if c.exists(): return c
        return Path.home() / "Desktop"

    @staticmethod
    def _create_shortcut(exe: Path, cwd: Path, dest: Path):
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            import win32com.client  # type: ignore
            sh  = win32com.client.Dispatch("WScript.Shell")
            lnk = sh.CreateShortCut(str(dest))
            lnk.Targetpath       = str(exe)
            lnk.WorkingDirectory = str(cwd)
            lnk.Description      = APP_NAME
            lnk.save()
        except ImportError:
            bat = dest.with_suffix(".bat")
            bat.parent.mkdir(parents=True, exist_ok=True)
            bat.write_text(f'@echo off\nstart "" "{exe}"\n', encoding="utf-8")

    @staticmethod
    def _dir_size_kb(path: Path) -> int:
        total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
        return max(1, total // 1024)

    @staticmethod
    def _write_registry(exe: Path, uninstaller: Path, install_path: Path, size_kb: int):
        import winreg
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\ISOManualAssistant"
        today    = datetime.date.today().strftime("%Y%m%d")

        uninstall_str = (
            str(uninstaller) if uninstaller.exists()
            else str(exe)
        )

        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key_path,
                                0, winreg.KEY_SET_VALUE) as k:
            def sv(name, val, kind=winreg.REG_SZ):
                winreg.SetValueEx(k, name, 0, kind, val)

            sv("DisplayName",          APP_NAME)
            sv("DisplayVersion",       APP_VERSION)
            sv("Publisher",            APP_PUBLISHER)
            sv("InstallLocation",      str(install_path))
            sv("DisplayIcon",          f"{exe},0")
            sv("UninstallString",      f'"{uninstall_str}"')
            sv("QuietUninstallString", f'"{uninstall_str}" /S')
            sv("InstallDate",          today)
            sv("URLInfoAbout",         "https://github.com/your-org/iso-manual-assistant")
            sv("HelpLink",             "https://github.com/your-org/iso-manual-assistant")
            sv("EstimatedSize",        size_kb,  winreg.REG_DWORD)
            sv("NoModify",             1,        winreg.REG_DWORD)
            sv("NoRepair",             1,        winreg.REG_DWORD)
            sv("Language",             1033,     winreg.REG_DWORD)

    # ── Launch screen ─────────────────────────────────────────────────────────

    def _show_launch_screen(self):
        """Replace the wizard UI with a full-window spinner while the app starts."""
        # Hide sidebar and all content
        for w in self.winfo_children():
            w.pack_forget()

        self.configure(bg=BG)
        frame = tk.Frame(self, bg=BG)
        frame.place(relx=0.5, rely=0.44, anchor="center")

        self._spinner_chars = list("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏")
        self._spinner_idx   = 0
        self._spinner_job   = None

        self._spin_lbl = tk.Label(
            frame, text="⠋", font=("Consolas", 38), bg=BG, fg=ACCENT)
        self._spin_lbl.pack()

        tk.Label(frame, text=f"Starting {APP_NAME}…",
                 font=(FONT, 13, "bold"), bg=BG, fg=FG).pack(pady=(12, 4))

        self._launch_sub = tk.Label(
            frame,
            text="This can take 15–30 seconds on first launch.",
            font=(FONT, 10), bg=BG, fg=MUTED, justify="center")
        self._launch_sub.pack()

        self._animate_spinner()

        def _do_launch():
            exe = Path(self.install_dir.get()) / "ISO_Manual_Assistant.exe"
            launched = False
            if exe.exists():
                try:
                    subprocess.Popen(
                        [str(exe)], cwd=str(exe.parent),
                        creationflags=(subprocess.DETACHED_PROCESS |
                                       subprocess.CREATE_NEW_PROCESS_GROUP),
                    )
                    launched = True
                except Exception:
                    pass
            # Wait up to 20 s, updating the sub-label every 5 s
            for tick in range(20):
                time.sleep(1)
                if tick == 10:
                    self.after(0, lambda: self._launch_sub.config(
                        text="Still starting — please wait a moment…"))
            # Done waiting
            if launched:
                self.after(0, self.destroy)
            else:
                self.after(0, self._show_manual_launch, exe)

        threading.Thread(target=_do_launch, daemon=True).start()

    def _animate_spinner(self):
        if not hasattr(self, '_spin_lbl') or not self._spin_lbl.winfo_exists():
            return
        self._spin_lbl.config(
            text=self._spinner_chars[self._spinner_idx % len(self._spinner_chars)])
        self._spinner_idx += 1
        self._spinner_job = self.after(80, self._animate_spinner)

    def _show_manual_launch(self, exe: Path):
        if self._spinner_job:
            self.after_cancel(self._spinner_job)
        for w in self.winfo_children():
            w.destroy()

        frame = tk.Frame(self, bg=BG)
        frame.place(relx=0.5, rely=0.44, anchor="center")

        tk.Label(frame, text="⚠", font=(FONT, 36), bg=BG, fg="#e67e22").pack()
        tk.Label(frame, text="App did not open automatically.",
                 font=(FONT, 13, "bold"), bg=BG, fg=FG).pack(pady=(10, 4))
        tk.Label(frame,
                 text="You can launch it from the Desktop shortcut\nor from the Start Menu.",
                 font=(FONT, 10), bg=BG, fg=MUTED, justify="center").pack()

        path_f = tk.Frame(frame, bg=CARD, padx=12, pady=8)
        path_f.pack(fill="x", pady=(14, 0))
        tk.Label(path_f, text="Install location:",
                 font=(FONT, 9), bg=CARD, fg=MUTED).pack(anchor="w")
        tk.Label(path_f, text=str(exe),
                 font=("Consolas", 8), bg=CARD, fg=FG,
                 wraplength=380, justify="left").pack(anchor="w")

        tk.Button(
            frame, text="  Close  ", width=14,
            bg=SUCCESS, fg="#fff", activebackground="#3a9e6e",
            activeforeground="#fff", font=(FONT, 10, "bold"),
            relief="flat", cursor="hand2", command=self.destroy,
        ).pack(pady=(20, 0))

    # ── Launch ────────────────────────────────────────────────────────────────

    def _launch_app(self):
        exe = Path(self.install_dir.get()) / "ISO_Manual_Assistant.exe"
        if exe.exists():
            subprocess.Popen(
                [str(exe)], cwd=str(exe.parent),
                creationflags=(subprocess.DETACHED_PROCESS |
                               subprocess.CREATE_NEW_PROCESS_GROUP),
            )


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = SetupWizard()
    app.mainloop()
