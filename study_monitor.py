import os
import sys
import json
import csv
import math
import time
import threading
import random
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

try:
    import cv2
    import mediapipe as mp
    import psutil
    import winsound
    import pygame
    from plyer import notification
    import win32gui
    import win32process
except ImportError as exc:
    missing = str(exc)
    raise SystemExit(
        "A required package is missing. Install dependencies with:\n"
        "py -3.11 -m pip install -r requirements.txt\n\nDetails: " + missing
    )

APP_NAME = "Study Monitor"
DATA_DIR = os.path.join(os.getenv("APPDATA", os.path.expanduser("~")), "StudyMonitor")
CONFIG_FILE = os.path.join(DATA_DIR, "settings.txt")
STATS_FILE = os.path.join(DATA_DIR, "stats.json")
AUDIO_DIR = os.path.join(DATA_DIR, "audio")
AUDIO_CONFIG = os.path.join(DATA_DIR, "audio_settings.json")
EVENTS_FILE = os.path.join(DATA_DIR, "events.csv")
DEFAULT_ALLOWED = ["studymonitor.exe", "python.exe", "pythonw.exe", "explorer.exe", "applicationframehost.exe", "searchhost.exe", "startmenuexperiencehost.exe", "textinputhost.exe", "notepad.exe", "acrobat.exe", "msedge.exe", "chrome.exe", "onenote.exe", "onenoteim.exe"]
DEFAULT_BLOCKED = ["discord.exe", "steam.exe", "epicgameslauncher.exe", "spotify.exe", "telegram.exe"]
APP_DIR = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, "frozen", False) else __file__))
RESOURCE_DIR = getattr(sys, "_MEIPASS", APP_DIR)
DISTRACTION_AUDIO = os.path.join(RESOURCE_DIR, "Kyu_Nhi_Ho_Rhi_Padhai_Meme_Download.mp3")

# MediaPipe Face Mesh eye landmark indices (approximate eye aspect ratio).
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

def eye_aspect_ratio(landmarks, indices, width, height):
    import math
    pts = []
    for idx in indices:
        p = landmarks[idx]
        pts.append((p.x * width, p.y * height))
    def dist(a, b):
        return math.hypot(a[0] - b[0], a[1] - b[1])
    vertical = dist(pts[1], pts[5]) + dist(pts[2], pts[4])
    horizontal = 2.0 * dist(pts[0], pts[3])
    return vertical / horizontal if horizontal else 1.0

class StudyMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Study Monitor")
        self.root.geometry("1020x720")
        self.root.minsize(900, 640)
        self.root.configure(bg="#10131b")

        self.running = False
        self.session_started = None
        self.elapsed_before_pause = 0
        self.camera_thread = None
        self.stop_event = threading.Event()
        self.camera_status = "Camera idle"
        self.drowsy_status = "Not monitoring"
        self.current_app = "—"
        self.last_alert = 0
        self.last_drowsy_alert = 0
        self.closed_eye_since = None
        self.last_head_y = None
        self.head_drop_since = None
        self.drowsy_frames = 0
        self.away_since = None
        self.last_focus_tick = time.time()
        self.focus_seconds = 0
        self.xp = 0
        self.level = 1
        self.daily_streak = 0
        self.last_study_date = ""
        self.session_date = datetime.now().strftime("%Y-%m-%d")
        self.load_stats()
        self.audio_files = {}
        self.audio_assignments = {"Distraction warning": "", "Drowsiness alert": "", "Session complete": "", "Break reminder": "", "Motivation": ""}
        self.audio_volume = 100
        self._alert_audio_index = 0
        self._alert_overlay = None
        self._voice_listening = False
        self.load_audio_settings()
        self.ensure_default_audio()
        self.app_checks = 0
        self.distraction_count = 0
        self.drowsy_count = 0
        self.focus_seconds = 0
        self.last_distraction_key = None
        self.last_foreground_name = None
        self.distraction_hits = {}
        self.close_on_second = tk.BooleanVar(value=True)
        self.allowed_apps = DEFAULT_ALLOWED[:]
        self.blocked_apps = DEFAULT_BLOCKED[:]
        self.load_config()
        self.build_ui()
        self.refresh_progress_label()
        self.update_clock()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground="#202635", background="#202635", foreground="#f2f4f8")
        self.create_header()

        body = tk.Frame(self.root, bg="#10131b")
        body.pack(fill="both", expand=True, padx=22, pady=(12, 22))
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        left = tk.Frame(body, bg="#171c28", highlightbackground="#2b3244", highlightthickness=1)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        right = tk.Frame(body, bg="#171c28", highlightbackground="#2b3244", highlightthickness=1)
        right.grid(row=0, column=1, sticky="nsew", padx=(12, 0))

        tk.Label(left, text="FOCUS SESSION", bg="#171c28", fg="#a8b2c7",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=22, pady=(22, 5))
        self.timer_label = tk.Label(left, text="00:00:00", bg="#171c28", fg="#f4f7ff",
                                    font=("Segoe UI", 42, "bold"))
        self.timer_label.pack(anchor="w", padx=20, pady=(0, 2))
        self.session_label = tk.Label(left, text="Ready when you are", bg="#171c28", fg="#8995ad",
                                      font=("Segoe UI", 10))
        self.session_label.pack(anchor="w", padx=22)

        controls = tk.Frame(left, bg="#171c28")
        controls.pack(fill="x", padx=22, pady=20)
        self.start_button = tk.Button(controls, text="▶  Start session", command=self.start_session,
                                      bg="#5b7cfa", fg="white", activebackground="#4566e5",
                                      activeforeground="white", relief="flat", bd=0, padx=18, pady=11,
                                      font=("Segoe UI", 10, "bold"), cursor="hand2")
        self.start_button.pack(side="left")
        self.pause_button = tk.Button(controls, text="Ⅱ  Pause", command=self.pause_session,
                                      bg="#252c3c", fg="#e9edf7", activebackground="#30394d",
                                      activeforeground="white", relief="flat", bd=0, padx=18, pady=11,
                                      font=("Segoe UI", 10), cursor="hand2", state="disabled")
        self.pause_button.pack(side="left", padx=10)
        tk.Button(controls, text="Reset", command=self.reset_session, bg="#252c3c", fg="#e9edf7",
                  activebackground="#30394d", relief="flat", bd=0, padx=16, pady=11,
                  font=("Segoe UI", 10), cursor="hand2").pack(side="left")

        self.stat_cards = tk.Frame(left, bg="#171c28")
        self.stat_cards.pack(fill="x", padx=18, pady=(0, 16))
        self.focus_stat = self.stat_card(self.stat_cards, "FOCUS TIME", "00:00", "#6f91ff")
        self.distraction_stat = self.stat_card(self.stat_cards, "DISTRACTIONS", "0", "#ffb86b")
        self.drowsy_stat = self.stat_card(self.stat_cards, "DROWSY ALERTS", "0", "#ff7788")

        tk.Label(left, text="LIVE STATUS", bg="#171c28", fg="#a8b2c7",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=22, pady=(10, 8))
        self.camera_label = self.status_line(left, "●", "Camera", "Camera idle")
        self.app_label = self.status_line(left, "▣", "Active app", "—")
        self.drowsy_label = self.status_line(left, "◉", "Alertness", "Not monitoring")
        self.focus_label = self.status_line(left, "◎", "Webcam focus", "Not monitoring")
        self.progress_label = self.status_line(left, "★", "Level / XP", "Level 1 · 0 XP")
        tk.Button(left, text="View study analytics", command=self.show_analytics, bg="#252c3c", fg="#e9edf7", activebackground="#30394d", relief="flat", bd=0, padx=14, pady=9, font=("Segoe UI", 9, "bold"), cursor="hand2").pack(anchor="w", padx=22, pady=(12, 4))

        tk.Label(right, text="STUDY SETTINGS", bg="#171c28", fg="#a8b2c7",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=20, pady=(22, 12))
        tk.Label(right, text="STUDY APPS (apps you plan to study in)", bg="#171c28", fg="#82dca5",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20)
        tk.Label(right, text="Enter one process name per line. Alerts are triggered by the separate distracting-app list.",
                 wraplength=260, justify="left", bg="#171c28", fg="#8995ad",
                 font=("Segoe UI", 8)).pack(anchor="w", padx=20, pady=(3, 4))
        self.allowed_text = tk.Text(right, height=7, bg="#101521", fg="#dce3f5", insertbackground="white",
                                    relief="flat", bd=0, font=("Consolas", 9), padx=10, pady=8)
        self.allowed_text.pack(fill="x", padx=20, pady=(7, 5))
        self.allowed_text.insert("1.0", "\n".join(self.allowed_apps))
        tk.Label(right, text="DISTRACTING APPS (warn / close on 2nd visit)", bg="#171c28", fg="#ffb86b",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(10, 0))
        self.blocked_text = tk.Text(right, height=5, bg="#101521", fg="#dce3f5", insertbackground="white",
                                    relief="flat", bd=0, font=("Consolas", 9), padx=10, pady=8)
        self.blocked_text.pack(fill="x", padx=20, pady=(7, 7))
        self.blocked_text.insert("1.0", "\n".join(self.blocked_apps))

        self.sound_var = tk.BooleanVar(value=True)
        self.popup_var = tk.BooleanVar(value=True)
        tk.Checkbutton(right, text="Play alert sound", variable=self.sound_var, bg="#171c28", fg="#e9edf7",
                       selectcolor="#252c3c", activebackground="#171c28", activeforeground="#e9edf7",
                       font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=2)
        tk.Checkbutton(right, text="Show Windows notification", variable=self.popup_var, bg="#171c28",
                       fg="#e9edf7", selectcolor="#252c3c", activebackground="#171c28",
                       activeforeground="#e9edf7", font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=2)
        tk.Checkbutton(right, text="Close listed app on 2nd distraction", variable=self.close_on_second,
                       bg="#171c28", fg="#ffb86b", selectcolor="#252c3c",
                       activebackground="#171c28", activeforeground="#ffb86b",
                       font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=2)
        tk.Label(right, text="Closing an app may lose unsaved work. Only enable for apps listed as distracting.",
                 wraplength=260, justify="left", bg="#171c28", fg="#7f8aa2",
                 font=("Segoe UI", 8)).pack(anchor="w", padx=20, pady=(2, 0))
        buttons = tk.Frame(right, bg="#171c28")
        buttons.pack(anchor="w", padx=20, pady=(12, 7))
        tk.Button(buttons, text="Save settings", command=self.save_settings, bg="#252c3c", fg="#e9edf7",
                  activebackground="#30394d", relief="flat", bd=0, padx=12, pady=9,
                  font=("Segoe UI", 9, "bold"), cursor="hand2").pack(side="left")
        tk.Button(buttons, text="Test sound", command=self.play_distraction_audio,
                  bg="#5b7cfa", fg="white", activebackground="#4566e5",
                  relief="flat", bd=0, padx=12, pady=9,
                  font=("Segoe UI", 9, "bold"), cursor="hand2").pack(side="left", padx=(8, 0))
        tk.Button(right, text="♫  Audio Manager", command=self.open_audio_manager, bg="#30394d", fg="#f4f7ff", activebackground="#3b4660", relief="flat", bd=0, padx=14, pady=10, font=("Segoe UI", 10, "bold"), cursor="hand2").pack(anchor="w", padx=20, pady=(5, 8))
        tk.Button(right, text="◉  JARVIS Voice Assistant", command=self.start_voice_assistant, bg="#173447", fg="#9fe8ff", activebackground="#20516a", relief="flat", bd=0, padx=14, pady=10, font=("Segoe UI", 10, "bold"), cursor="hand2").pack(anchor="w", padx=20, pady=(3, 8))

        note = ("Privacy: camera frames are processed locally and are not saved. "
                "Drowsiness detection is an estimate and may be wrong.")
        tk.Label(right, text=note, wraplength=260, justify="left", bg="#171c28", fg="#7f8aa2",
                 font=("Segoe UI", 8)).pack(anchor="w", padx=20, pady=(9, 20))

    def create_header(self):
        header = tk.Frame(self.root, bg="#10131b")
        header.pack(fill="x", padx=24, pady=(20, 8))
        tk.Label(header, text="STUDY / MONITOR", bg="#10131b", fg="#6f91ff",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(header, text="Stay on task.", bg="#10131b", fg="#f4f7ff",
                 font=("Segoe UI", 24, "bold")).pack(anchor="w", pady=(3, 0))
        self.date_label = tk.Label(header, text="", bg="#10131b", fg="#8995ad",
                                   font=("Segoe UI", 9))
        self.date_label.pack(anchor="w", pady=(3, 0))

    def stat_card(self, parent, title, value, accent):
        card = tk.Frame(parent, bg="#202635", padx=12, pady=12)
        card.pack(side="left", fill="both", expand=True, padx=4)
        tk.Label(card, text=title, bg="#202635", fg="#8995ad", font=("Segoe UI", 8, "bold")).pack(anchor="w")
        val = tk.Label(card, text=value, bg="#202635", fg=accent, font=("Segoe UI", 20, "bold"))
        val.pack(anchor="w", pady=(4, 0))
        return val

    def status_line(self, parent, symbol, title, value):
        row = tk.Frame(parent, bg="#171c28")
        row.pack(fill="x", padx=22, pady=5)
        tk.Label(row, text=symbol, bg="#171c28", fg="#6f91ff", font=("Segoe UI", 14)).pack(side="left")
        tk.Label(row, text=title, bg="#171c28", fg="#dce3f5", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(9, 8))
        val = tk.Label(row, text=value, bg="#171c28", fg="#8995ad", font=("Segoe UI", 9))
        val.pack(side="right")
        return val

    def load_config(self):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
            if "[ALLOWED]" in lines:
                i = lines.index("[ALLOWED]")
                j = lines.index("[BLOCKED]") if "[BLOCKED]" in lines else len(lines)
                self.allowed_apps = [x.strip().lower() for x in lines[i+1:j] if x.strip()]
                if "[BLOCKED]" in lines:
                    k = lines.index("[BLOCKED]")
                    self.blocked_apps = [x.strip().lower() for x in lines[k+1:] if x.strip()]
        except (OSError, ValueError):
            pass

    def save_settings(self):
        self.allowed_apps = [x.strip().lower() for x in self.allowed_text.get("1.0", "end").splitlines() if x.strip()]
        self.blocked_apps = [x.strip().lower() for x in self.blocked_text.get("1.0", "end").splitlines() if x.strip()]
        try:
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                f.write("[ALLOWED]\n" + "\n".join(self.allowed_apps) + "\n[BLOCKED]\n" + "\n".join(self.blocked_apps))
            messagebox.showinfo("Settings saved", "Your app lists have been saved.")
        except OSError as exc:
            messagebox.showerror("Could not save", str(exc))

    def notify(self, title, body, kind="distraction"):
        now = time.time()
        cooldown = 15 if kind == "drowsy" else (30 if kind == "away" else 10)
        if now - self.last_alert < cooldown and kind != "drowsy":
            return
        if kind == "drowsy":
            if now - self.last_drowsy_alert < 25:
                return
            self.last_drowsy_alert = now
            self.drowsy_count += 1
        else:
            self.last_alert = now
            if kind == "away":
                pass
            else:
                self.distraction_count += 1
            self.log_event(kind, body)
        if self.sound_var.get():
            if kind == "drowsy" and self.audio_assignments.get("Drowsiness alert"):
                self.play_audio_file(self.audio_assignments["Drowsiness alert"])
            else:
                try:
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                except Exception:
                    pass
        if self.popup_var.get():
            try:
                notification.notify(title=title, message=body, app_name=APP_NAME, timeout=5)
            except Exception:
                pass
        self.root.after(0, self.refresh_stats)

    def start_session(self):
        if self.running:
            return
        self.save_settings_silent()
        self.running = True
        self.session_started = time.time()
        self.last_focus_tick = time.time()
        self.log_event("session_start", "Study session started")
        self.play_assigned_event("Motivation")
        self.stop_event.clear()
        self.start_button.configure(state="disabled")
        self.pause_button.configure(state="normal")
        self.session_label.configure(text="Session active · monitoring enabled", fg="#82dca5")
        self.camera_thread = threading.Thread(target=self.camera_loop, daemon=True)
        self.camera_thread.start()
        self.root.after(800, self.check_active_app)

    def pause_session(self):
        if not self.running:
            return
        self.running = False
        self.elapsed_before_pause += time.time() - self.session_started if self.session_started else 0
        self.session_started = None
        self.stop_event.set()
        self.play_assigned_event("Break reminder")
        self.award_session_xp()
        self.log_event("session_pause", "Study session paused")
        self.start_button.configure(state="normal")
        self.pause_button.configure(state="disabled")
        self.session_label.configure(text="Session paused", fg="#ffb86b")
        self.camera_label.configure(text="Paused")
        self.drowsy_label.configure(text="Paused")
        self.camera_status = "Paused"
        self.drowsy_status = "Paused"

    def reset_session(self):
        was_active_or_used = self.elapsed_before_pause > 0 or self.session_started is not None
        self.pause_session()
        if was_active_or_used:
            self.play_assigned_event("Session complete")
        self.elapsed_before_pause = 0
        self.session_started = None
        self.distraction_count = 0
        self.drowsy_count = 0
        self.distraction_stat.configure(text="0")
        self.drowsy_stat.configure(text="0")
        self.timer_label.configure(text="00:00:00")
        self.focus_stat.configure(text="00:00")
        self.session_label.configure(text="Ready when you are", fg="#8995ad")
        self.current_app = "—"
        self.app_label.configure(text="—")

    def save_settings_silent(self):
        self.allowed_apps = [x.strip().lower() for x in self.allowed_text.get("1.0", "end").splitlines() if x.strip()]
        self.blocked_apps = [x.strip().lower() for x in self.blocked_text.get("1.0", "end").splitlines() if x.strip()]
        try:
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                f.write("[ALLOWED]\n" + "\n".join(self.allowed_apps) + "\n[BLOCKED]\n" + "\n".join(self.blocked_apps))
        except OSError:
            pass

    def load_audio_settings(self):
        try:
            os.makedirs(AUDIO_DIR, exist_ok=True)
            with open(AUDIO_CONFIG, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.audio_assignments.update(data.get("assignments", {}))
            self.audio_volume = max(0, min(100, int(data.get("volume", 100))))
        except (OSError, ValueError, TypeError):
            pass
        self.refresh_audio_files()

    def save_audio_settings(self):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(AUDIO_CONFIG, "w", encoding="utf-8") as f:
                json.dump({"assignments": self.audio_assignments, "volume": self.audio_volume}, f, indent=2)
        except OSError as exc:
            messagebox.showerror("Audio settings", str(exc))

    def ensure_default_audio(self):
        try:
            os.makedirs(AUDIO_DIR, exist_ok=True)
            # Seed the library with bundled meme clips; users can add/remove files in Audio Manager.
            for bundled_name in ("Padhai_Likhai_Karo_Ias_Bano_Meme_Video_Download_From_Indian_Meme_Template.mp3",
                                 "Tumse_Na_Ho_Payega_Meme_Video_Download.mp3",
                                 "Kyu_Nhi_Ho_Rhi_Padhai_Meme_Download(1).mp3",
                                 "wm_6537c8b9.mp3"):
                bundled = os.path.join(RESOURCE_DIR, bundled_name)
                target = os.path.join(AUDIO_DIR, bundled_name)
                if os.path.isfile(bundled) and not os.path.isfile(target):
                    import shutil
                    shutil.copy2(bundled, target)
            default_target = os.path.join(AUDIO_DIR, os.path.basename(DISTRACTION_AUDIO))
            if os.path.isfile(DISTRACTION_AUDIO) and not os.path.isfile(default_target):
                import shutil
                shutil.copy2(DISTRACTION_AUDIO, default_target)
            if not self.audio_assignments.get("Distraction warning") and os.path.isfile(default_target):
                self.audio_assignments["Distraction warning"] = default_target
            self.refresh_audio_files()
            self.save_audio_settings()
        except OSError:
            pass

    def refresh_audio_files(self):
        try:
            os.makedirs(AUDIO_DIR, exist_ok=True)
            self.audio_files = {name: os.path.join(AUDIO_DIR, name) for name in os.listdir(AUDIO_DIR)
                                if name.lower().endswith((".mp3", ".wav", ".ogg", ".flac"))
                                and os.path.isfile(os.path.join(AUDIO_DIR, name))}
        except OSError:
            self.audio_files = {}

    def open_audio_manager(self):
        win = tk.Toplevel(self.root)
        win.title("Study Monitor · Audio Manager")
        win.geometry("650x510")
        win.minsize(580, 460)
        win.configure(bg="#10131b")
        tk.Label(win, text="CUSTOM AUDIO MANAGER", bg="#10131b", fg="#6f91ff", font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=20, pady=(18, 4))
        tk.Label(win, text="Add MP3/WAV/OGG/FLAC files once. They stay in your local AppData audio folder and do not require rebuilding the EXE.", wraplength=600, justify="left", bg="#10131b", fg="#8995ad", font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=(0, 12))
        body = tk.Frame(win, bg="#10131b")
        body.pack(fill="both", expand=True, padx=20)
        left = tk.Frame(body, bg="#171c28")
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        tk.Label(left, text="AUDIO LIBRARY", bg="#171c28", fg="#dce3f5", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        listing = tk.Listbox(left, bg="#101521", fg="#dce3f5", selectbackground="#5b7cfa", relief="flat", font=("Consolas", 9))
        listing.pack(fill="both", expand=True, padx=10, pady=5)
        def repopulate(select_name=None):
            self.refresh_audio_files(); listing.delete(0, "end")
            names = sorted(self.audio_files)
            for name in names: listing.insert("end", name)
            if select_name in names:
                idx = names.index(select_name); listing.selection_set(idx); listing.activate(idx)
        def selected_path():
            sel = listing.curselection()
            return os.path.join(AUDIO_DIR, listing.get(sel[0])) if sel else None
        def add_files():
            paths = filedialog.askopenfilenames(parent=win, title="Choose audio files", filetypes=[("Audio files", "*.mp3 *.wav *.ogg *.flac"), ("All files", "*.*")])
            if not paths: return
            import shutil
            last = None
            for src in paths:
                if not src.lower().endswith((".mp3", ".wav", ".ogg", ".flac")):
                    continue
                dst = os.path.join(AUDIO_DIR, os.path.basename(src))
                try:
                    if os.path.abspath(src) != os.path.abspath(dst): shutil.copy2(src, dst)
                    last = os.path.basename(dst)
                except OSError as exc: messagebox.showerror("Could not add audio", str(exc), parent=win)
            repopulate(last)
        def play_selected():
            path = selected_path()
            if path: self.play_audio_file(path)
            else: messagebox.showinfo("Select audio", "Choose an audio file first.", parent=win)
        def remove_selected():
            path = selected_path()
            if not path: return
            name = os.path.basename(path)
            if not messagebox.askyesno("Remove audio", f"Remove {name} from the audio library?", parent=win): return
            try:
                os.remove(path)
                for event, assigned in list(self.audio_assignments.items()):
                    if assigned == path: self.audio_assignments[event] = ""
                self.save_audio_settings(); repopulate()
            except OSError as exc: messagebox.showerror("Could not remove", str(exc), parent=win)
        lb = tk.Frame(left, bg="#171c28"); lb.pack(fill="x", padx=10, pady=(3, 10))
        tk.Button(lb, text="＋ Add audio", command=add_files, bg="#5b7cfa", fg="white", relief="flat", padx=9, pady=7).pack(side="left")
        tk.Button(lb, text="▶ Test", command=play_selected, bg="#30394d", fg="white", relief="flat", padx=9, pady=7).pack(side="left", padx=5)
        tk.Button(lb, text="Remove", command=remove_selected, bg="#30394d", fg="white", relief="flat", padx=9, pady=7).pack(side="left")
        right = tk.Frame(body, bg="#171c28", width=240); right.pack(side="right", fill="y"); right.pack_propagate(False)
        tk.Label(right, text="EVENT ASSIGNMENT", bg="#171c28", fg="#dce3f5", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=12, pady=(12, 8))
        event_var = tk.StringVar(value="Distraction warning")
        ttk.Combobox(right, textvariable=event_var, values=list(self.audio_assignments), state="readonly").pack(fill="x", padx=12, pady=4)
        assigned_var = tk.StringVar()
        audio_choice = ttk.Combobox(right, textvariable=assigned_var, state="readonly")
        audio_choice.pack(fill="x", padx=12, pady=4)
        def sync_choice(*_):
            audio_choice["values"] = ["(No sound)"] + sorted(self.audio_files)
            current = self.audio_assignments.get(event_var.get(), "")
            assigned_var.set(os.path.basename(current) if current and os.path.isfile(current) else "(No sound)")
        event_var.trace_add("write", sync_choice)
        sync_choice()
        def assign_audio():
            val = assigned_var.get()
            self.audio_assignments[event_var.get()] = "" if val == "(No sound)" else os.path.join(AUDIO_DIR, val)
            self.save_audio_settings()
            messagebox.showinfo("Saved", f"Sound assigned to {event_var.get()}.", parent=win)
        tk.Button(right, text="Save assignment", command=assign_audio, bg="#5b7cfa", fg="white", relief="flat", padx=10, pady=8).pack(fill="x", padx=12, pady=(7, 15))
        tk.Label(right, text="Playback volume", bg="#171c28", fg="#dce3f5", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=12)
        vol_var = tk.IntVar(value=self.audio_volume)
        vol_label = tk.Label(right, text=f"{self.audio_volume}%", bg="#171c28", fg="#8995ad")
        vol_label.pack(anchor="w", padx=12, pady=(2, 0))
        def change_volume(v):
            self.audio_volume = int(float(v)); vol_label.configure(text=f"{self.audio_volume}%")
        tk.Scale(right, from_=0, to=100, orient="horizontal", variable=vol_var, command=change_volume, bg="#171c28", fg="#dce3f5", troughcolor="#30394d", highlightthickness=0).pack(fill="x", padx=8)
        tk.Button(right, text="Save volume", command=lambda: self.save_audio_settings(), bg="#30394d", fg="white", relief="flat", padx=10, pady=8).pack(fill="x", padx=12, pady=8)
        tk.Label(right, text="Tip: audio is stored in %APPDATA%\\StudyMonitor\\audio", wraplength=210, justify="left", bg="#171c28", fg="#8995ad", font=("Segoe UI", 8)).pack(anchor="w", padx=12, pady=(8, 4))
        repopulate()

    def play_assigned_event(self, event_name):
        """Play the sound assigned to an app event, if one is configured."""
        path = self.audio_assignments.get(event_name, "")
        if path and os.path.isfile(path):
            self.play_audio_file(path)

    def play_audio_file(self, path):
        """Play a local audio file using pygame; show a useful error if decoding fails."""
        def worker():
            try:
                if not os.path.isfile(path):
                    raise FileNotFoundError(path)
                if not pygame.mixer.get_init():
                    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
                pygame.mixer.music.stop()
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(max(0, min(100, int(self.audio_volume))) / 100.0)
                pygame.mixer.music.play()
            except Exception as exc:
                message = str(exc)
                self.root.after(0, lambda msg=message: messagebox.showerror(
                    "Could not play audio",
                    "This audio file could not be decoded. Remove it from Audio Manager or convert it to a standard MP3/WAV.\n\n" + msg))
        threading.Thread(target=worker, daemon=True).start()

    def speak_alert_after_audio(self, phrase="Please study, sir. Wapas padhai par aaiye."):
        """Speak the alert after the meme clip finishes, using an installed Windows voice."""
        def worker():
            try:
                deadline = time.time() + 18
                while time.time() < deadline:
                    if not pygame.mixer.get_init() or not pygame.mixer.music.get_busy():
                        break
                    time.sleep(0.2)
                import pyttsx3
                engine = pyttsx3.init()
                voices = engine.getProperty("voices")
                # Prefer a soft/female voice if Windows has one installed.
                for voice in voices:
                    desc = (str(getattr(voice, "name", "")) + " " + str(getattr(voice, "id", ""))).lower()
                    if any(k in desc for k in ("zira", "female", "heera", "priya")):
                        engine.setProperty("voice", voice.id)
                        break
                engine.setProperty("rate", 160)
                engine.setProperty("volume", max(0.2, min(1.0, self.audio_volume / 100.0)))
                engine.say(phrase)
                engine.runAndWait()
                engine.stop()
            except Exception:
                # Meme playback must continue to work even if Windows TTS is unavailable.
                pass
        threading.Thread(target=worker, daemon=True).start()

    def play_distraction_audio(self):
        # Alternate the bundled meme clips on each alert. The previously supplied
        # Kyu Nhi file was an AAC/MP4 stream mislabeled .mp3; it is now re-encoded.
        preferred = [
            "Padhai_Likhai_Karo_Ias_Bano_Meme_Video_Download_From_Indian_Meme_Template.mp3",
            "Tumse_Na_Ho_Payega_Meme_Video_Download.mp3",
            "Kyu_Nhi_Ho_Rhi_Padhai_Meme_Download.mp3",
            "wm_6537c8b9.mp3",
        ]
        candidates = []
        for name in preferred:
            path = os.path.join(AUDIO_DIR, name)
            if os.path.isfile(path):
                candidates.append(path)
        # Keep any other user-added audio available after the four known meme clips.
        for name, path in sorted(self.audio_files.items()):
            if path not in candidates and os.path.isfile(path):
                candidates.append(path)
        assigned = self.audio_assignments.get("Distraction warning", "")
        if assigned and os.path.isfile(assigned):
            candidates = [assigned] + [p for p in candidates if os.path.abspath(p) != os.path.abspath(assigned)]
        if not candidates and os.path.isfile(DISTRACTION_AUDIO):
            candidates = [DISTRACTION_AUDIO]
        if candidates:
            path = candidates[self._alert_audio_index % len(candidates)]
            self._alert_audio_index += 1
            self.play_audio_file(path)
            self.speak_alert_after_audio()
        else:
            self.root.after(0, lambda: messagebox.showwarning(
                "No audio found", "Open Audio Manager and add an MP3/WAV file first."))
        self.show_fullscreen_alert("PLEASE STUDY, SIR!", "Distraction detected. Back to your study.")

    def show_fullscreen_alert(self, headline="PLEASE STUDY, SIR!", detail="Stay focused."):
        # Full-screen topmost reminder; Esc or the button dismisses it.
        def show():
            try:
                if self._alert_overlay and self._alert_overlay.winfo_exists():
                    self._alert_overlay.destroy()
                win = tk.Toplevel(self.root)
                self._alert_overlay = win
                win.configure(bg="#070b16")
                win.attributes("-fullscreen", True)
                win.attributes("-topmost", True)
                win.focus_force()
                win.bind("<Escape>", lambda _e: win.destroy())
                tk.Label(win, text="S T U D Y   G U A R D I A N", bg="#070b16", fg="#68dcff",
                         font=("Segoe UI", 18, "bold")).pack(pady=(100, 25))
                tk.Label(win, text="⚠", bg="#070b16", fg="#ff4d6d",
                         font=("Segoe UI", 76, "bold")).pack()
                tk.Label(win, text=headline, bg="#070b16", fg="#ffffff",
                         font=("Segoe UI", 38, "bold")).pack(pady=18)
                tk.Label(win, text=detail, bg="#070b16", fg="#aebbd3",
                         font=("Segoe UI", 19)).pack(pady=8)
                tk.Button(win, text="I'M BACK TO STUDY  ·  DISMISS", command=win.destroy,
                          bg="#2374ff", fg="white", activebackground="#1457cc",
                          relief="flat", padx=28, pady=14, font=("Segoe UI", 13, "bold")).pack(pady=35)
            except Exception:
                pass
        self.root.after(0, show)

    def start_voice_assistant(self):
        if self._voice_listening:
            messagebox.showinfo("JARVIS", "Already listening. Please wait for the current command.")
            return
        self._voice_listening = True
        self.notify("JARVIS", "Listening for one Hindi/English command. Internet may be required for speech recognition.")
        threading.Thread(target=self._voice_command_worker, daemon=True).start()

    def _voice_command_worker(self):
        try:
            import speech_recognition as sr
            import pyttsx3
            import pyautogui
            import pyperclip
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                self.root.after(0, lambda: self.session_label.configure(text="JARVIS listening…", fg="#68dcff"))
                audio = recognizer.listen(source, timeout=6, phrase_time_limit=8)
            spoken = ""
            for lang in ("hi-IN", "en-IN"):
                try:
                    spoken = recognizer.recognize_google(audio, language=lang)
                    if spoken: break
                except Exception:
                    continue
            if not spoken:
                raise RuntimeError("Could not recognize speech. Try again in a quieter room.")
            lower = spoken.lower()
            engine = pyttsx3.init()
            # Prefer an installed female voice; voice availability depends on Windows.
            for voice in engine.getProperty("voices"):
                desc = (voice.name + " " + voice.id).lower()
                if any(k in desc for k in ("zira", "female", "heera", "priya")):
                    engine.setProperty("voice", voice.id); break
            engine.setProperty("rate", 168)
            self.root.after(0, lambda text=spoken: self.show_voice_reply("You said: " + text))
            if any(k in lower for k in ("whatsapp", "व्हाट्सएप")) and any(k in lower for k in ("open", "khol", "खोल")):
                os.startfile("whatsapp:")
                # If user says "WhatsApp khol [name]", wait briefly then search chat by name.
                chat_match = re.search(r"(?:whatsapp|व्हाट्सएप)\s+(?:khol|open|खोल)\s+(.+)", spoken, flags=re.I)
                if chat_match:
                    chat_name = chat_match.group(1).strip()
                    time.sleep(2.5)
                    pyautogui.hotkey("ctrl", "f")
                    time.sleep(0.4)
                    pyperclip.copy(chat_name)
                    pyautogui.hotkey("ctrl", "v")
                    time.sleep(1.0)
                    pyautogui.press("enter")
                    reply = chat_name + " chat search karne ki koshish ki hai. Verify kar lena."
                else:
                    reply = "WhatsApp khol rahi hoon. Chat ka naam bol sakti hain."
                engine.say(reply); engine.runAndWait()
            elif any(k in lower for k in ("type", "likh", "लिख", "टाइप")):
                # Dictation into the currently focused text field; never send automatically.
                text = re.sub(r"^(please\s+)?(type|write|likh|लिख|टाइप)\s*", "", spoken, flags=re.I).strip()
                if text:
                    pyperclip.copy(text)
                    pyautogui.hotkey("ctrl", "v")
                    reply = "Text type kar diya hai. Send karne se pehle check kar lena."
                    engine.say(reply); engine.runAndWait()
                else:
                    reply = "Please boliye kya type karna hai."
                    engine.say(reply); engine.runAndWait()
            elif any(k in lower for k in ("start session", "study start", "padhai shuru", "पढ़ाई शुरू")):
                self.root.after(0, self.start_session)
                engine.say("Study session shuru kar rahi hoon."); engine.runAndWait()
            elif any(k in lower for k in ("pause", "रुको", "pause session")):
                self.root.after(0, self.pause_session)
                engine.say("Session pause kar diya."); engine.runAndWait()
            else:
                engine.say("Maine suna: " + spoken + ". Abhi is command ka action configured nahi hai.")
                engine.runAndWait()
        except Exception as exc:
            self.root.after(0, lambda msg=str(exc): messagebox.showerror("JARVIS Voice Assistant", "Voice assistant needs a microphone and the optional voice packages. Speech recognition may need internet.\\n\\n" + msg))
        finally:
            self._voice_listening = False

    def show_voice_reply(self, text):
        self.show_fullscreen_alert("JARVIS", text)

    def close_distracting_app(self, process_name):
        # Only close an exact executable name from the user's explicit list.
        closed_any = False
        for proc in psutil.process_iter(["name"]):
            try:
                if (proc.info.get("name") or "").lower() == process_name.lower():
                    proc.terminate()
                    closed_any = True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        if closed_any:
            self.notify("Distraction stopped", f"Closed {process_name} after the second distraction.")
        else:
            self.notify("Could not close app", f"Windows did not allow Study Monitor to close {process_name}.")

    def check_active_app(self):
        if not self.running:
            return
        try:
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            proc = psutil.Process(pid)
            name = proc.name().lower()
            self.current_app = name
            self.app_label.configure(text=name[:23])
            # Count only when switching into a listed distracting app.
            entered_blocked_app = name in self.blocked_apps and name != self.last_foreground_name
            if entered_blocked_app:
                hits = self.distraction_hits.get(name, 0) + 1
                self.distraction_hits[name] = hits
                if hits == 1:
                    self.notify("Back to your study!", f"{name} detected. Return to your study.")
                    self.log_event("distraction_first", name)
                    self.play_distraction_audio()
                elif hits >= 2:
                    self.log_event("distraction_repeat", name)
                    if self.close_on_second.get():
                        self.play_distraction_audio()
                        self.close_distracting_app(name)
                    else:
                        self.notify("Second distraction", f"{name} detected again. Return to your study.")
                        self.play_distraction_audio()
                self.last_distraction_key = name
            elif name not in self.blocked_apps:
                self.last_distraction_key = None
            self.last_foreground_name = name
        except Exception:
            pass
        self.root.after(1800, self.check_active_app)

    def camera_loop(self):
        self.root.after(0, lambda: self.camera_label.configure(text="Starting…"))
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap.release()
            self.camera_status = "Camera unavailable"
            self.root.after(0, lambda: self.camera_label.configure(text="Unavailable"))
            self.root.after(0, lambda: self.drowsy_label.configure(text="Camera unavailable"))
            return
        self.camera_status = "Monitoring"
        mp_face = mp.solutions.face_mesh
        try:
            with mp_face.FaceMesh(max_num_faces=1, refine_landmarks=True,
                                  min_detection_confidence=0.5,
                                  min_tracking_confidence=0.5) as mesh:
                while not self.stop_event.is_set():
                    ok, frame = cap.read()
                    if not ok:
                        time.sleep(0.2)
                        continue
                    frame = cv2.flip(frame, 1)
                    h, w = frame.shape[:2]
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    result = mesh.process(rgb)
                    now = time.time()
                    eyes_closed = False
                    head_drooping = False
                    if result.multi_face_landmarks:
                        lm = result.multi_face_landmarks[0].landmark
                        left = eye_aspect_ratio(lm, LEFT_EYE, w, h)
                        right = eye_aspect_ratio(lm, RIGHT_EYE, w, h)
                        eyes_closed = ((left + right) / 2) < 0.19
                        # Approximate head direction from nose position relative to eye corners.
                        eye_mid_x = (lm[33].x + lm[263].x) / 2.0
                        eye_span = max(abs(lm[263].x - lm[33].x), 0.001)
                        nose_offset = (lm[1].x - eye_mid_x) / eye_span
                        looking_away = abs(nose_offset) > 0.22
                        if looking_away:
                            if self.away_since is None:
                                self.away_since = now
                            if now - self.away_since > 8:
                                self.root.after(0, lambda: self.focus_label.configure(text="Looking away"))
                                self.notify("Stay with your study", "Your head appears turned away for a while.", "away")
                        else:
                            self.away_since = None
                            self.root.after(0, lambda: self.focus_label.configure(text="Face toward screen"))
                        # Nose landmark moving down is only a rough head-droop signal.
                        nose_y = lm[1].y
                        if self.last_head_y is not None and nose_y - self.last_head_y > 0.035:
                            self.head_drop_since = now
                        self.last_head_y = nose_y
                        head_drooping = self.head_drop_since is not None and now - self.head_drop_since > 1.8
                        if not head_drooping:
                            self.head_drop_since = None
                        self.root.after(0, lambda: self.drowsy_label.configure(text="Face detected"))
                    else:
                        self.last_head_y = None
                        self.head_drop_since = None
                        if self.away_since is None:
                            self.away_since = now
                        if now - self.away_since > 8:
                            self.root.after(0, lambda: self.focus_label.configure(text="Face not detected"))
                            self.notify("Face not detected", "Sit in view of the webcam to track focus.", "away")
                        self.root.after(0, lambda: self.drowsy_label.configure(text="Face not detected"))
                    if eyes_closed:
                        if self.closed_eye_since is None:
                            self.closed_eye_since = now
                        if now - self.closed_eye_since > 1.8:
                            self.notify("Drowsiness detected?", "Your eyes appear closed. Sit up, blink, and take a short break.", "drowsy")
                            self.closed_eye_since = now
                    else:
                        self.closed_eye_since = None
                    if head_drooping:
                        self.notify("Check your alertness", "Your head movement may indicate tiredness. Take a short break.", "drowsy")
                    time.sleep(0.04)
        except Exception as exc:
            self.camera_status = "Camera error"
            self.root.after(0, lambda: self.camera_label.configure(text="Camera error"))
        finally:
            cap.release()
            self.camera_status = "Camera idle"
            self.root.after(0, lambda: self.camera_label.configure(text="Camera idle" if not self.running else "Stopped"))

    def refresh_stats(self):
        self.distraction_stat.configure(text=str(self.distraction_count))
        self.drowsy_stat.configure(text=str(self.drowsy_count))
        self.refresh_progress_label()

    def update_clock(self):
        elapsed = self.elapsed_before_pause
        if self.running and self.session_started:
            elapsed += time.time() - self.session_started
        elapsed = int(elapsed)
        hh, rem = divmod(elapsed, 3600)
        mm, ss = divmod(rem, 60)
        self.timer_label.configure(text=f"{hh:02d}:{mm:02d}:{ss:02d}")
        if self.running and time.time() - self.last_focus_tick >= 60:
            gained = int((time.time() - self.last_focus_tick) // 60)
            self.focus_seconds += gained * 60
            self.xp += gained * 5
            self.last_focus_tick = time.time()
            self.update_streak()
            self.save_stats()
            self.refresh_progress_label()
        self.focus_stat.configure(text=f"{hh:02d}:{mm:02d}")
        self.date_label.configure(text=datetime.now().strftime("%A, %d %B %Y  ·  %I:%M %p"))
        self.root.after(500, self.update_clock)

    def load_stats(self):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.xp = int(data.get("xp", 0))
            self.level = max(1, self.xp // 250 + 1)
            self.daily_streak = int(data.get("daily_streak", 0))
            self.last_study_date = data.get("last_study_date", "")
        except (OSError, ValueError, TypeError):
            pass

    def save_stats(self):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(STATS_FILE, "w", encoding="utf-8") as f:
                json.dump({"xp": self.xp, "daily_streak": self.daily_streak,
                           "last_study_date": self.last_study_date}, f, indent=2)
        except OSError:
            pass

    def update_streak(self):
        today = datetime.now().strftime("%Y-%m-%d")
        if self.last_study_date != today:
            from datetime import date, timedelta
            yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
            self.daily_streak = self.daily_streak + 1 if self.last_study_date == yesterday else 1
            self.last_study_date = today

    def refresh_progress_label(self):
        self.level = max(1, self.xp // 250 + 1)
        if hasattr(self, "progress_label"):
            self.progress_label.configure(text=f"Level {self.level} · {self.xp} XP · {self.daily_streak}-day streak")

    def award_session_xp(self):
        minutes = int(self.elapsed_before_pause // 60)
        if self.session_started:
            minutes += int((time.time() - self.session_started) // 60)
        # XP is also earned incrementally by the session clock; don't double-award.
        self.save_stats()
        self.refresh_progress_label()

    def log_event(self, event, detail):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            new_file = not os.path.exists(EVENTS_FILE)
            with open(EVENTS_FILE, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if new_file:
                    writer.writerow(["timestamp", "event", "detail"])
                writer.writerow([datetime.now().isoformat(timespec="seconds"), event, detail])
        except OSError:
            pass

    def show_analytics(self):
        try:
            rows = []
            if os.path.exists(EVENTS_FILE):
                with open(EVENTS_FILE, "r", newline="", encoding="utf-8") as f:
                    rows = list(csv.DictReader(f))
            today = datetime.now().strftime("%Y-%m-%d")
            today_rows = [r for r in rows if (r.get("timestamp", "").startswith(today))]
            recent = rows[-12:]
            lines = [f"Total recorded events: {len(rows)}", f"Events today: {len(today_rows)}",
                     f"Lifetime XP: {self.xp}", f"Level: {self.level}", f"Daily streak: {self.daily_streak}", "",
                     "Recent activity:"]
            lines.extend([f"{r.get('timestamp','')}  |  {r.get('event','')}  |  {r.get('detail','')}" for r in recent] or ["No events logged yet."])
            win = tk.Toplevel(self.root)
            win.title("Study analytics")
            win.geometry("700x480")
            win.configure(bg="#10131b")
            tk.Label(win, text="STUDY ANALYTICS", bg="#10131b", fg="#6f91ff", font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=18, pady=(16, 8))
            chart = tk.Canvas(win, height=115, bg="#171c28", highlightthickness=0)
            chart.pack(fill="x", padx=18, pady=(0, 8))
            from datetime import date, timedelta
            days = [(date.today() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
            counts = [sum(1 for r in rows if r.get("timestamp", "").startswith(day) and r.get("event") in ("session_start", "session_pause", "distraction_first", "distraction_repeat")) for day in days]
            max_count = max(counts + [1])
            cw = 650 / 7
            for i, (day, count) in enumerate(zip(days, counts)):
                x0 = 12 + i * cw
                bar_h = 65 * count / max_count
                chart.create_rectangle(x0 + 10, 78 - bar_h, x0 + 44, 78, fill="#5b7cfa", outline="")
                chart.create_text(x0 + 27, 88, text=day[5:], fill="#8995ad", font=("Segoe UI", 8))
                chart.create_text(x0 + 27, 70 - bar_h, text=str(count), fill="#dce3f5", font=("Segoe UI", 8))
            tk.Label(win, text="Weekly activity chart · recorded study/distraction events", bg="#10131b", fg="#8995ad", font=("Segoe UI", 8)).pack(anchor="w", padx=20, pady=(0, 4))
            txt = tk.Text(win, bg="#171c28", fg="#dce3f5", insertbackground="white", relief="flat", font=("Consolas", 10), wrap="none")
            txt.pack(fill="both", expand=True, padx=18, pady=(0, 18))
            txt.insert("1.0", "\n".join(lines))
            txt.configure(state="disabled")
        except Exception as exc:
            messagebox.showerror("Analytics unavailable", str(exc))

    def on_close(self):
        self.running = False
        self.stop_event.set()
        self.save_stats()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = StudyMonitor(root)
    root.mainloop()

if __name__ == "__main__":
    main()
