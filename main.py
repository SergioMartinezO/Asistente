
import asyncio
import re
import threading
import json
import sys
import traceback
from pathlib import Path
import numpy as np
# import sounddevice as sd # Removed, as it's handled in controller.py and might not be needed directly here
import google.genai as genai
from google.genai import types

from ui import JarvisUI
from memory.memory_manager import load_memory, update_memory, format_memory_for_prompt
from memory.conversation_history import save_session, format_history_for_prompt

# Módulos de Acciones
from actions.file_processor import file_processor
from actions.flight_finder import flight_finder
from actions.electronics import electronics
from actions.dev_tools import dev_tools
from actions.mechatronics import mechatronics
from actions.open_app import open_app
from actions.weather_report import weather_action
# Conditional import for send_message to avoid DISPLAY error
try:
    from actions.send_message import send_message
    HAS_SEND_MESSAGE = True
except (ImportError, KeyError) as e:
    print(f"[WARNING] Could not import send_message due to display issues: {e}. 'send_message' action will be disabled.")
    send_message = None
    HAS_SEND_MESSAGE = False

from actions.reminder import reminder
# Conditional import for computer_settings to avoid DISPLAY error
try:
    from actions.computer_settings import computer_settings
    HAS_COMPUTER_SETTINGS = True
except (ImportError, KeyError) as e:
    print(f"[WARNING] Could not import computer_settings due to display issues: {e}. 'computer_settings' action will be disabled.")
    computer_settings = None
    HAS_COMPUTER_SETTINGS = False

# Conditional import for screen_processor to avoid DISPLAY error
try:
    from actions.screen_processor import screen_process
    HAS_SCREEN_PROCESSOR = True
except (ImportError, KeyError) as e:
    print(f"[WARNING] Could not import screen_processor due to display issues: {e}. 'screen_process' action will be disabled.")
    screen_process = None
    HAS_SCREEN_PROCESSOR = False

# Conditional import for youtube_video to avoid DISPLAY error
try:
    from actions.youtube_video import youtube_video
    HAS_YOUTUBE_VIDEO = True
except (ImportError, KeyError) as e:
    print(f"[WARNING] Could not import youtube_video due to display issues: {e}. 'youtube_video' action will be disabled.")
    youtube_video = None
    HAS_YOUTUBE_VIDEO = False

# Conditional import for desktop_control to avoid DISPLAY error
try:
    from actions.desktop import desktop_control
    HAS_DESKTOP_CONTROL = True
except (ImportError, KeyError) as e:
    print(f"[WARNING] Could not import desktop_control due to display issues: {e}. 'desktop_control' action will be disabled.")
    desktop_control = None
    HAS_DESKTOP_CONTROL = False

# Conditional import for browser_control to avoid DISPLAY error
try:
    from actions.browser_control import browser_control
    HAS_BROWSER_CONTROL = True
except (ImportError, KeyError) as e:
    print(f"[WARNING] Could not import browser_control due to display issues: {e}. 'browser_control' action will be disabled.")
    browser_control = None
    HAS_BROWSER_CONTROL = False

# Conditional import for file_controller to avoid DISPLAY error
try:
    from actions.file_controller import file_controller
    HAS_FILE_CONTROLLER = True
except (ImportError, KeyError) as e:
    print(f"[WARNING] Could not import file_controller due to display issues: {e}. 'file_controller' action will be disabled.")
    file_controller = None
    HAS_FILE_CONTROLLER = False

from actions.code_helper import code_helper
from actions.dev_agent import dev_agent
from actions.web_search import web_search as web_search_action

# Conditional import for computer_control to avoid DISPLAY error
try:
    from actions.computer_control import computer_control
    HAS_COMPUTER_CONTROL = True
except (ImportError, KeyError) as e:
    print(f"[WARNING] Could not import computer_control due to display issues: {e}. 'computer_control' action will be disabled.")
    computer_control = None
    HAS_COMPUTER_CONTROL = False

from actions.game_updater import game_updater
from actions.datasheet_finder import datasheet_finder
from actions.materials_science import materials_science

# Conditional import for proteus_automation to avoid DISPLAY error
try:
    from actions.proteus_automation import proteus_automation
    HAS_PROTEUS_AUTOMATION = True
