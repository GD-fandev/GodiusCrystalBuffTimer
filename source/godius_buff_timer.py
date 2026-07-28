import ctypes
import json
import math
import os
import sys
import time
import tkinter as tk
from ctypes import wintypes
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageGrab, ImageTk


if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).resolve().parent
    RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR))
else:
    APP_DIR = Path(__file__).resolve().parent
    RESOURCE_DIR = APP_DIR

ROOT = APP_DIR


def resource_path(relative_path):
    return RESOURCE_DIR / relative_path

VK_CODES = {
    "0": 0x30,
    "1": 0x31,
    "2": 0x32,
    "3": 0x33,
    "4": 0x34,
    "5": 0x35,
    "6": 0x36,
    "7": 0x37,
    "8": 0x38,
    "9": 0x39,
    "F10": 0x79,
    "+": 0xBB,
    "-": 0xBD,
    "NUMPAD_ADD": 0x6B,
    "NUMPAD_SUBTRACT": 0x6D,
}

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
SW_SHOWNOACTIVATE = 4
HWND_TOPMOST = wintypes.HWND(-1)
GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

try:
    user32.SetProcessDPIAware()
except Exception:
    pass

EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

user32.EnumWindows.argtypes = [EnumWindowsProc, wintypes.LPARAM]
user32.EnumWindows.restype = wintypes.BOOL
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.IsWindowVisible.restype = wintypes.BOOL
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
user32.GetWindowTextLengthW.restype = ctypes.c_int
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowTextW.restype = ctypes.c_int
user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.GetWindowRect.restype = wintypes.BOOL
user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.GetClientRect.restype = wintypes.BOOL
user32.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
user32.ClientToScreen.restype = wintypes.BOOL
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
user32.GetAsyncKeyState.restype = ctypes.c_short
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.SetWindowPos.argtypes = [
    wintypes.HWND,
    wintypes.HWND,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_uint,
]
user32.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_long]
user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]

kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.QueryFullProcessImageNameW.argtypes = [
    wintypes.HANDLE,
    wintypes.DWORD,
    wintypes.LPWSTR,
    ctypes.POINTER(wintypes.DWORD),
]
kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL


def load_config():
    external_config = ROOT / "config.json"
    bundled_config = resource_path("config.json")
    config_path = external_config if external_config.exists() else bundled_config
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def process_path_from_pid(pid):
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return ""
    try:
        size = wintypes.DWORD(32768)
        buf = ctypes.create_unicode_buffer(size.value)
        if kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
            return buf.value
        return ""
    finally:
        kernel32.CloseHandle(handle)


def process_name_for_hwnd(hwnd):
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    path = process_path_from_pid(pid.value)
    return os.path.basename(path), pid.value


def window_title_for_hwnd(hwnd):
    length = user32.GetWindowTextLengthW(hwnd)
    if length <= 0:
        return ""
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value


