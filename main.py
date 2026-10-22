"""
Mechanical Keyboard Audio Simulator
===================================
A lightweight, zero-latency desktop application that simulates authentic,
studio-recorded mechanical switch sounds for every OS-wide keystroke.

Features:
- Pure Keyboard Simulation: Global low-latency OS hook via `pynput`
- 100% Authentic Internet Sound Packs (Drop Holy Panda, NovelKeys Cream, Gateron Black Ink,
  Cherry MX Blue/Brown/Black/Speed Silver, ZealPC Tealios V2, Logitech G915, Mechvibes Classic, etc.)
- Multi-sample Acoustic Banks & Character Mapping (exact key recordings like a.wav, b.wav, etc.)
- Stabilizer Audio Mapping (Spacebar, Enter, Backspace, Shift) with robust fallback
- Cascading Brand & Model dropdown selectors
- Sub-5ms ultra-low latency audio playback via `pygame.mixer` (128 buffer • 64 channels)
- System tray minimization and background operation via `pystray`
"""

import json
import os
import random
import sys
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional

# Pre-initialize pygame mixer BEFORE importing/initializing standard pygame modules
# to force low audio buffer and sample settings for lowest possible latency.
import pygame

try:
    pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=128)
    pygame.init()
    pygame.mixer.set_num_channels(64)
except Exception as e:
    print(f"Warning initializing audio mixer: {e}")

import customtkinter as ctk
from PIL import Image, ImageDraw
import pynput
from pynput.keyboard import Key, KeyCode
import pystray

BASE_DIR = Path(__file__).resolve().parent
SOUNDS_DIR = BASE_DIR / "sounds"

# Windows Scan Code Mapping for Mechvibes packs
SCAN_CODE_MAP = {
    Key.space: "57",
    Key.enter: "28",
    Key.backspace: "14",
    Key.shift: "42",
    getattr(Key, "shift_l", Key.shift): "42",
    getattr(Key, "shift_r", Key.shift): "54",
    Key.tab: "15",
    Key.caps_lock: "58",
    Key.esc: "1",
}


