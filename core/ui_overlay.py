"""
JARVIS Iron Man Holographic HUD Overlay
Authentic Tony Stark Mark VI/VII Arc Reactor center-screen translucent HUD.
Features real-time audio visualizer, rotating holographic radar ticks, telemetry subtitles,
smooth rounded pill buttons (Stop, Talk, Turn Off), and one-click permanent shutdown.
"""

import sys
import math
import time
import queue
import threading
import tkinter as tk
from pathlib import Path
from typing import Optional, Callable
from PIL import Image, ImageTk

# State constants
STATE_IDLE = "idle"
STATE_LISTENING = "listening"
STATE_THINKING = "thinking"
STATE_SPEAKING = "speaking"
STATE_OFFLINE = "offline"

# Color Palette - Iron Man Holographic Glass
BG_GLASS = "#060d14"
BORDER_DARK = "#003344"
CYAN = "#00f0ff"
DARK_CYAN = "#004455"
GOLD = "#ffb300"
PURPLE = "#c084fc"
RED = "#ef4444"
TEXT_WHITE = "#f0f9ff"
TEXT_MUTED = "#64748b"


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
        self.status_text = "● PROTOCOL: STANDBY // READY"
        self.subtitle_text = "Say 'Hey Jarvis' or click Talk to begin..."
        self.is_running = True
        self.is_hidden = False
        self.anim_frame = 0
        self.root = None
        self._thread = None
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._auto_hide_id = None
        self._reactor_img_tk = None

    def start(self):
        """Starts the UI in a dedicated GUI thread."""
        self._thread = threading.Thread(target=self._run_tk, daemon=True)
        self._thread.start()

    def _run_tk(self):
        # Ensure secondary thread is attached to the active interactive desktop on Windows
        if sys.platform == "win32":
            try:
                import ctypes
                user32 = ctypes.windll.user32
                hdesk = user32.OpenDesktopW('default', 0, False, 0x01FF)
                if hdesk:
                    user32.SetThreadDesktop(hdesk)
            except Exception:
                pass

        self.root = tk.Tk()
        self.root.title("JARVIS HUD")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        
        # Authentic Iron Man Visor translucent glassmorphism
        try:
            self.root.attributes("-alpha", 0.86)
        except Exception:
            pass

        # Window dimensions & positioning (Centered on screen)
        width = 420
        height = 520
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        pos_x = (screen_width - width) // 2
        pos_y = (screen_height - height) // 2

        self.root.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
        self.root.configure(bg=BG_GLASS)

        # Build Main Sci-Fi Canvas
        self.canvas = tk.Canvas(
            self.root,
            width=width,
            height=height,
            bg=BG_GLASS,
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        # Enable window dragging by top header area
        self.canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self.canvas.bind("<B1-Motion>", self._on_drag_motion)

        # Load Triangular Arc Reactor Asset
        asset_path = Path(__file__).resolve().parent.parent / "data" / "arc_reactor_hud.png"
        if asset_path.exists():
            try:
                pil_img = Image.open(asset_path)
                self._reactor_img_tk = ImageTk.PhotoImage(pil_img)
            except Exception:
                self._reactor_img_tk = None

        # Bind Rounded Button Click Events on Canvas
        self.canvas.tag_bind("btn_stop", "<Button-1>", lambda e: self._handle_stop_click())
        self.canvas.tag_bind("btn_talk", "<Button-1>", lambda e: self._handle_mic_click())
        self.canvas.tag_bind("btn_turnoff", "<Button-1>", lambda e: self._handle_hangup_click())

        # Bind Hover Hand Cursors for Rounded Buttons
        for tag in ["btn_stop", "btn_talk", "btn_turnoff"]:
            self.canvas.tag_bind(tag, "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
            self.canvas.tag_bind(tag, "<Leave>", lambda e: self.canvas.config(cursor=""))

        # Auto-hide after 3.5s of initial greeting
        self._schedule_auto_hide(delay_ms=3500)
        self._periodic_tick()
        self.root.mainloop()

    def _draw_rounded_pill(self, x1, y1, x2, y2, radius=18, tag=None, **kwargs):
        """Draws a smooth rounded pill polygon directly on the canvas."""
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
        if tag:
            kwargs["tags"] = tag
        return self.canvas.create_polygon(points, **kwargs, smooth=True)

    def _draw_hud_frame(self, x1, y1, x2, y2, cut=20):
        """Draws Iron Man angular chamfered HUD border frame with golden corner brackets."""
        points = [
            x1 + cut, y1,
            x2 - cut, y1,
            x2, y1 + cut,
            x2, y2 - cut,
            x2 - cut, y2,
            x1 + cut, y2,
            x1, y2 - cut,
            x1, y1 + cut,
            x1 + cut, y1
        ]
        self.canvas.create_polygon(points, outline=BORDER_DARK, fill="#050c14", width=2)
        
        # Neon edge lines
        self.canvas.create_line(x1 + cut, y1, x2 - cut, y1, fill=CYAN, width=2)
        self.canvas.create_line(x1 + cut, y2, x2 - cut, y2, fill=CYAN, width=2)
        self.canvas.create_line(x1, y1 + cut, x1, y2 - cut, fill=CYAN, width=2)
        self.canvas.create_line(x2, y1 + cut, x2, y2 - cut, fill=CYAN, width=2)

        # Golden sci-fi brackets
        blen = 24
        self.canvas.create_line(x1 + cut, y1 + 6, x1 + cut + blen, y1 + 6, fill=GOLD, width=1.5)
        self.canvas.create_line(x2 - cut, y1 + 6, x2 - cut - blen, y1 + 6, fill=GOLD, width=1.5)

    def _on_drag_start(self, event):
        # Allow dragging if clicking in the upper region of HUD
        if event.y < 70:
            self._drag_start_x = event.x
            self._drag_start_y = event.y

    def _on_drag_motion(self, event):
        if self.root and event.y < 70:
            x = self.root.winfo_x() + (event.x - self._drag_start_x)
            y = self.root.winfo_y() + (event.y - self._drag_start_y)
            self.root.geometry(f"+{x}+{y}")

    def _handle_mic_click(self):
        if self.on_mic_click:
            threading.Thread(target=self.on_mic_click, daemon=True).start()

    def _handle_stop_click(self):
        if self.on_stop_click:
            threading.Thread(target=self.on_stop_click, daemon=True).start()
        else:
            self.set_state(STATE_IDLE, "● PROTOCOL: PAUSED", "Audio playback halted.")

    def _handle_hangup_click(self):
        """Permanent shutdown of Jarvis."""
        self.set_state(STATE_OFFLINE, "● PROTOCOL: TERMINATED // OFFLINE", "Jarvis shutting down permanently...")
        if self.on_hangup_click:
            threading.Thread(target=self.on_hangup_click, daemon=True).start()

    def show(self):
        """Pops up the window in the center of the screen, topmost over all applications."""
        self._cancel_auto_hide()
        if self.root:
            try:
                self.root.deiconify()
                self.root.lift()
                self.root.attributes("-topmost", True)
                self.is_hidden = False
                
                # Force Win32 Topmost & Foreground placement
                if sys.platform == "win32":
                    try:
                        import ctypes
                        user32 = ctypes.windll.user32
                        hwnd = self.root.winfo_id()
                        user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)
                        user32.SetForegroundWindow(hwnd)
                    except Exception:
                        pass
            except Exception:
                pass

    def hide(self):
        """Hides the overlay into background when idle."""
        self._cancel_auto_hide()
        if self.root:
            try:
                self.root.withdraw()
                self.is_hidden = True
            except Exception:
                pass

    def _schedule_auto_hide(self, delay_ms: int = 3000):
        if not self.root:
            return
        self._cancel_auto_hide()
        self._auto_hide_id = self.root.after(delay_ms, self._do_auto_hide)

    def _cancel_auto_hide(self):
        if self.root and self._auto_hide_id:
            try:
                self.root.after_cancel(self._auto_hide_id)
            except Exception:
                pass
            self._auto_hide_id = None

    def _do_auto_hide(self):
        self._auto_hide_id = None
        if self.state in [STATE_IDLE, STATE_OFFLINE]:
            self.hide()

    # ---------------- Thread-Safe API ----------------

    def set_state(self, state: str, status_text: str = None, subtitle_text: str = None):
        """Thread-safe method to update overlay state and telemetry."""
        self.event_queue.put({
            "type": "state",
            "state": state,
            "status_text": status_text,
            "subtitle_text": subtitle_text
        })

    def set_subtitle(self, text: str):
        """Thread-safe method to update directive transcription text."""
        self.event_queue.put({
            "type": "subtitle",
            "text": text
        })

    def set_language_badge(self, lang_name: str):
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
                    
                    # Auto pop-up overlay when active (Listening, Thinking, Speaking)
                    if self.state in [STATE_LISTENING, STATE_THINKING, STATE_SPEAKING]:
                        self.show()
                    elif self.state == STATE_IDLE:
                        # Auto-hide after 3 seconds of idle so screen remains unobstructed
                        self._schedule_auto_hide(delay_ms=3000)

                elif event_type == "subtitle":
                    self.subtitle_text = event.get("text", "")
                    if self.subtitle_text:
                        self.show()

                elif event_type == "close":
                    try:
                        self.root.destroy()
                    except Exception:
                        pass
                    return

            except queue.Empty:
                break

        # 2. Render Full Holographic Frame & Animations
        try:
            self._render_holographic_hud()
        except Exception:
            pass

        # 3. Schedule next frame (~30 FPS)
        self.anim_frame += 1
        self.root.after(33, self._periodic_tick)

    def _render_holographic_hud(self):
        """Draws the complete Stark Industries Arc Reactor HUD with rounded pill buttons."""
        canvas = self.canvas
        canvas.delete("all")

        w, h = 420, 520
        cx, cy = w // 2, 175
        t = self.anim_frame * 0.08

        # 1. Outer chamfered sci-fi frame
        self._draw_hud_frame(8, 8, w - 8, h - 8, cut=20)

        # 2. Top Header
        canvas.create_text(
            w // 2, 32,
            text="◈ S.T.A.R.K. INDUSTRIES // JARVIS HUD ◈",
            fill=CYAN,
            font=("Consolas", 10, "bold")
        )
        canvas.create_line(40, 48, w - 40, 48, fill=DARK_CYAN, width=1)

        # 3. Rotating Sci-Fi Radar Ticks
        rotation_offset = self.anim_frame * (2.5 if self.state == STATE_THINKING else 1.2)
        for angle_deg in range(0, 360, 15):
            cur_angle = angle_deg + rotation_offset
            rad = math.radians(cur_angle)
            r1, r2 = 100, 112
            
            # Color logic based on state
            if self.state == STATE_THINKING:
                color = PURPLE if angle_deg % 45 == 0 else DARK_CYAN
            elif self.state == STATE_SPEAKING:
                color = "#38bdf8" if angle_deg % 30 == 0 else DARK_CYAN
            elif self.state == STATE_OFFLINE:
                color = RED if angle_deg % 45 == 0 else "#450a0a"
            else:
                color = CYAN if angle_deg % 45 == 0 else (GOLD if angle_deg % 90 == 0 else DARK_CYAN)
                
            width = 2 if angle_deg % 45 == 0 else 1
            canvas.create_line(
                cx + r1 * math.cos(rad), cy + r1 * math.sin(rad),
                cx + r2 * math.cos(rad), cy + r2 * math.sin(rad),
                fill=color, width=width
            )

        # 4. Concentric HUD Rings
        canvas.create_oval(cx - 105, cy - 105, cx + 105, cy + 105, outline=DARK_CYAN, width=1)
        canvas.create_oval(cx - 114, cy - 114, cx + 114, cy + 114, outline="#002233", width=1)

        # 5. Acoustic Waveform Frequency Bars (Reacts dynamically)
        for i in range(-5, 6):
            if self.state in [STATE_LISTENING, STATE_SPEAKING]:
                wave = abs(math.sin(t * 3 + abs(i) * 0.7))
                bar_h = 8 + int(wave * 24)
            elif self.state == STATE_THINKING:
                wave = abs(math.sin(t * 4 + i))
                bar_h = 6 + int(wave * 16)
            else:
                bar_h = 8 + (5 - abs(i)) * 3

            bar_color = PURPLE if self.state == STATE_THINKING else (RED if self.state == STATE_OFFLINE else CYAN)
            canvas.create_line(cx - 120, cy + i * 9, cx - 120 - bar_h, cy + i * 9, fill=bar_color, width=2)
            canvas.create_line(cx + 120, cy + i * 9, cx + 120 + bar_h, cy + i * 9, fill=bar_color, width=2)

        # 6. Center Triangular Arc Reactor Asset
        if self._reactor_img_tk:
            canvas.create_image(cx, cy, image=self._reactor_img_tk)
        else:
            # Fallback procedural Arc Reactor
            canvas.create_oval(cx - 75, cy - 75, cx + 75, cy + 75, outline=CYAN, width=3)
            p1 = (cx, cy + 50)
            p2 = (cx - 45, cy - 35)
            p3 = (cx + 45, cy - 35)
            canvas.create_polygon([p1[0], p1[1], p2[0], p2[1], p3[0], p3[1]], fill="", outline=CYAN, width=4)

        # 7. Dynamic Telemetry Status
        status_color = CYAN
        if self.state == STATE_THINKING:
            status_color = PURPLE
        elif self.state == STATE_SPEAKING:
            status_color = "#38bdf8"
        elif self.state == STATE_OFFLINE:
            status_color = RED
        elif self.state == STATE_IDLE:
            status_color = "#94a3b8"

        canvas.create_text(
            w // 2, 305,
            text=self.status_text,
            fill=status_color,
            font=("Segoe UI", 12, "bold")
        )

        # 8. Directive / Spoken Subtitles
        sub_display = self.subtitle_text
        if len(sub_display) > 80:
            sub_display = sub_display[:77] + "..."
        canvas.create_text(
            w // 2, 345,
            text=f'"{sub_display}"' if not sub_display.startswith('"') else sub_display,
            fill=TEXT_WHITE,
            font=("Segoe UI", 10, "italic"),
            width=w - 60,
            justify="center"
        )

        # 9. Three Smooth Rounded Pill Buttons (Stop, Talk, Turn Off)
        btn_y1 = 390
        btn_y2 = 435
        btn_w = 110
        gap = 14
        start_x = (w - (btn_w * 3 + gap * 2)) // 2

        # Button 1: STOP (Rounded Pill)
        b1_x1 = start_x
        b1_x2 = b1_x1 + btn_w
        self._draw_rounded_pill(
            b1_x1, btn_y1, b1_x2, btn_y2,
            radius=18, tag="btn_stop",
            fill="#0d2230", outline=CYAN, width=1.5
        )
        canvas.create_text(
            (b1_x1 + b1_x2) // 2, (btn_y1 + btn_y2) // 2,
            text="⏸ STOP", fill=CYAN,
            font=("Segoe UI", 9, "bold"),
            tags="btn_stop"
        )

        # Button 2: TALK (Rounded Pill)
        b2_x1 = b1_x2 + gap
        b2_x2 = b2_x1 + btn_w
        talk_fill = CYAN if self.state == STATE_LISTENING else "#0284c7"
        talk_text_color = "#000000" if self.state == STATE_LISTENING else "#ffffff"
        self._draw_rounded_pill(
            b2_x1, btn_y1, b2_x2, btn_y2,
            radius=18, tag="btn_talk",
            fill=talk_fill, outline="#38bdf8", width=2
        )
        canvas.create_text(
            (b2_x1 + b2_x2) // 2, (btn_y1 + btn_y2) // 2,
            text="🎙 TALK", fill=talk_text_color,
            font=("Segoe UI", 9, "bold"),
            tags="btn_talk"
        )

        # Button 3: TURN OFF (Rounded Pill)
        b3_x1 = b2_x2 + gap
        b3_x2 = b3_x1 + btn_w
        self._draw_rounded_pill(
            b3_x1, btn_y1, b3_x2, btn_y2,
            radius=18, tag="btn_turnoff",
            fill="#dc2626", outline="#f87171", width=2
        )
        canvas.create_text(
            (b3_x1 + b3_x2) // 2, (btn_y1 + btn_y2) // 2,
            text="📞 TURN OFF", fill="#ffffff",
            font=("Segoe UI", 9, "bold"),
            tags="btn_turnoff"
        )

        # 10. Telemetry Diagnostics Footer
        canvas.create_text(
            w // 2, 480,
            text="SYS.TEMP: 37°C  |  PWR: 100%  |  STARK OS v4.2",
            fill=DARK_CYAN,
            font=("Consolas", 8, "bold")
        )


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
