"""
JARVIS Siri/Gemini-Style Floating HUD Overlay
A sleek, modern, dark-themed floating overlay widget with real-time audio visualizer,
subtitles, microphone toggle, and permanent hangup / power-off controls.
"""

import sys
import math
import time
import queue
import threading
import tkinter as tk
from typing import Optional, Callable

# State constants
STATE_IDLE = "idle"
STATE_LISTENING = "listening"
STATE_THINKING = "thinking"
STATE_SPEAKING = "speaking"
STATE_OFFLINE = "offline"

class JarvisOverlayUI:
    def __init__(
        self,
        on_mic_click: Optional[Callable[[], None]] = None,
        on_hangup_click: Optional[Callable[[], None]] = None,
        on_stop_click: Optional[Callable[[], None]] = None,
    ):
        self.on_mic_click = on_mic_click
        self.on_hangup_click = on_hangup_click
        self.on_stop_click = on_stop_click

        self.event_queue = queue.Queue()
        self.state = STATE_IDLE
        self.status_text = "Ready"
        self.subtitle_text = "Say 'Hey Jarvis' or click mic to start"
        self.is_running = True
        self.is_hidden = False
        self.anim_frame = 0
        self.root = None
        self._thread = None
        self._drag_start_x = 0
        self._drag_start_y = 0

    def start(self):
        """Starts the UI in a dedicated GUI thread."""
        self._thread = threading.Thread(target=self._run_tk, daemon=True)
        self._thread.start()

    def _run_tk(self):
        self.root = tk.Tk()
        self.root.title("JARVIS AI")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        
        # Color Palette - Sleek Dark Theme
        self.BG_MAIN = "#12141a"
        self.BG_CARD = "#191d26"
        self.BORDER_COLOR = "#2a3142"
        self.ACCENT_CYAN = "#00e5ff"
        self.ACCENT_BLUE = "#3b82f6"
        self.ACCENT_PURPLE = "#a855f7"
        self.ACCENT_RED = "#ef4444"
        self.TEXT_PRIMARY = "#f8fafc"
        self.TEXT_SECONDARY = "#94a3b8"
        self.TEXT_MUTED = "#64748b"

        # Window dimensions & positioning (Bottom-Right of screen)
        width = 330
        height = 420
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        pos_x = screen_width - width - 35
        pos_y = screen_height - height - 70

        self.root.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
        self.root.configure(bg=self.BG_MAIN)

        # Build Main Canvas with rounded border
        self.canvas_bg = tk.Canvas(
            self.root,
            width=width,
            height=height,
            bg=self.BG_MAIN,
            highlightthickness=0
        )
        self.canvas_bg.pack(fill="both", expand=True)

        # Draw card container
        self._draw_rounded_rect(
            self.canvas_bg, 4, 4, width - 4, height - 4,
            radius=24,
            fill=self.BG_CARD,
            outline=self.BORDER_COLOR,
            width=2
        )

        # Top Header Bar (Draggable)
        self.header_frame = tk.Frame(self.root, bg=self.BG_CARD)
        self.header_frame.place(x=16, y=14, width=width - 32, height=36)
        
        # Header Drag Bindings
        self.header_frame.bind("<ButtonPress-1>", self._on_drag_start)
        self.header_frame.bind("<B1-Motion>", self._on_drag_motion)
        
        # Logo / Glow indicator
        self.logo_canvas = tk.Canvas(self.header_frame, width=22, height=22, bg=self.BG_CARD, highlightthickness=0)
        self.logo_canvas.pack(side="left", padx=(0, 6))
        self.logo_dot = self.logo_canvas.create_oval(3, 3, 19, 19, fill=self.ACCENT_CYAN, outline="")
        self.logo_canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self.logo_canvas.bind("<B1-Motion>", self._on_drag_motion)

        # Title Label
        self.title_lbl = tk.Label(
            self.header_frame,
            text="JARVIS AI",
            font=("Segoe UI", 11, "bold"),
            fg=self.TEXT_PRIMARY,
            bg=self.BG_CARD
        )
        self.title_lbl.pack(side="left", padx=2)
        self.title_lbl.bind("<ButtonPress-1>", self._on_drag_start)
        self.title_lbl.bind("<B1-Motion>", self._on_drag_motion)

        # Language / Mode pill
        self.lang_badge = tk.Label(
            self.header_frame,
            text="ONLINE",
            font=("Segoe UI", 8, "bold"),
            fg=self.ACCENT_CYAN,
            bg="#0f2b38",
            padx=6,
            pady=1
        )
        self.lang_badge.pack(side="left", padx=6)

        # Close / Minimize buttons
        self.btn_minimize = tk.Button(
            self.header_frame,
            text="─",
            font=("Segoe UI", 9, "bold"),
            fg=self.TEXT_SECONDARY,
            bg=self.BG_CARD,
            activeforeground=self.TEXT_PRIMARY,
            activebackground=self.BORDER_COLOR,
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self.toggle_hide
        )
        self.btn_minimize.pack(side="right", padx=2)

        # Center Visualizer Orb Canvas
        self.orb_size = 140
        self.orb_canvas = tk.Canvas(
            self.root,
            width=self.orb_size,
            height=self.orb_size,
            bg=self.BG_CARD,
            highlightthickness=0
        )
        self.orb_canvas.place(x=(width - self.orb_size) // 2, y=60)
        self.orb_canvas.bind("<ButtonPress-1>", self._on_orb_click)

        # Status Label (e.g. "Listening...", "Speaking...")
        self.lbl_status = tk.Label(
            self.root,
            text=self.status_text,
            font=("Segoe UI", 12, "bold"),
            fg=self.ACCENT_CYAN,
            bg=self.BG_CARD
        )
        self.lbl_status.place(x=16, y=205, width=width - 32)

        # Subtitle / Response text box
        self.lbl_subtitle = tk.Label(
            self.root,
            text=self.subtitle_text,
            font=("Segoe UI", 9),
            fg=self.TEXT_SECONDARY,
            bg=self.BG_CARD,
            wraplength=width - 40,
            justify="center",
            height=3
        )
        self.lbl_subtitle.place(x=20, y=232, width=width - 40)

        # Action Control Panel (Bottom)
        self.controls_frame = tk.Frame(self.root, bg=self.BG_CARD)
        self.controls_frame.place(x=20, y=305, width=width - 40, height=85)

        # 1. Stop / Interrupt Button
        self.btn_stop = tk.Button(
            self.controls_frame,
            text="⏸",
            font=("Segoe UI", 13),
            fg=self.TEXT_PRIMARY,
            bg="#262b38",
            activeforeground="#ffffff",
            activebackground="#374151",
            relief="flat",
            bd=0,
            width=4,
            height=2,
            cursor="hand2",
            command=self._handle_stop_click
        )
        self.btn_stop.pack(side="left", padx=10, pady=8)

        # 2. Main Microphone Button (Large Pulsing Action)
        self.btn_mic = tk.Button(
            self.controls_frame,
            text="🎙️",
            font=("Segoe UI", 16, "bold"),
            fg="#ffffff",
            bg=self.ACCENT_BLUE,
            activeforeground="#ffffff",
            activebackground=self.ACCENT_CYAN,
            relief="flat",
            bd=0,
            width=4,
            height=2,
            cursor="hand2",
            command=self._handle_mic_click
        )
        self.btn_mic.pack(side="left", padx=12, pady=4)

        # 3. Hangup / Power Off Button (Red - Permanent Shutdown)
        self.btn_hangup = tk.Button(
            self.controls_frame,
            text="📞",
            font=("Segoe UI", 15, "bold"),
            fg="#ffffff",
            bg=self.ACCENT_RED,
            activeforeground="#ffffff",
            activebackground="#b91c1c",
            relief="flat",
            bd=0,
            width=4,
            height=2,
            cursor="hand2",
            command=self._handle_hangup_click
        )
        self.btn_hangup.pack(side="right", padx=10, pady=8)

        # Sub-labels for controls
        self.ctrl_labels = tk.Label(
            self.root,
            text="Stop            Talk            Hangup",
            font=("Segoe UI", 7, "bold"),
            fg=self.TEXT_MUTED,
            bg=self.BG_CARD
        )
        self.ctrl_labels.place(x=20, y=390, width=width - 40)

        # Start periodic tick for animations and event queue processing
        self._periodic_tick()
        self.root.mainloop()

    def _draw_rounded_rect(self, canvas, x1, y1, x2, y2, radius=25, **kwargs):
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1
        ]
        return canvas.create_polygon(points, **kwargs, smooth=True)

    def _on_drag_start(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _on_drag_motion(self, event):
        x = self.root.winfo_x() + (event.x - self._drag_start_x)
        y = self.root.winfo_y() + (event.y - self._drag_start_y)
        self.root.geometry(f"+{x}+{y}")

    def _on_orb_click(self, event):
        self._handle_mic_click()

    def _handle_mic_click(self):
        if self.on_mic_click:
            threading.Thread(target=self.on_mic_click, daemon=True).start()

    def _handle_stop_click(self):
        if self.on_stop_click:
            threading.Thread(target=self.on_stop_click, daemon=True).start()
        else:
            self.set_state(STATE_IDLE, "Stopped", "Playback paused")

    def _handle_hangup_click(self):
        self.set_state(STATE_OFFLINE, "Shutting Down...", "Permanent offline command initiated")
        if self.on_hangup_click:
            threading.Thread(target=self.on_hangup_click, daemon=True).start()

    def toggle_hide(self):
        """Minimizes/Hides or Restores overlay."""
        if not self.root:
            return
        if self.is_hidden:
            self.root.deiconify()
            self.is_hidden = False
            self.btn_minimize.configure(text="─")
        else:
            self.root.withdraw()
            self.is_hidden = True

    def show(self):
        """Ensures the window is visible and on top."""
        if self.root:
            try:
                self.root.deiconify()
                self.root.attributes("-topmost", True)
                self.is_hidden = False
            except Exception:
                pass

    def hide(self):
        """Hides the window."""
        if self.root:
            try:
                self.root.withdraw()
                self.is_hidden = True
            except Exception:
                pass

    # ---------------- Thread-Safe API ----------------

    def set_state(self, state: str, status_text: str = None, subtitle_text: str = None):
        """Thread-safe method to update overlay state and messages."""
        self.event_queue.put({
            "type": "state",
            "state": state,
            "status_text": status_text,
            "subtitle_text": subtitle_text
        })

    def set_subtitle(self, text: str):
        """Thread-safe method to update subtitle/transcription text."""
        self.event_queue.put({
            "type": "subtitle",
            "text": text
        })

    def set_language_badge(self, lang_name: str):
        """Thread-safe method to update active language."""
        self.event_queue.put({
            "type": "lang",
            "lang": lang_name
        })

    def close(self):
        """Safely closes the overlay window."""
        self.is_running = False
        self.event_queue.put({"type": "close"})

    # ---------------- Animation & Queue Loop ----------------

    def _periodic_tick(self):
        if not self.is_running or not self.root:
            return

        # 1. Process pending thread-safe events
        while not self.event_queue.empty():
            try:
                event = self.event_queue.get_nowait()
                event_type = event.get("type")

                if event_type == "state":
                    self.state = event.get("state", self.state)
                    if event.get("status_text"):
                        self.status_text = event["status_text"]
                    if event.get("subtitle_text") is not None:
                        self.subtitle_text = event["subtitle_text"]
                    
                    # Auto-show overlay when active
                    if self.state in [STATE_LISTENING, STATE_THINKING, STATE_SPEAKING]:
                        self.show()

                elif event_type == "subtitle":
                    self.subtitle_text = event.get("text", "")
                    if self.subtitle_text:
                        self.show()

                elif event_type == "lang":
                    self.lang_badge.configure(text=event.get("lang", "EN"))

                elif event_type == "close":
                    try:
                        self.root.destroy()
                    except Exception:
                        pass
                    return

            except queue.Empty:
                break

        # 2. Update UI widgets
        try:
            self.lbl_status.configure(text=self.status_text)
            self.lbl_subtitle.configure(text=self.subtitle_text)

            # Update status colors & button highlights based on state
            if self.state == STATE_LISTENING:
                self.lbl_status.configure(fg=self.ACCENT_CYAN)
                self.btn_mic.configure(bg=self.ACCENT_CYAN, text="🎙️")
                self.logo_canvas.itemconfig(self.logo_dot, fill=self.ACCENT_CYAN)
            elif self.state == STATE_THINKING:
                self.lbl_status.configure(fg=self.ACCENT_PURPLE)
                self.btn_mic.configure(bg=self.ACCENT_PURPLE, text="⚡")
                self.logo_canvas.itemconfig(self.logo_dot, fill=self.ACCENT_PURPLE)
            elif self.state == STATE_SPEAKING:
                self.lbl_status.configure(fg="#38bdf8")
                self.btn_mic.configure(bg="#2563eb", text="🔊")
                self.logo_canvas.itemconfig(self.logo_dot, fill="#38bdf8")
            elif self.state == STATE_OFFLINE:
                self.lbl_status.configure(fg=self.ACCENT_RED)
                self.btn_mic.configure(bg="#475569", text="💤")
                self.logo_canvas.itemconfig(self.logo_dot, fill=self.ACCENT_RED)
            else: # IDLE
                self.lbl_status.configure(fg=self.TEXT_SECONDARY)
                self.btn_mic.configure(bg=self.ACCENT_BLUE, text="🎙️")
                self.logo_canvas.itemconfig(self.logo_dot, fill=self.ACCENT_BLUE)

            # 3. Render animated Siri/Gemini style visualizer orb
            self._render_orb_animation()
        except Exception:
            pass

        # 4. Schedule next frame (~30 FPS)
        self.anim_frame += 1
        self.root.after(33, self._periodic_tick)

    def _render_orb_animation(self):
        """Draws dynamic multi-ring glowing orb based on assistant state."""
        canvas = self.orb_canvas
        canvas.delete("all")
        cx = self.orb_size / 2
        cy = self.orb_size / 2
        t = self.anim_frame * 0.08

        if self.state == STATE_LISTENING:
            # Pulsing Siri/Gemini Cyan Ripple
            pulse1 = (math.sin(t * 2) + 1) / 2
            pulse2 = (math.sin(t * 2 + 1.5) + 1) / 2
            
            # Outer ripples
            r_outer = 45 + pulse1 * 18
            canvas.create_oval(cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer, fill="", outline="#00e5ff", width=2)
            
            r_mid = 35 + pulse2 * 12
            canvas.create_oval(cx - r_mid, cy - r_mid, cx + r_mid, cy + r_mid, fill="#083344", outline="#38bdf8", width=2)
            
            # Glowing core
            r_core = 24 + pulse1 * 4
            canvas.create_oval(cx - r_core, cy - r_core, cx + r_core, cy + r_core, fill="#00e5ff", outline="#cffafe", width=2)
            
            # Inner mic dot
            canvas.create_oval(cx - 8, cy - 8, cx + 8, cy + 8, fill="#ffffff", outline="")

        elif self.state == STATE_THINKING:
            # Swirling Magenta / Purple Orbital Rings
            angle = t * 3
            canvas.create_oval(cx - 48, cy - 48, cx + 48, cy + 48, fill="", outline="#4c1d95", width=1)
            
            # Orbiting nodes
            for i in range(4):
                a = angle + i * (math.pi / 2)
                rad = 36 + math.sin(t * 3 + i) * 6
                ox = cx + math.cos(a) * rad
                oy = cy + math.sin(a) * rad
                color = self.ACCENT_PURPLE if i % 2 == 0 else "#ec4899"
                canvas.create_oval(ox - 7, oy - 7, ox + 7, oy + 7, fill=color, outline="")

            # Center core
            r_core = 20 + math.sin(t * 4) * 3
            canvas.create_oval(cx - r_core, cy - r_core, cx + r_core, cy + r_core, fill="#7e22ce", outline="#d8b4fe", width=2)

        elif self.state == STATE_SPEAKING:
            # Dynamic Audio Waveform Ring
            canvas.create_oval(cx - 30, cy - 30, cx + 30, cy + 30, fill="#1e3a8a", outline="#60a5fa", width=2)
            
            # Waveform bars around perimeter
            num_bars = 16
            for i in range(num_bars):
                a = i * (2 * math.pi / num_bars)
                height = 10 + 14 * abs(math.sin(t * 3 + i * 0.7))
                x1 = cx + math.cos(a) * 34
                y1 = cy + math.sin(a) * 34
                x2 = cx + math.cos(a) * (34 + height)
                y2 = cy + math.sin(a) * (34 + height)
                canvas.create_line(x1, y1, x2, y2, fill="#38bdf8", width=3, capstyle="round")
                
            # Center bright core
            canvas.create_oval(cx - 16, cy - 16, cx + 16, cy + 16, fill="#60a5fa", outline="#ffffff", width=2)

        elif self.state == STATE_OFFLINE:
            # Dimmed red stopped indicator
            canvas.create_oval(cx - 35, cy - 35, cx + 35, cy + 35, fill="#2a1215", outline="#7f1d1d", width=2)
            canvas.create_oval(cx - 18, cy - 18, cx + 18, cy + 18, fill="#ef4444", outline="")
            canvas.create_line(cx - 10, cy - 10, cx + 10, cy + 10, fill="#ffffff", width=3)
            canvas.create_line(cx + 10, cy - 10, cx - 10, cy + 10, fill="#ffffff", width=3)

        else:
            # IDLE - Gentle Breathing Ring
            breath = (math.sin(t) + 1) / 2
            r_b = 32 + breath * 5
            canvas.create_oval(cx - 46, cy - 46, cx + 46, cy + 46, fill="", outline="#1e293b", width=1)
            canvas.create_oval(cx - r_b, cy - r_b, cx + r_b, cy + r_b, fill="#1e2433", outline="#3b82f6", width=2)
            canvas.create_oval(cx - 16, cy - 16, cx + 16, cy + 16, fill="#3b82f6", outline="")


# Global singleton instance holder
_global_ui_overlay: Optional[JarvisOverlayUI] = None

def get_overlay_ui() -> Optional[JarvisOverlayUI]:
    return _global_ui_overlay

def init_overlay_ui(
    on_mic_click: Optional[Callable[[], None]] = None,
    on_hangup_click: Optional[Callable[[], None]] = None,
    on_stop_click: Optional[Callable[[], None]] = None,
) -> JarvisOverlayUI:
    global _global_ui_overlay
    if _global_ui_overlay is None:
        _global_ui_overlay = JarvisOverlayUI(
            on_mic_click=on_mic_click,
            on_hangup_click=on_hangup_click,
            on_stop_click=on_stop_click
        )
        _global_ui_overlay.start()
    return _global_ui_overlay