def find_window_by_process_name(process_name):
    matches = []
    target = process_name.lower()

    def callback(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        name, _pid = process_name_for_hwnd(hwnd)
        if name.lower() == target:
            matches.append(hwnd)
        return True

    user32.EnumWindows(EnumWindowsProc(callback), 0)
    return matches[0] if matches else None


def find_window_by_title(title):
    if not title:
        return None
    matches = []
    needle = title.lower()

    def callback(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        if needle in window_title_for_hwnd(hwnd).lower():
            matches.append(hwnd)
        return True

    user32.EnumWindows(EnumWindowsProc(callback), 0)
    return matches[0] if matches else None


def get_window_rect(hwnd):
    rect = wintypes.RECT()
    if not hwnd or not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return None
    if rect.right <= rect.left or rect.bottom <= rect.top:
        return None
    return rect.left, rect.top, rect.right, rect.bottom


def get_client_screen_rect(hwnd):
    rect = wintypes.RECT()
    origin = wintypes.POINT(0, 0)
    if not hwnd or not user32.GetClientRect(hwnd, ctypes.byref(rect)):
        return None
    if not user32.ClientToScreen(hwnd, ctypes.byref(origin)):
        return None
    return origin.x, origin.y, origin.x + rect.right, origin.y + rect.bottom


def get_detection_base_rect(hwnd, origin):
    if origin == "screen":
        return 0, 0, user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    if origin == "window":
        return get_window_rect(hwnd)
    return get_client_screen_rect(hwnd)


def ensure_icon(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    size = 96
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx = cy = size // 2
    points = []
    for i in range(12):
        radius = 42 if i % 2 == 0 else 20
        angle = -math.pi / 2 + i * math.pi / 6
        points.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
    draw.polygon(points, fill=(125, 220, 255, 230), outline=(225, 250, 255, 255))
    draw.ellipse((30, 30, 66, 66), fill=(235, 255, 255, 210))
    draw.line((48, 8, 48, 88), fill=(245, 255, 255, 240), width=3)
    draw.line((8, 48, 88, 48), fill=(245, 255, 255, 220), width=3)
    draw.line((20, 20, 76, 76), fill=(245, 255, 255, 190), width=2)
    draw.line((76, 20, 20, 76), fill=(245, 255, 255, 190), width=2)
    img.save(path)


def format_time(seconds_left):
    seconds_left = max(0, int(math.ceil(seconds_left)))
    return str(seconds_left)


class BuffTimerApp:
    def __init__(self, config):
        self.config = config
        self.target_hwnd = None
        self.end_time = None
        self.started_at = None
        self.active_buff = None
        self.expired_buff_lock = None
        self.expired_buff_lock_until = 0.0
        self.last_cancel_down = False
        self.last_calibration_toggle_down = False
        self.last_grow_down = False
        self.last_shrink_down = False
        self.calibration_mode = False
        self.timer_visible = True
        self.config["timer_visible"] = True
        self.detect_hits = {}
        self.absent_hits = 0
        self.missing_hits = 0
        self.last_detect_at = 0.0
        self.last_absent_score = None
        self.last_capture_bbox = None
        self.buffs = self.load_buffs()
        self.absent_template = self.load_plain_template("absent_template_path")
        self.manual_position = False
        self.last_timer_geometry = ""

        self.root = tk.Tk()
        self.root.title("Godius Crystal Buff Timer")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#101722")

        self.width = int(config["window_width"])
        self.height = int(config["window_height"])
        start_x = int(config.get("timer_window_x", 120))
        start_y = int(config.get("timer_window_y", 120))
        start_x, start_y = self.clamp_timer_position(start_x, start_y)
        self.root.geometry(f"{self.width}x{self.height}+{start_x}+{start_y}")
        icon_size = int(config.get("display_icon_size", 80))
        self.default_buff_key = self.first_buff_key()
        self.base_icon = self.icon_for_buff(self.default_buff_key, icon_size)
        self.display_icon_opacity = max(0.0, min(1.0, float(config.get("display_icon_opacity", 0.7))))
        self.root.attributes("-alpha", self.display_icon_opacity)
        self.timer_image = None
        self.text_image = None

        self.transparent_key = "#010101"
        self.root.configure(bg=self.transparent_key)
        self.root.wm_attributes("-transparentcolor", self.transparent_key)

        self.frame = tk.Frame(self.root, bg=self.transparent_key, padx=0, pady=0)
        self.frame.pack(fill="both", expand=True)

        self.body_frame = tk.Frame(self.frame, bg=self.transparent_key)
        self.body_frame.pack(fill="both", expand=True)
        self.timer_label = tk.Label(self.body_frame, bg=self.transparent_key, bd=0)
        self.timer_label.place(relx=0.5, rely=0.5, anchor="center")
        self.text_window = self.create_text_window()
        self.text_label = tk.Label(self.text_window, bg=self.transparent_key, bd=0)
        self.text_label.pack(fill="both", expand=True)
        self.text_label.bind("<ButtonPress-1>", self.begin_drag)
        self.text_label.bind("<B1-Motion>", self.drag)
        self.apply_timer_geometry(start_x, start_y)
        self.render_no_buff_image()
        self.control_window = self.create_control_window()

        self.root.bind("<ButtonPress-1>", self.begin_drag)
        self.root.bind("<B1-Motion>", self.drag)
        self.timer_label.bind("<ButtonPress-1>", self.begin_drag)
        self.timer_label.bind("<B1-Motion>", self.drag)
        self.drag_x = 0
        self.drag_y = 0
        self.drag_enabled = False

        self.apply_tool_window_style()
        self.region_window = self.create_region_window()
        self.region_window.winfo_children()[0].bind("<ButtonPress-1>", self.begin_region_drag)
        self.region_window.winfo_children()[0].bind("<B1-Motion>", self.region_drag)
        self.tick()

    def create_region_window(self):
        return self.create_box_window("#ff3030", 0.45)

    def create_text_window(self):
        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(bg=self.transparent_key)
        win.wm_attributes("-transparentcolor", self.transparent_key)
        win.geometry(f"{self.width}x{self.height}+120+120")
        hwnd = win.winfo_id()
        exstyle = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, exstyle | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE)
        return win

    def create_control_window(self):
        win = tk.Toplevel(self.root)
        win.title("Crystal Buff Timer")
        win.resizable(False, False)
        win.configure(bg="#eff8fb")
        control_width = 300
        control_height = 118
        x = int(self.config.get("control_window_x", 40))
        y = int(self.config.get("control_window_y", 40))
        x, y = self.clamp_window_position(x, y, control_width, control_height)
        win.geometry(f"{control_width}x{control_height}+{x}+{y}")
        try:
            self.control_icon_image = ImageTk.PhotoImage(self.load_program_icon(32))
            win.iconphoto(True, self.control_icon_image)
        except Exception:
            self.control_icon_image = None

        shell = tk.Frame(win, bg="#eff8fb", padx=16, pady=14)
        shell.pack(fill="both", expand=True)
        header = tk.Frame(shell, bg="#eff8fb")
        header.pack(fill="x")
        if self.control_icon_image:
            tk.Label(header, image=self.control_icon_image, bg="#eff8fb", bd=0).pack(side="left", padx=(0, 8))
        title_area = tk.Frame(header, bg="#eff8fb")
        title_area.pack(side="left", fill="x", expand=True)
        tk.Label(
            title_area,
            text="Crystal Buff Timer",
            fg="#214252",
            bg="#eff8fb",
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        ).pack(fill="x")
        quit_button = tk.Button(
            shell,
            text="QUIT",
            command=self.quit_app,
            fg="#ffffff",
            bg="#4d9bb8",
            activeforeground="#ffffff",
            activebackground="#367e98",
            relief="flat",
            bd=0,
            padx=18,
            pady=7,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
        )
        quit_button.pack(fill="x", pady=(16, 0))
        win.protocol("WM_DELETE_WINDOW", self.quit_app)
        return win

    def create_box_window(self, color, alpha):
        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.attributes("-alpha", alpha)
        win.configure(bg="#ff00ff")
        win.wm_attributes("-transparentcolor", "#ff00ff")
        canvas = tk.Canvas(win, width=40, height=40, bg="#ff00ff", highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        canvas.create_rectangle(1, 1, 39, 39, outline=color, fill=color, width=3)
        win.withdraw()
        win.update_idletasks()
        hwnd = win.winfo_id()
        exstyle = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, exstyle | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE)
        return win

    def begin_region_drag(self, event):
        self.drag_enabled = bool(event.state & 0x0004)

    def region_drag(self, event):
        if not self.drag_enabled or not self.calibration_mode:
            return
        self.calibrate_region_at_screen_point(event.x_root, event.y_root)

    def apply_tool_window_style(self):
        hwnd = self.root.winfo_id()
        exstyle = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, exstyle | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE)

    def quit_app(self):
        self.save_control_window_position()
        self.save_config()
        self.root.destroy()

    def save_control_window_position(self):
        if not getattr(self, "control_window", None):
            return
        self.control_window.update_idletasks()
        x = self.control_window.winfo_x()
        y = self.control_window.winfo_y()
        width = max(1, self.control_window.winfo_width())
        height = max(1, self.control_window.winfo_height())
        x, y = self.clamp_window_position(x, y, width, height)
        self.config["control_window_x"] = x
        self.config["control_window_y"] = y

    def begin_drag(self, event):
        self.drag_enabled = bool(event.state & 0x0004)
        self.drag_x = event.x
        self.drag_y = event.y

    def drag(self, event):
        if not self.drag_enabled:
            return
        self.manual_position = True
        x = event.x_root - self.drag_x
        y = event.y_root - self.drag_y
        self.set_timer_position(x, y)
        self.apply_timer_geometry(x, y)

    def render_timer_image(self, text, color, buff_key=None):
        canvas = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        icon = self.icon_for_buff(buff_key or self.active_buff).copy()
        x = (self.width - icon.width) // 2
        y = (self.height - icon.height) // 2
        canvas.alpha_composite(icon, (x, y))
        self.timer_image = ImageTk.PhotoImage(canvas)
        self.timer_label.configure(image=self.timer_image)

        text_canvas = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_canvas)
        max_text_width = max(1, int(icon.width * 0.8))
        max_text_height = max(1, int(icon.height * 0.45))
        font = ImageFont.load_default()
        for size in range(max(12, int(icon.height * 0.72)), 9, -1):
            try:
                candidate = ImageFont.truetype("segoeuib.ttf", size)
            except OSError:
                break
            bbox = draw.textbbox((0, 0), text, font=candidate)
            if (bbox[2] - bbox[0]) <= max_text_width and (bbox[3] - bbox[1]) <= max_text_height:
                font = candidate
                break
        bbox = draw.textbbox((0, 0), text, font=font)
        tx = (self.width - (bbox[2] - bbox[0])) / 2 - bbox[0]
        ty = (self.height - (bbox[3] - bbox[1])) / 2 - bbox[1]
        draw.text((tx + 1, ty + 1), text, font=font, fill=(0, 0, 0, 190))
        draw.text((tx, ty), text, font=font, fill=color)
        self.text_image = ImageTk.PhotoImage(text_canvas)
        self.text_label.configure(image=self.text_image)

    def render_no_buff_image(self):
        canvas = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 230))
        self.timer_image = ImageTk.PhotoImage(canvas)
        self.timer_label.configure(image=self.timer_image)

        text_canvas = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_canvas)
        text = "No buff"
        font = ImageFont.load_default()
        for size in range(max(14, int(self.height * 0.22)), 9, -1):
            try:
                candidate = ImageFont.truetype("segoeuib.ttf", size)
            except OSError:
                break
            bbox = draw.textbbox((0, 0), text, font=candidate)
            if (bbox[2] - bbox[0]) <= int(self.width * 0.85):
                font = candidate
                break
        bbox = draw.textbbox((0, 0), text, font=font)
        tx = (self.width - (bbox[2] - bbox[0])) / 2 - bbox[0]
        ty = (self.height - (bbox[3] - bbox[1])) / 2 - bbox[1]
        draw.text((tx + 1, ty + 1), text, font=font, fill=(0, 0, 0, 220))
        draw.text((tx, ty), text, font=font, fill=(255, 220, 70, 255))
        self.text_image = ImageTk.PhotoImage(text_canvas)
        self.text_label.configure(image=self.text_image)

    def keep_timer_visible(self):
        if not self.timer_visible:
            return
        if not self.root.winfo_viewable():
            self.root.deiconify()
        if not self.text_window.winfo_viewable():
            self.text_window.deiconify()
        self.root.attributes("-topmost", True)
        self.text_window.attributes("-topmost", True)
        self.root.attributes("-alpha", self.display_icon_opacity)
        user32.ShowWindow(self.root.winfo_id(), SW_SHOWNOACTIVATE)
        user32.ShowWindow(self.text_window.winfo_id(), SW_SHOWNOACTIVATE)
        flags = SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW
        user32.SetWindowPos(self.root.winfo_id(), HWND_TOPMOST, 0, 0, 0, 0, flags)
        user32.SetWindowPos(self.text_window.winfo_id(), HWND_TOPMOST, 0, 0, 0, 0, flags)

    def is_target_foreground(self):
        fg = user32.GetForegroundWindow()
        if not fg:
            return False
        name, _pid = process_name_for_hwnd(fg)
        return name.lower() == self.config["process_name"].lower()

    def position_near_target(self):
        if not self.target_hwnd:
            self.target_hwnd = find_window_by_title(self.config.get("window_title", ""))
        if not self.target_hwnd:
            self.target_hwnd = find_window_by_process_name(self.config["process_name"])
        if self.manual_position:
            self.update_timer_attached_position()
            return bool(get_client_screen_rect(self.target_hwnd))
        rect = get_window_rect(self.target_hwnd)
        if not rect:
            self.target_hwnd = None
            return False
        left, top, right, bottom = rect
        client = get_client_screen_rect(self.target_hwnd)
        if client and self.config.get("timer_attach_to_client", True):
            x = client[0] + int(self.config.get("timer_offset_x", right - self.width - int(self.config["offset_x"])))
            y = client[1] + int(self.config.get("timer_offset_y", bottom - self.height - int(self.config["offset_y"])))
        else:
            x = right - self.width - int(self.config["offset_x"])
            y = bottom - self.height - int(self.config["offset_y"])
        x, y = self.clamp_timer_position(x, y)
        self.set_timer_position(x, y)
        self.apply_timer_geometry(x, y)
        return True

    def clamp_timer_position(self, x, y):
        return self.clamp_window_position(x, y, self.width, self.height)

    def clamp_window_position(self, x, y, width, height):
        screen_w = max(1, user32.GetSystemMetrics(0))
        screen_h = max(1, user32.GetSystemMetrics(1))
        max_x = max(0, screen_w - int(width))
        max_y = max(0, screen_h - int(height))
        return max(0, min(int(x), max_x)), max(0, min(int(y), max_y))

    def set_timer_position(self, x, y):
        x, y = self.clamp_timer_position(x, y)
        self.config["timer_window_x"] = x
        self.config["timer_window_y"] = y
        client = get_client_screen_rect(self.target_hwnd)
        if client:
            self.config["timer_attach_to_client"] = True
            self.config["timer_offset_x"] = x - client[0]
            self.config["timer_offset_y"] = y - client[1]
        self.save_config()

    def update_timer_attached_position(self):
        if not self.config.get("timer_attach_to_client", True):
            return
        client = get_client_screen_rect(self.target_hwnd)
        if not client:
            return
        x = client[0] + int(self.config.get("timer_offset_x", 18))
        y = client[1] + int(self.config.get("timer_offset_y", 46))
        x, y = self.clamp_timer_position(x, y)
        self.apply_timer_geometry(x, y)

    def apply_timer_geometry(self, x, y):
        x, y = self.clamp_timer_position(x, y)
        geometry = f"{self.width}x{self.height}+{x}+{y}"
        self.root.geometry(geometry)
        self.text_window.geometry(geometry)
        self.last_timer_geometry = geometry

    def handle_hotkey(self):
        cancel_vk = VK_CODES.get(str(self.config.get("cancel_key", "0")).upper())
        toggle_vk = VK_CODES.get(str(self.config.get("calibration_toggle_key", "F10")).upper())
        grow_vks = self.key_codes_for(self.config.get("grow_key", "+"), "+", "NUMPAD_ADD")
        shrink_vks = self.key_codes_for(self.config.get("shrink_key", "-"), "-", "NUMPAD_SUBTRACT")

        if cancel_vk and bool(self.config.get("allow_timer_visibility_toggle", False)):
            cancel_down = bool(user32.GetAsyncKeyState(cancel_vk) & 0x8000)
            if cancel_down and not self.last_cancel_down:
                self.toggle_timer_visibility()
            self.last_cancel_down = cancel_down
        else:
            self.last_cancel_down = False

        if toggle_vk:
            toggle_down = bool(user32.GetAsyncKeyState(toggle_vk) & 0x8000)
            if toggle_down and not self.last_calibration_toggle_down:
                self.toggle_calibration_mode()
            self.last_calibration_toggle_down = toggle_down

        if self.calibration_mode and grow_vks:
            grow_down = any(bool(user32.GetAsyncKeyState(vk) & 0x8000) for vk in grow_vks)
            if grow_down and not self.last_grow_down:
                self.resize_detect_region(2)
            self.last_grow_down = grow_down

        if self.calibration_mode and shrink_vks:
            shrink_down = any(bool(user32.GetAsyncKeyState(vk) & 0x8000) for vk in shrink_vks)
            if shrink_down and not self.last_shrink_down:
                self.resize_detect_region(-2)
            self.last_shrink_down = shrink_down

    def key_codes_for(self, *names):
        codes = []
        for name in names:
            code = VK_CODES.get(str(name).upper())
            if code is not None and code not in codes:
                codes.append(code)
        return codes

    def start_timer(self, buff_key):
        self.timer_visible = True
        self.config["timer_visible"] = True
        now = time.monotonic()
        seconds = float(self.config["duration_seconds"]) - float(self.config.get("start_adjust_seconds", 0))
        self.active_buff = buff_key
        self.base_icon = self.icon_for_buff(buff_key)
        self.started_at = now
        self.end_time = now + max(1.0, seconds)
        self.root.attributes("-alpha", self.display_icon_opacity)
        user32.ShowWindow(self.root.winfo_id(), SW_SHOWNOACTIVATE)
        user32.ShowWindow(self.text_window.winfo_id(), SW_SHOWNOACTIVATE)

    def toggle_timer_visibility(self):
        if not bool(self.config.get("allow_timer_visibility_toggle", False)):
            self.timer_visible = True
            self.config["timer_visible"] = True
            self.root.deiconify()
            self.text_window.deiconify()
            self.render_no_buff_image()
            self.save_config()
            return
        self.timer_visible = not self.timer_visible
        self.config["timer_visible"] = self.timer_visible
        self.end_time = None
        self.started_at = None
        self.active_buff = None
        self.expired_buff_lock = None
        self.expired_buff_lock_until = 0.0
        self.detect_hits = {}
        self.absent_hits = 0
        self.missing_hits = 0
        self.save_config()
        if self.timer_visible:
            self.root.deiconify()
            self.text_window.deiconify()
            self.render_no_buff_image()
        else:
            self.root.withdraw()
            self.text_window.withdraw()

    def toggle_calibration_mode(self):
        self.calibration_mode = not self.calibration_mode
        if not self.calibration_mode:
            self.save_config()
            if self.region_window:
                self.region_window.withdraw()
        else:
            self.update_region_window()

    def save_config(self):
        with open(ROOT / "config.json", "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
            f.write("\n")

    def calibrate_region_at_screen_point(self, screen_x, screen_y):

        box_w = 40
        box_h = 40
        current = self.config.get("detect_region", [0, 0, 40, 40])
        if len(current) == 4:
            box_w = max(8, int(current[2]) - int(current[0]))
            box_h = max(8, int(current[3]) - int(current[1]))

        if not self.target_hwnd:
            self.target_hwnd = find_window_by_title(self.config.get("window_title", ""))
        if not self.target_hwnd:
            self.target_hwnd = find_window_by_process_name(self.config["process_name"])
        if not self.target_hwnd:
            return

        client = get_client_screen_rect(self.target_hwnd)
        if not client:
            return

        client_left, client_top, client_right, client_bottom = client
        client_w = max(1, client_right - client_left)
        client_h = max(1, client_bottom - client_top)

        # Store the calibrated area in current client coordinates. Because the
        # origin stays tied to the Godius client area, moving the window later
        # keeps the detection box on the same in-game UI position.
        self.config["detect_coordinate_origin"] = "client"
        self.config["detect_reference_size"] = [client_w, client_h]
        left = round((screen_x - client_left) - box_w / 2)
        top = round((screen_y - client_top) - box_h / 2)
        self.config["detect_region"] = [left, top, left + box_w, top + box_h]
        self.save_config()
        self.last_capture_bbox = self.current_detection_bbox()

    def resize_detect_region(self, delta):
        region = self.config.get("detect_region", [0, 0, 40, 40])
        left, top, right, bottom = [int(v) for v in region]
        width = max(8, (right - left) + delta)
        height = max(8, (bottom - top) + delta)
        self.config["detect_region"] = [left, top, left + width, top + height]
        self.save_config()
        self.last_capture_bbox = self.current_detection_bbox()

    def current_detection_bbox(self):
        if not self.target_hwnd:
            self.target_hwnd = find_window_by_title(self.config.get("window_title", ""))
        if not self.target_hwnd:
            self.target_hwnd = find_window_by_process_name(self.config["process_name"])
        if not self.target_hwnd:
            return None
        region = self.config.get("detect_region")
        if not region or len(region) != 4:
            return None
        origin = str(self.config.get("detect_coordinate_origin", "client")).lower()
        base_rect = get_detection_base_rect(self.target_hwnd, origin)
        if not base_rect:
            return None
        base_left, base_top, base_right, base_bottom = base_rect
        base_width = max(1, base_right - base_left)
        base_height = max(1, base_bottom - base_top)
        left, top, right, bottom = [int(v) for v in region]
        reference = self.config.get("detect_reference_size", [base_width, base_height])
        if reference and len(reference) == 2:
            ref_width = max(1, float(reference[0]))
            ref_height = max(1, float(reference[1]))
            scale_x = base_width / ref_width
            scale_y = base_height / ref_height
            left = round(left * scale_x)
            right = round(right * scale_x)
            top = round(top * scale_y)
            bottom = round(bottom * scale_y)
        return base_left + left, base_top + top, base_left + right, base_top + bottom

    def configured_buffs(self):
        buffs = self.config.get("buffs")
        if isinstance(buffs, list) and buffs:
            return buffs
        return [
            {
                "key": "ice",
                "name": "Ice Crystal",
                "detect_template_path": self.config.get("detect_template_path", "icons/ice_crystal_template.png"),
                "display_icon_path": self.config.get("icon_path", "icons/ice_display.png"),
            }
        ]

    def first_buff_key(self):
        for buff in self.buffs:
            return buff["key"]
        return None

    def load_buffs(self):
        if not self.config.get("auto_detect", False):
            return []
        loaded = []
        for buff_config in self.configured_buffs():
            key = str(buff_config.get("key", "")).strip()
            if not key:
                continue
            template_path = resource_path(buff_config.get("detect_template_path", ""))
            icon_path = resource_path(buff_config.get("display_icon_path", self.config.get("icon_path", "")))
            if not template_path.exists() or not icon_path.exists():
                continue
            template = Image.open(template_path).convert("RGB")
            loaded.append({
                "key": key,
                "name": str(buff_config.get("name", key)),
                "template": template,
                "mask": self.create_detect_mask(template),
                "icon_path": icon_path,
                "icon_cache": {},
            })
        return loaded

    def create_detect_mask(self, template):
        arr = np.asarray(template, dtype=np.uint8)
        # Compare mostly bright and saturated crystal pixels so similar empty UI
        # slots do not trigger.
        luma = (0.299 * arr[:, :, 0]) + (0.587 * arr[:, :, 1]) + (0.114 * arr[:, :, 2])
        channel_spread = np.max(arr, axis=2).astype(np.int16) - np.min(arr, axis=2).astype(np.int16)
        mask = (luma > 105) | ((luma > 65) & (channel_spread > 35))
        if np.count_nonzero(mask) < 20:
            mask = luma > np.percentile(luma, 70)
        return Image.fromarray((mask.astype(np.uint8) * 255), mode="L")

    def buff_by_key(self, buff_key):
        for buff in self.buffs:
            if buff["key"] == buff_key:
                return buff
        return self.buffs[0] if self.buffs else None

    def icon_for_buff(self, buff_key, size=None):
        buff = self.buff_by_key(buff_key)
        icon_size = int(size or self.config.get("display_icon_size", 80))
        if not buff:
            icon_path = resource_path(self.config.get("icon_path", "icons/ice_display.png"))
            ensure_icon(icon_path)
            return Image.open(icon_path).convert("RGBA").resize((icon_size, icon_size), Image.Resampling.NEAREST)
        cache = buff["icon_cache"]
        if icon_size not in cache:
            cache[icon_size] = Image.open(buff["icon_path"]).convert("RGBA").resize((icon_size, icon_size), Image.Resampling.NEAREST)
        return cache[icon_size]

    def load_program_icon(self, size):
        path = resource_path(self.config.get("program_icon_path", "icons/Godius_104.png"))
        return Image.open(path).convert("RGBA").resize((int(size), int(size)), Image.Resampling.LANCZOS)

    def load_plain_template(self, config_key):
        path = resource_path(self.config.get(config_key, ""))
        if not path.exists():
            return None
        return Image.open(path).convert("RGB")

    def detect_buff_present(self):
        if not self.buffs or not self.target_hwnd:
            return None
        region = self.config.get("detect_region")
        if not region or len(region) != 4:
            return None
        origin = str(self.config.get("detect_coordinate_origin", "client")).lower()
        base_rect = get_detection_base_rect(self.target_hwnd, origin)
        if not base_rect:
            self.target_hwnd = None
            return None

        base_left, base_top, base_right, base_bottom = base_rect
        base_width = max(1, base_right - base_left)
        base_height = max(1, base_bottom - base_top)
        left, top, right, bottom = [int(v) for v in region]
        reference = self.config.get("detect_reference_size", [base_width, base_height])
        if reference and len(reference) == 2:
            ref_width = max(1, float(reference[0]))
            ref_height = max(1, float(reference[1]))
            scale_x = base_width / ref_width
            scale_y = base_height / ref_height
            left = round(left * scale_x)
            right = round(right * scale_x)
            top = round(top * scale_y)
            bottom = round(bottom * scale_y)
        bbox = (base_left + left, base_top + top, base_left + right, base_top + bottom)
        if bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
            return None
        self.last_capture_bbox = bbox

        try:
            if self.region_window:
                self.region_window.withdraw()
                self.region_window.update_idletasks()
            if self.config.get("hide_overlay_during_capture", False):
                self.root.withdraw()
                self.text_window.withdraw()
                self.root.update_idletasks()
                time.sleep(0.03)
            capture = ImageGrab.grab(bbox=bbox).convert("RGB")
            if self.config.get("hide_overlay_during_capture", False):
                self.root.deiconify()
                self.text_window.deiconify()
        except OSError:
            if self.config.get("hide_overlay_during_capture", False):
                self.root.deiconify()
                self.text_window.deiconify()
            return None

        if self.absent_template:
            self.last_absent_score = self.score_by_pixel_difference(capture, self.absent_template)
            absent_threshold = float(self.config.get("absent_threshold", 0.82))
            if self.last_absent_score >= absent_threshold:
                return None

        threshold = float(self.config.get("detect_threshold", 0.62))
        best_key = None
        best_score = threshold
        for buff in self.buffs:
            template = buff["template"]
            mask = buff["mask"]
            detect_score = self.score_template(capture, template, mask)
            if detect_score >= best_score:
                best_key = buff["key"]
                best_score = detect_score
        return best_key

    def score_template(self, capture, template, mask):
        if template.size != capture.size:
            template = template.resize(capture.size, Image.Resampling.LANCZOS)
            if mask:
                mask = mask.resize(capture.size, Image.Resampling.NEAREST)

        cap_rgb = np.asarray(capture, dtype=np.float32)
        tmpl_rgb = np.asarray(template, dtype=np.float32)
        if mask:
            mask_arr = np.asarray(mask, dtype=bool)
            if np.count_nonzero(mask_arr) > 0:
                cap_rgb = cap_rgb[mask_arr]
                tmpl_rgb = tmpl_rgb[mask_arr]

        pixel_similarity = float(1.0 - (np.mean(np.abs(cap_rgb - tmpl_rgb)) / 255.0))

        cap = cap_rgb.reshape(-1)
        tmpl = tmpl_rgb.reshape(-1)
        cap_std = float(np.std(cap))
        tmpl_std = float(np.std(tmpl))
        if cap_std < 0.001 or tmpl_std < 0.001:
            correlation = 0.0
        else:
            correlation = float(np.mean(((cap - np.mean(cap)) / cap_std) * ((tmpl - np.mean(tmpl)) / tmpl_std)))
            correlation = (correlation + 1.0) / 2.0
        return (correlation * 0.45) + (pixel_similarity * 0.55)

    def score_by_pixel_difference(self, capture, template):
        if template.size != capture.size:
            template = template.resize(capture.size, Image.Resampling.NEAREST)
        cap = np.asarray(capture, dtype=np.float32)
        tmpl = np.asarray(template, dtype=np.float32)
        return float(1.0 - (np.mean(np.abs(cap - tmpl)) / 255.0))

    def update_region_window(self):
        if not self.region_window:
            return
        if self.calibration_mode:
            self.last_capture_bbox = self.current_detection_bbox()
        if not self.calibration_mode or not self.last_capture_bbox:
            self.region_window.withdraw()
            return
        left, top, right, bottom = self.last_capture_bbox
        width = max(1, right - left)
        height = max(1, bottom - top)
        self.region_window.geometry(f"{width}x{height}+{left}+{top}")
        canvas = self.region_window.winfo_children()[0]
        canvas.configure(width=width, height=height)
        canvas.delete("all")
        canvas.create_rectangle(1, 1, width - 2, height - 2, outline="#ff3030", fill="#ff3030", width=3)
        self.region_window.deiconify()

    def handle_auto_detect(self):
        if not self.config.get("auto_detect", False):
            return
        if self.calibration_mode:
            return
        if not self.is_target_foreground():
            return
        now = time.monotonic()
        interval = max(0.1, float(self.config.get("detect_interval_ms", 350)) / 1000.0)
        if now - self.last_detect_at < interval:
            return
        self.last_detect_at = now

        detected_buff = self.detect_buff_present()
        absent_detected = False
        if self.last_absent_score is not None:
            absent_detected = self.last_absent_score >= float(self.config.get("absent_threshold", 0.82))
        if not detected_buff:
            self.detect_hits = {}
            self.expired_buff_lock = None
            self.expired_buff_lock_until = 0.0
            if self.end_time is not None:
                absent_grace_seconds = max(0.0, float(self.config.get("absent_grace_seconds", 5)))
                started_at = self.started_at if self.started_at is not None else now
                can_stop_on_absent = now - started_at >= absent_grace_seconds
                if can_stop_on_absent:
                    self.missing_hits += 1
                    if absent_detected:
                        self.absent_hits += 1
                    else:
                        self.absent_hits = 0
                else:
                    self.absent_hits = 0
                    self.missing_hits = 0
                required_absent = max(1, int(self.config.get("absent_required_hits", 2)))
                required_missing = max(required_absent, int(self.config.get("missing_required_hits", required_absent)))
                stop_on_absent = bool(self.config.get("stop_when_absent_detected", True))
                stop_on_missing = bool(self.config.get("stop_when_icon_missing", False))
                absent_long_enough = stop_on_absent and absent_detected and self.absent_hits >= required_absent
                missing_long_enough = stop_on_missing and self.missing_hits >= required_missing
                if absent_long_enough or missing_long_enough:
                    self.end_time = None
                    self.started_at = None
                    self.active_buff = None
                    self.expired_buff_lock = None
                    self.expired_buff_lock_until = 0.0
                    self.absent_hits = 0
                    self.missing_hits = 0
            else:
                self.absent_hits = 0
                self.missing_hits = 0
            return

        for buff_key in list(self.detect_hits):
            if buff_key != detected_buff:
                self.detect_hits[buff_key] = 0

        if self.expired_buff_lock and now >= self.expired_buff_lock_until:
            self.expired_buff_lock = None
            self.expired_buff_lock_until = 0.0

        if self.expired_buff_lock == detected_buff:
            self.detect_hits[detected_buff] = 0
            self.absent_hits = 0
            self.missing_hits = 0
            return

        self.detect_hits[detected_buff] = self.detect_hits.get(detected_buff, 0) + 1
        self.absent_hits = 0
        self.missing_hits = 0

        required_hits = max(1, int(self.config.get("detect_required_hits", 2)))
        if self.detect_hits[detected_buff] >= required_hits:
            if self.end_time is None or self.active_buff != detected_buff:
                self.start_timer(detected_buff)

    def update_display(self):
        if self.end_time is None:
            self.render_no_buff_image()
            self.root.attributes("-alpha", self.display_icon_opacity)
            return
        remaining = self.end_time - time.monotonic()
        if remaining <= 0:
            expired_buff = self.active_buff
            self.active_buff = None
            self.started_at = None
            self.end_time = None
            self.expired_buff_lock = expired_buff
            self.expired_buff_lock_until = time.monotonic() + max(
                0.0,
                float(self.config.get("expire_restart_suppression_seconds", 1.5)),
            )
            self.detect_hits = {}
            self.absent_hits = 0
            self.missing_hits = 0
            self.render_no_buff_image()
            self.root.attributes("-alpha", self.display_icon_opacity)
            return
        color = "#ff5555" if remaining <= 10 else "#ffdf7d" if remaining <= 30 else "#ffffff"
        label = format_time(remaining)
        self.render_timer_image(label, color, self.active_buff)
        self.root.attributes("-alpha", self.display_icon_opacity)

    def tick(self):
        self.position_near_target()
        self.handle_hotkey()
        self.handle_auto_detect()
        self.update_region_window()
        self.update_display()
        self.keep_timer_visible()
        self.root.after(100, self.tick)

    def run(self):
        self.root.mainloop()


def main():
    if sys.platform != "win32":
        raise SystemExit("This overlay is Windows-only.")
    config = load_config()
    BuffTimerApp(config).run()


if __name__ == "__main__":
    main()