class SoundManager:
    """Manages brand & model audio libraries and zero-latency playback."""

    def __init__(self, sounds_dir: Path):
        self.sounds_dir = sounds_dir
        self.library: Dict[str, List[str]] = {}
        self.current_brand: str = ""
        self.current_model: str = ""
        self.volume: float = 0.8

        # Sound caches
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.keycode_sounds: Dict[str, pygame.mixer.Sound] = {}
        self.char_sounds: Dict[str, pygame.mixer.Sound] = {}
        self.multi_samples: List[pygame.mixer.Sound] = []

        self.rescan_library()

    def rescan_library(self) -> Dict[str, List[str]]:
        """
        Scans sounds/ directory for:
          sounds/<Brand_Name>/<Model_Name>/
        Returns a dictionary mapping: Brand -> List of Models.
        """
        self.library.clear()
        if not self.sounds_dir.exists():
            return self.library

        audio_extensions = {".wav", ".mp3", ".ogg"}

        for brand_entry in sorted(self.sounds_dir.iterdir()):
            if brand_entry.is_dir():
                models = []
                for model_entry in sorted(brand_entry.iterdir()):
                    if model_entry.is_dir():
                        audio_files = [
                            f for f in model_entry.iterdir()
                            if f.suffix.lower() in audio_extensions
                        ]
                        if audio_files:
                            models.append(model_entry.name)
                if models:
                    self.library[brand_entry.name] = models

        return self.library

    def get_brands(self) -> List[str]:
        """Returns sorted list of available brands."""
        return sorted(list(self.library.keys()))

    def get_models_for_brand(self, brand: str) -> List[str]:
        """Returns models for a given brand."""
        return self.library.get(brand, [])

    def load_model(self, brand: str, model: str):
        """
        Pre-loads all key audio files for the given brand and model into memory.
        Supports:
          1. Exact key letter sounds (e.g. a.wav, b.wav in NK Cream).
          2. Mechvibes config.json scan-code definitions.
          3. Multi-sample key variation banks.
          4. Stabilizers (space, enter, backspace, shift).
          5. Universal default fallback sound.
        """
        self.current_brand = brand
        self.current_model = model
        model_path = self.sounds_dir / brand / model
        self.sounds.clear()
        self.keycode_sounds.clear()
        self.char_sounds.clear()
        self.multi_samples.clear()

        if not model_path.exists():
            print(f"Error: Path {model_path} does not exist.")
            return

        # 1. Mechvibes config.json support
        config_path = model_path / "config.json"
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                    defines = config_data.get("defines", {})
                    for code_str, file_name in defines.items():
                        target_file = model_path / file_name
                        if target_file.exists():
                            snd = pygame.mixer.Sound(str(target_file))
                            snd.set_volume(self.volume)
                            self.keycode_sounds[str(code_str)] = snd
            except Exception as e:
                print(f"Notice: Parsing config.json: {e}")

        # 2. Collect all audio files in the folder
        audio_files = [
            f for f in model_path.iterdir()
            if f.suffix.lower() in (".wav", ".mp3", ".ogg")
        ]

        # 3. Detect character-specific key sounds (e.g., 'a.wav', 'b.wav')
        for f in audio_files:
            stem = f.stem.lower()
            if len(stem) == 1 and stem.isalpha():
                try:
                    char_snd = pygame.mixer.Sound(str(f))
                    char_snd.set_volume(self.volume)
                    self.char_sounds[stem] = char_snd
                except Exception:
                    pass

        # 4. Collect multi-sample sound banks for typing variety
        for f in audio_files:
            stem = f.stem.lower()
            if (
                stem.isdigit()
                or "key" in stem
                or "generic" in stem
                or "clip" in stem
                or stem.startswith("mx-")
            ):
                try:
                    ms_snd = pygame.mixer.Sound(str(f))
                    ms_snd.set_volume(self.volume)
                    self.multi_samples.append(ms_snd)
                except Exception:
                    pass

        # 5. Stabilizer and default mappings with robust fallback
        candidate_map = {
            "default": ["default", "key1", "key-press-1", "press_key1", "1", "1real", "a"],
            "space": ["space", "press_space", "space-press-1"],
            "enter": ["enter", "ent", "press_enter", "enter-press-1"],
            "backspace": ["backspace", "back", "delete", "press_back", "7"],
            "shift": ["shift", "press_key2", "key-press-2", "20", "key2"],
        }

        for target_key, candidates in candidate_map.items():
            matched_sound = None
            for cand in candidates:
                for ext in [".wav", ".mp3", ".ogg"]:
                    cand_path = model_path / f"{cand}{ext}"
                    if cand_path.exists():
                        try:
                            matched_sound = pygame.mixer.Sound(str(cand_path))
                            break
                        except Exception:
                            pass
                if matched_sound:
                    break

            if matched_sound:
                self.sounds[target_key] = matched_sound

        # If default sound is still missing, fallback to any available audio file
        if "default" not in self.sounds and audio_files:
            try:
                self.sounds["default"] = pygame.mixer.Sound(str(audio_files[0]))
            except Exception:
                pass

        # Fallback missing stabilizers to default
        default_sound = self.sounds.get("default")
        for k in ["space", "enter", "backspace", "shift"]:
            if k not in self.sounds and default_sound:
                self.sounds[k] = default_sound

        self.apply_volume(self.volume)

    def apply_volume(self, volume: float):
        """Sets playback volume [0.0 - 1.0] across all active cached sounds."""
        self.volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            if sound:
                sound.set_volume(self.volume)
        for sound in self.keycode_sounds.values():
            if sound:
                sound.set_volume(self.volume)
        for sound in self.char_sounds.values():
            if sound:
                sound.set_volume(self.volume)
        for sound in self.multi_samples:
            if sound:
                sound.set_volume(self.volume)

    def play_key(self, sound_type: str = "default", key=None, char_key: Optional[str] = None):
        """
        Plays the mapped switch sound with sub-millisecond execution time.
        Priority:
          1. Character-specific key sound (e.g. a.wav, b.wav if available)
          2. Mechvibes config.json scan-code match
          3. Specific stabilizer mapping (space, enter, backspace, shift)
          4. Random selection from multi-sample bank (realistic acoustic variety)
          5. Universal default fallback sound
        """
        sound: Optional[pygame.mixer.Sound] = None

        # 1. Check character-specific sound
        if char_key and char_key in self.char_sounds:
            sound = self.char_sounds[char_key]

        # 2. Check Mechvibes scan-code
        if sound is None and self.keycode_sounds and key is not None:
            scan_code = SCAN_CODE_MAP.get(key)
            if scan_code and scan_code in self.keycode_sounds:
                sound = self.keycode_sounds[scan_code]

        # 3. Check specific stabilizer sound
        if sound is None and sound_type != "default":
            sound = self.sounds.get(sound_type)

        # 4. Multi-sample organic bank for regular alphanumeric typing
        if sound is None and sound_type == "default" and self.multi_samples:
            sound = random.choice(self.multi_samples)

        # 5. Default fallback
        if sound is None:
            sound = self.sounds.get("default")

        # Play sound immediately
        if sound:
            channel = pygame.mixer.find_channel()
            if channel:
                channel.play(sound)
            else:
                sound.play()