except (ImportError, KeyError) as e:
    print(f"[WARNING] Could not import proteus_automation due to display issues: {e}. 'proteus_automation' action will be disabled.")
    proteus_automation = None
    HAS_PROTEUS_AUTOMATION = False

# Conditional import for ltspice_automation to avoid DISPLAY error
try:
    from actions.ltspice_automation import ltspice_automation
    HAS_LTSPICE_AUTOMATION = True
except (ImportError, KeyError) as e:
    print(f"[WARNING] Could not import ltspice_automation due to display issues: {e}. 'ltspice_automation' action will be disabled.")
    ltspice_automation = None
    HAS_LTSPICE_AUTOMATION = False

def get_base_dir():
    # In Colab, __file__ might not be defined. Use Path.cwd() which should point to /content/Asistente
    # after the initial `!cd Asistente` command.
    return Path.cwd()

BASE_DIR = get_base_dir()
CONFIG_DIR = BASE_DIR / "config"
CORE_DIR = BASE_DIR / "core"
API_CONFIG_PATH = CONFIG_DIR / "api_keys.json"
PROMPT_PATH = CORE_DIR / "prompt.txt"
LIVE_MODEL = "models/gemini-2.5-flash-native-audio-preview-12-2025"

# Parámetros de Audio Optimizados
CHANNELS = 1
SEND_SAMPLE_RATE = 16_000
RECEIVE_SAMPLE_RATE = 24_000
CHUNK_SIZE = 4096

# Expresión regular para limpiar transcripciones
_CTRL_RE = re.compile(r"<ctrl\d+>", re.IGNORECASE)

def _clean_transcript(text: str) -> str:
    text = _CTRL_RE.sub("", text)
    text = re.sub(r"[\x00-\x08\x0b-\x1f]", "", text)
    return text.strip()


def _load_system_prompt() -> str:
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return "You are a helpful AI assistant."


# Declaraciones de herramientas para Gemini Live API (formato dict, no funciones Python).
from core.tool_declarations import TOOL_DECLARATIONS as _ALL_TOOL_DECLARATIONS

_EXCLUDED_TOOL_NAMES: set[str] = set()
if not HAS_SEND_MESSAGE:
    _EXCLUDED_TOOL_NAMES.add("send_message")
if not HAS_COMPUTER_SETTINGS:
    _EXCLUDED_TOOL_NAMES.add("computer_settings")
if not HAS_SCREEN_PROCESSOR:
    _EXCLUDED_TOOL_NAMES.add("screen_process")
if not HAS_YOUTUBE_VIDEO:
    _EXCLUDED_TOOL_NAMES.add("youtube_video")
if not HAS_DESKTOP_CONTROL:
    _EXCLUDED_TOOL_NAMES.add("desktop_control")
if not HAS_BROWSER_CONTROL:
    _EXCLUDED_TOOL_NAMES.add("browser_control")
if not HAS_FILE_CONTROLLER:
    _EXCLUDED_TOOL_NAMES.add("file_controller")
if not HAS_COMPUTER_CONTROL:
    _EXCLUDED_TOOL_NAMES.add("computer_control")
if not HAS_PROTEUS_AUTOMATION:
    _EXCLUDED_TOOL_NAMES.add("proteus_automation")
if not HAS_LTSPICE_AUTOMATION:
    _EXCLUDED_TOOL_NAMES.add("ltspice_automation")

TOOL_DECLARATIONS = [
    tool for tool in _ALL_TOOL_DECLARATIONS
    if tool.get("name") not in _EXCLUDED_TOOL_NAMES
]


def main():
    from model import JarvisModel
    from controller import JarvisController

    # 1. Crear Vista (JarvisUI)
    ui = JarvisUI("face.png")

    # 2. Crear Modelo (JarvisModel)
    model = JarvisModel()

    # 3. Crear Controlador (JarvisController) vinculando Vista y Modelo
    controller = JarvisController(model, ui)

    # 4. Hilo de ejecución para el loop asíncrono gestionado por el Controlador
    def runner():
        ui.wait_for_api_key()
        try:
            # Ensure the controller's run method is awaited correctly
            asyncio.run(controller.run())
        except KeyboardInterrupt:
            print("\n🔴 Shutting down...")
        except Exception as e:
            print(f"An error occurred in the controller runner: {e}")
            traceback.print_exc()

    threading.Thread(target=runner, daemon=True).start()
    ui.root.mainloop()

if __name__ == "__main__":
    main()
