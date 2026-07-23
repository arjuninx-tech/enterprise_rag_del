"""
setup_wizard/uninstaller.py
───────────────────────────
Standalone uninstaller for ISO Manual Assistant.
Compiled by PyInstaller into ISO_Manual_Assistant_Uninstall.exe
and placed inside %LOCALAPPDATA%\ISO Manual Assistant\ during setup.

Registered as the UninstallString in the Windows registry so it appears
in Settings → Apps → "Add or Remove Programs".

What it removes
───────────────
  Always:
    - App binaries  (%LOCALAPPDATA%\ISO Manual Assistant\)
    - Desktop shortcut
    - Start Menu entry
    - "Add or Remove Programs" registry entry

  On request (user is asked):
    - User data (%APPDATA%\ISO Manual Assistant\)
      includes chat history, uploaded documents, and the knowledge base
"""

import os
import sys
import shutil
import subprocess
import threading
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

# ── Paths ─────────────────────────────────────────────────────────────────────

APP_NAME    = "ISO Manual Assistant"
APP_DATA    = Path(os.environ.get("APPDATA", Path.home())) / APP_NAME

def _read_install_dir() -> Path:
    """Read the real install location from the registry (user may have changed it)."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\ISOManualAssistant",
        )
        val, _ = winreg.QueryValueEx(key, "InstallLocation")
        winreg.CloseKey(key)
        return Path(val)
    except Exception:
        pass
    # Fallback: directory this exe is running from (likely correct)
    return Path(sys.executable).parent

INSTALL_DIR = _read_install_dir()
START_MENU  = (
    Path(os.environ.get("APPDATA", "")) /
    "Microsoft" / "Windows" / "Start Menu" / "Programs" / APP_NAME
)
UNINSTALL_REG_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\ISOManualAssistant"

# ── Colours ───────────────────────────────────────────────────────────────────

BG      = "#1e1e1e"
BG2     = "#2a2a2a"
FG      = "#e0e0e0"
FG_MUTED= "#888888"
ACCENT  = "#6366f1"
DANGER  = "#e5533d"
SUCCESS = "#4caf82"
BORDER  = "#3a3a3a"


class Uninstaller:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"Uninstall {APP_NAME}")
        self.root.geometry("520x440")
        self.root.resizable(True, False)
        self.root.configure(bg=BG)
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth()  - 520) // 2
        y = (self.root.winfo_screenheight() - 440) // 2
        self.root.geometry(f"520x440+{x}+{y}")
        self._build_ui()

    def _build_ui(self):
        # ── Pack bottom widgets FIRST so tkinter reserves their space ─────────

        # Status label (very bottom)
        self.status_var = tk.StringVar(value="")
        tk.Label(self.root, textvariable=self.status_var,
                 font=("Segoe UI", 9), bg=BG, fg=FG_MUTED).pack(side="bottom", pady=(0, 4))

        # Button bar
        tk.Frame(self.root, bg=BORDER, height=1).pack(side="bottom", fill="x")
        bf = tk.Frame(self.root, bg=BG, pady=14)
        bf.pack(side="bottom", fill="x")

        tk.Button(
            bf, text="  Cancel  ", width=12,
            bg=BG2, fg=FG, activebackground=BORDER, activeforeground=FG,
            font=("Segoe UI", 10), relief="flat", cursor="hand2",
            command=self.root.destroy,
        ).pack(side="right", padx=(0, 16))

        self.btn_uninstall = tk.Button(
            bf, text="  Uninstall  ", width=14,
            bg=DANGER, fg="#ffffff", activebackground="#c94030",
            activeforeground="#ffffff", font=("Segoe UI", 10, "bold"),
            relief="flat", cursor="hand2",
            command=self._confirm_and_uninstall,
        )
        self.btn_uninstall.pack(side="right", padx=(0, 8))

        # ── Top content fills remaining space ─────────────────────────────────

        # Header
        hdr = tk.Frame(self.root, bg=BG, pady=16)
        hdr.pack(side="top", fill="x")
        tk.Label(hdr, text=f"Uninstall {APP_NAME}",
                 font=("Segoe UI", 15, "bold"), bg=BG, fg=FG).pack()
        tk.Label(hdr, text="This will remove the application from your computer.",
                 font=("Segoe UI", 10), bg=BG, fg=FG_MUTED).pack(pady=(4, 0))

        tk.Frame(self.root, bg=BORDER, height=1).pack(side="top", fill="x")

        # Options
        opts = tk.Frame(self.root, bg=BG, padx=32, pady=16)
        opts.pack(side="top", fill="x")

        tk.Label(opts, text="The following will always be removed:",
                 font=("Segoe UI", 10, "bold"), bg=BG, fg=FG).pack(anchor="w", pady=(0, 6))

        always = [
            f"App files   ({INSTALL_DIR})",
            "Desktop shortcut",
            "Start Menu entry",
            "Windows Apps list entry",
        ]
        for item in always:
            row = tk.Frame(opts, bg=BG)
            row.pack(fill="x", pady=1)
            tk.Label(row, text="✕", fg=DANGER, bg=BG,
                     font=("Segoe UI", 10)).pack(side="left", padx=(0, 8))
            tk.Label(row, text=item, font=("Segoe UI", 10), bg=BG,
                     fg=FG_MUTED, anchor="w").pack(side="left")

        tk.Frame(opts, bg=BORDER, height=1).pack(fill="x", pady=(12, 10))

        tk.Label(opts, text="Optional:",
                 font=("Segoe UI", 10, "bold"), bg=BG, fg=FG).pack(anchor="w", pady=(0, 6))

        self.keep_data_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            opts,
            text="Keep my documents, chat history and knowledge base",
            variable=self.keep_data_var,
            bg=BG, fg=FG, selectcolor="#444",
            activebackground=BG, activeforeground=FG,
            font=("Segoe UI", 10), anchor="w",
            relief="flat",
        ).pack(anchor="w")
        tk.Label(opts, text=str(APP_DATA),
                 font=("Consolas", 8), bg=BG, fg=FG_MUTED,
                 anchor="w").pack(anchor="w", padx=(22, 0))

    def _confirm_and_uninstall(self):
        keep = self.keep_data_var.get()
        msg = (
            f"This will permanently remove {APP_NAME} from your computer.\n\n"
            + ("Your documents and chat history will be KEPT.\n\n"
               if keep else
               "⚠  Your documents, chat history and knowledge base will also be DELETED.\n\n")
            + "Are you sure you want to continue?"
        )
        if not messagebox.askyesno("Confirm Uninstall", msg, icon="warning"):
            return
        self.btn_uninstall.config(state="disabled", text="  Removing…  ")
        threading.Thread(target=self._uninstall, args=(keep,), daemon=True).start()

    def _status(self, msg: str):
        self.status_var.set(msg)
        self.root.update_idletasks()

    def _uninstall(self, keep_data: bool):
        try:
            self._status("Removing shortcuts…")
            self._remove_desktop_shortcut()
            self._remove_startmenu()
            self._remove_registry()

            if not keep_data:
                self._status("Removing user data…")
                self._remove_user_data()

            # Schedule deletion of INSTALL_DIR (including this exe) via a
            # temp batch script that runs AFTER this process exits.
            self._status("Scheduling app files removal…")
            self._schedule_dir_removal(INSTALL_DIR)

            self._status("Done.")
            self.root.after(0, self._show_done)

        except Exception as exc:
            self.root.after(0, lambda: messagebox.showerror(
                "Uninstall Error", f"Uninstall failed:\n{exc}"))
            self.root.after(0, lambda: self.btn_uninstall.config(
                state="normal", text="  Uninstall  "))

    # ── Removal helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _get_desktop_path() -> Path:
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
            )
            desktop, _ = winreg.QueryValueEx(key, "Desktop")
            winreg.CloseKey(key)
            p = Path(desktop)
            if p.exists():
                return p
        except Exception:
            pass
        for c in [Path(os.environ.get("USERPROFILE", "")) / "Desktop",
                  Path.home() / "Desktop"]:
            if c.exists():
                return c
        return Path.home() / "Desktop"

    def _remove_desktop_shortcut(self):
        desktop = self._get_desktop_path()
        for ext in (".lnk", ".bat"):
            f = desktop / f"{APP_NAME}{ext}"
            if f.exists():
                f.unlink()

    def _remove_startmenu(self):
        if START_MENU.exists():
            shutil.rmtree(START_MENU, ignore_errors=True)

    def _remove_registry(self):
        try:
            import winreg
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, UNINSTALL_REG_KEY)
        except FileNotFoundError:
            pass   # already gone
        except Exception:
            pass

    def _remove_user_data(self):
        if APP_DATA.exists():
            shutil.rmtree(APP_DATA, ignore_errors=True)

    def _schedule_dir_removal(self, target: Path):
        """
        Write a temp .bat that waits 3 seconds (for this process to exit)
        then deletes the install directory, then deletes itself.
        """
        script = (
            "@echo off\n"
            "timeout /t 3 /nobreak >nul\n"
            f'rd /s /q "{target}"\n'
            'del "%~f0"\n'
        )
        bat = Path(os.environ.get("TEMP", Path.home())) / "iso_uninstall_cleanup.bat"
        bat.write_text(script, encoding="utf-8")
        subprocess.Popen(
            ["cmd", "/c", str(bat)],
            creationflags=(
                subprocess.DETACHED_PROCESS |
                subprocess.CREATE_NEW_PROCESS_GROUP |
                subprocess.CREATE_NO_WINDOW
            ),
        )

    # ── Done screen ───────────────────────────────────────────────────────────

    def _show_done(self):
        for w in self.root.winfo_children():
            w.destroy()
        frame = tk.Frame(self.root, bg=BG)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(frame, text="✓", font=("Segoe UI", 40),
                 bg=BG, fg=SUCCESS).pack()
        tk.Label(frame, text=f"{APP_NAME} has been uninstalled.",
                 font=("Segoe UI", 14, "bold"), bg=BG, fg=FG).pack(pady=(12, 4))
        tk.Label(frame,
                 text="The app files will be removed after this window closes.",
                 font=("Segoe UI", 10), bg=BG, fg=FG_MUTED).pack()
        tk.Button(
            frame, text="  Close  ", width=14,
            bg=SUCCESS, fg="#ffffff", activebackground="#3a9e6e",
            activeforeground="#ffffff", font=("Segoe UI", 10, "bold"),
            relief="flat", cursor="hand2", command=self.root.destroy,
        ).pack(pady=(20, 0))

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    Uninstaller().run()