class KeyboardListenerService:
    """Manages the global OS-level keyboard listener via pynput with hold-repeat suppression."""

    def __init__(self, sound_manager: SoundManager, on_key_event=None):
        self.sound_manager = sound_manager
        self.on_key_event = on_key_event
        self.is_running = False
        self._listener: Optional[pynput.keyboard.Listener] = None
        self._pressed_keys = set()
        self._lock = threading.Lock()

    def _get_key_id(self, key):
        """Generates a stable, unique identifier for a physical key to detect held state."""
        if hasattr(key, "vk") and key.vk is not None:
            return ("vk", key.vk)
        if isinstance(key, Key):
            return ("key", key.name)
        if isinstance(key, KeyCode) and key.char:
            return ("char", key.char.lower())
        return ("str", str(key))

    def start(self):
        if self.is_running and self._listener:
            return

        with self._lock:
            self._pressed_keys.clear()

        self.is_running = True
        self._listener = pynput.keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
            suppress=False,  # Non-blocking hook
        )
        self._listener.daemon = True
        self._listener.start()

    def stop(self):
        self.is_running = False
        with self._lock:
            self._pressed_keys.clear()
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None

    def toggle(self) -> bool:
        if self.is_running:
            self.stop()
        else:
            self.start()
        return self.is_running

    def _on_press(self, key):
        if not self.is_running:
            return

        # Suppress OS typematic auto-repeat when holding down a key.
        # Only the initial keydown event produces sound.
        key_id = self._get_key_id(key)
        with self._lock:
            if key_id in self._pressed_keys:
                return
            self._pressed_keys.add(key_id)

        sound_type = "default"
        key_name = "Key"
        char_key = None

        # Categorize key and identify specific audio mappings
        if key == Key.space:
            sound_type = "space"
            key_name = "SPACE"
        elif key in (Key.enter, getattr(Key, "num_enter", Key.enter)):
            sound_type = "enter"
            key_name = "ENTER"
        elif key == Key.backspace:
            sound_type = "backspace"
            key_name = "BACKSPACE"
        elif key in (Key.shift, getattr(Key, "shift_l", Key.shift), getattr(Key, "shift_r", Key.shift)):
            sound_type = "shift"
            key_name = "SHIFT"
        elif key == Key.tab:
            sound_type = "tab"
            key_name = "TAB"
        elif key == Key.caps_lock:
            sound_type = "capslock"
            key_name = "CAPS"
        elif isinstance(key, KeyCode) and key.char:
            key_name = key.char.upper()
            char_key = key.char.lower()
        elif hasattr(key, "name"):
            key_name = key.name.upper()

        # Trigger audio playback immediately with zero latency
        self.sound_manager.play_key(sound_type, key=key, char_key=char_key)

        # Notify GUI asynchronously
        if self.on_key_event:
            self.on_key_event(key_name)

    def _on_release(self, key):
        """Frees key from pressed set when physically lifted."""
        key_id = self._get_key_id(key)
        with self._lock:
            self._pressed_keys.discard(key_id)


def create_tray_image(width=64, height=64) -> Image.Image:
    """Generates a sleek, high-DPI keyboard keycap icon for the system tray."""
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Keycap base bevel (Dark metallic gray)
    draw.rounded_rectangle([4, 6, width - 4, height - 6], radius=10, fill=(35, 39, 46))
    # Keycap top surface (Cyan/Blue accent top)
    draw.rounded_rectangle([10, 10, width - 10, height - 12], radius=7, fill=(45, 55, 72))
    # Key legend / mechanical switch stem cross
    cx, cy = width // 2, height // 2 - 2
    accent_color = (56, 189, 248)  # Electric sky blue
    # Stem center
    draw.rectangle([cx - 4, cy - 10, cx + 4, cy + 10], fill=accent_color)
    draw.rectangle([cx - 10, cy - 4, cx + 10, cy + 4], fill=accent_color)

    return image


class MechanicalKeyboardApp(ctk.CTk):
    """Main application window and controller with cascading brand & model selectors."""

    def __init__(self):
        super().__init__()

        # Window Configuration
        self.title("Mechanical Keyboard Audio Simulator")
        self.geometry("490x600")
        self.resizable(False, False)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Audio and Background Services
        self.sound_manager = SoundManager(SOUNDS_DIR)
        self.listener_service = KeyboardListenerService(
            sound_manager=self.sound_manager,
            on_key_event=self._on_key_detected,
        )

        # Stats tracking
        self.stroke_count = 0
        self.last_key_name = "-"

        # System Tray State
        self.tray_icon: Optional[pystray.Icon] = None
        self._is_quitting = False

        # Build Interface
        self._build_ui()

        # Initialize Default Brand & Model
        self._initialize_brand_and_model()

        # Start Keyboard Listener by default
        self.listener_service.start()
        self._update_status_ui(True)

        # Intercept window close to minimize to tray
        self.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)

        # Initialize System Tray in background thread
        self._init_system_tray()

    def _build_ui(self):
        """Constructs the modern customtkinter layout with cascading selectors."""
        self.main_frame = ctk.CTkFrame(self, corner_radius=16, fg_color="#18181b")
        self.main_frame.pack(fill="both", expand=True, padx=16, pady=16)

        # Top Bar: Header and Status Pill
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=16, pady=(16, 4))

        title_label = ctk.CTkLabel(
            header_frame,
            text="Mechanical Audio",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#f4f4f5",
        )
        title_label.pack(side="left")

        self.status_pill = ctk.CTkLabel(
            header_frame,
            text="● LISTENING",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#22c55e",
            fg_color="#14532d",
            corner_radius=12,
            padx=10,
            pady=3,
        )
        self.status_pill.pack(side="right")

        # Engine Badge
        engine_badge = ctk.CTkLabel(
            self.main_frame,
            text="⚡ DirectSound Engine (128 Buffer • Studio Mechanical Packs)",
            font=ctk.CTkFont(size=11),
            text_color="#71717a",
        )
        engine_badge.pack(pady=(0, 12))

        # Live Keystroke Visualizer Card
        visualizer_card = ctk.CTkFrame(
            self.main_frame, corner_radius=12, fg_color="#27272a", border_width=1, border_color="#3f3f46"
        )
        visualizer_card.pack(fill="x", padx=16, pady=(0, 14))

        vis_header = ctk.CTkLabel(
            visualizer_card,
            text="LIVE KEYSTROKE MONITOR",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#a1a1aa",
        )
        vis_header.pack(pady=(8, 2))

        self.key_display = ctk.CTkLabel(
            visualizer_card,
            text="PRESS ANY KEY",
            font=ctk.CTkFont(size=22, weight="bold", family="Consolas"),
            text_color="#38bdf8",
        )
        self.key_display.pack(pady=(0, 4))

        self.counter_label = ctk.CTkLabel(
            visualizer_card,
            text="Total Keystrokes: 0",
            font=ctk.CTkFont(size=11),
            text_color="#a1a1aa",
        )
        self.counter_label.pack(pady=(0, 8))

        # Brand Selector Section
        brand_label = ctk.CTkLabel(
            self.main_frame,
            text="1. Select Brand / Soundpack",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#e4e4e7",
            anchor="w",
        )
        brand_label.pack(fill="x", padx=18, pady=(2, 2))

        self.brand_dropdown = ctk.CTkOptionMenu(
            self.main_frame,
            values=["Loading..."],
            command=self._on_brand_selected,
            font=ctk.CTkFont(size=13),
            fg_color="#2563eb",
            button_color="#1d4ed8",
            button_hover_color="#1e40af",
            dropdown_fg_color="#27272a",
            dropdown_hover_color="#3f3f46",
            height=34,
            corner_radius=8,
        )
        self.brand_dropdown.pack(fill="x", padx=16, pady=(0, 10))

        # Model Selector Section
        model_label = ctk.CTkLabel(
            self.main_frame,
            text="2. Select Switch Model",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#e4e4e7",
            anchor="w",
        )
        model_label.pack(fill="x", padx=18, pady=(2, 2))

        self.model_dropdown = ctk.CTkOptionMenu(
            self.main_frame,
            values=["Loading..."],
            command=self._on_model_selected,
            font=ctk.CTkFont(size=13),
            fg_color="#0284c7",
            button_color="#0369a1",
            button_hover_color="#075985",
            dropdown_fg_color="#27272a",
            dropdown_hover_color="#3f3f46",
            height=34,
            corner_radius=8,
        )
        self.model_dropdown.pack(fill="x", padx=16, pady=(0, 16))

        # Volume Section
        vol_header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        vol_header_frame.pack(fill="x", padx=18, pady=(0, 2))

        volume_label = ctk.CTkLabel(
            vol_header_frame,
            text="Master Volume",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#e4e4e7",
        )
        volume_label.pack(side="left")

        self.volume_val_label = ctk.CTkLabel(
            vol_header_frame,
            text="80%",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#38bdf8",
        )
        self.volume_val_label.pack(side="right")

        self.volume_slider = ctk.CTkSlider(
            self.main_frame,
            from_=0.0,
            to=1.0,
            number_of_steps=100,
            command=self._on_volume_changed,
            button_color="#38bdf8",
            button_hover_color="#0284c7",
            progress_color="#3b82f6",
            height=16,
        )
        self.volume_slider.set(0.8)
        self.volume_slider.pack(fill="x", padx=16, pady=(0, 18))

        # Start / Stop Toggle Button
        self.toggle_btn = ctk.CTkButton(
            self.main_frame,
            text="Stop Keyboard Listener",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._toggle_listener,
            fg_color="#ef4444",
            hover_color="#dc2626",
            height=40,
            corner_radius=10,
        )
        self.toggle_btn.pack(fill="x", padx=16, pady=(0, 10))

        # Secondary Actions
        secondary_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        secondary_frame.pack(fill="x", padx=16, pady=(2, 6))

        self.minimize_btn = ctk.CTkButton(
            secondary_frame,
            text="Minimize to Tray",
            command=self.minimize_to_tray,
            fg_color="#3f3f46",
            hover_color="#52525b",
            font=ctk.CTkFont(size=12),
            height=32,
            corner_radius=8,
        )
        self.minimize_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.folder_btn = ctk.CTkButton(
            secondary_frame,
            text="Open Sounds Folder",
            command=self._open_sounds_folder,
            fg_color="#27272a",
            hover_color="#3f3f46",
            border_width=1,
            border_color="#52525b",
            font=ctk.CTkFont(size=12),
            height=32,
            corner_radius=8,
        )
        self.folder_btn.pack(side="right", fill="x", expand=True, padx=(6, 0))

    def _initialize_brand_and_model(self):
        brands = self.sound_manager.get_brands()
        if not brands:
            return

        self.brand_dropdown.configure(values=brands)
        # Select Deep Thock by default if available
        initial_brand = "Deep Thock" if "Deep Thock" in brands else ("Mechvibes" if "Mechvibes" in brands else brands[0])
        self.brand_dropdown.set(initial_brand)

        models = self.sound_manager.get_models_for_brand(initial_brand)
        if models:
            self.model_dropdown.configure(values=models)
            initial_model = models[0]
            self.model_dropdown.set(initial_model)
            self.sound_manager.load_model(initial_brand, initial_model)

    def _on_brand_selected(self, selected_brand: str):
        models = self.sound_manager.get_models_for_brand(selected_brand)
        if models:
            self.model_dropdown.configure(values=models)
            first_model = models[0]
            self.model_dropdown.set(first_model)
            self.sound_manager.load_model(selected_brand, first_model)
        else:
            self.model_dropdown.configure(values=["No models found"])
            self.model_dropdown.set("No models found")

    def _on_model_selected(self, selected_model: str):
        current_brand = self.brand_dropdown.get()
        self.sound_manager.load_model(current_brand, selected_model)

    def _on_key_detected(self, key_name: str):
        self.stroke_count += 1
        self.last_key_name = key_name
        self.after(0, self._refresh_key_ui)

    def _refresh_key_ui(self):
        self.key_display.configure(text=f"[ {self.last_key_name} ]")
        self.counter_label.configure(text=f"Total Keystrokes: {self.stroke_count}")

    def _on_volume_changed(self, value: float):
        self.sound_manager.apply_volume(value)
        self.volume_val_label.configure(text=f"{int(value * 100)}%")

    def _toggle_listener(self):
        is_active = self.listener_service.toggle()
        self._update_status_ui(is_active)

    def _update_status_ui(self, is_active: bool):
        if is_active:
            self.status_pill.configure(
                text="● LISTENING",
                text_color="#22c55e",
                fg_color="#14532d",
            )
            self.toggle_btn.configure(
                text="Stop Keyboard Listener",
                fg_color="#ef4444",
                hover_color="#dc2626",
            )
        else:
            self.status_pill.configure(
                text="○ PAUSED",
                text_color="#f87171",
                fg_color="#450a0a",
            )
            self.toggle_btn.configure(
                text="Start Keyboard Listener",
                fg_color="#22c55e",
                hover_color="#16a34a",
            )

    def _open_sounds_folder(self):
        os.makedirs(SOUNDS_DIR, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(SOUNDS_DIR)
        elif sys.platform == "darwin":
            os.system(f'open "{SOUNDS_DIR}"')
        else:
            os.system(f'xdg-open "{SOUNDS_DIR}"')

    def _init_system_tray(self):
        tray_image = create_tray_image()

        menu = pystray.Menu(
            pystray.MenuItem("Show Window", self._tray_show_window, default=True),
            pystray.MenuItem("Toggle Keyboard Listener", self._tray_toggle_listener),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self._tray_quit_app),
        )

        self.tray_icon = pystray.Icon(
            "MechanicalKeyboardSimulator",
            tray_image,
            "Mechanical Keyboard Audio",
            menu,
        )

        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def minimize_to_tray(self):
        self.withdraw()

    def show_window(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def _tray_show_window(self, icon=None, item=None):
        self.after(0, self.show_window)

    def _tray_toggle_listener(self, icon=None, item=None):
        self.after(0, self._toggle_listener)

    def _tray_quit_app(self, icon=None, item=None):
        self._is_quitting = True
        self.listener_service.stop()

        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass

        try:
            pygame.mixer.quit()
        except Exception:
            pass

        self.after(0, self._safe_destroy)

    def _safe_destroy(self):
        self.quit()
        self.destroy()


def main():
    app = MechanicalKeyboardApp()
    app.mainloop()


if __name__ == "__main__":
    main()
