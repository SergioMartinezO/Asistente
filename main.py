from core.tool_declarations import TOOL_DECLARATIONS as _ALL_TOOL_DECLARATIONS
from actions.materials_science import materials_science
from actions.datasheet_finder import datasheet_finder
from actions.game_updater import game_updater
from actions.web_search import web_search as web_search_action
from actions.dev_agent import dev_agent
from actions.code_helper import code_helper
from actions.reminder import reminder
from actions.weather_report import weather_action
from actions.open_app import open_app
from actions.mechatronics import mechatronics
from actions.dev_tools import dev_tools
from actions.electronics import electronics
from actions.flight_finder import flight_finder
from actions.file_processor import file_processor
from memory.conversation_history import save_session, format_history_for_prompt
from memory.memory_manager import load_memory, update_memory, format_memory_for_prompt
from ui import RexUI
from core.dependency_check import check_project_dependencies, build_install_command
from google.genai import types
import google.genai as genai
import asyncio
import re
import threading
import json
import sys
import os
import traceback
from pathlib import Path
import numpy as np
import shutil
import atexit

# ── DPI / Qt: debe estar ANTES de cualquier import de PyQt6 ──────────────────
# Evita "SetProcessDpiAwarenessContext() failed: Acceso denegado" en Windows.
# Qt6 fija DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 por defecto; si otro
# componente (p.ej. el runtime de Python) ya llamó SetProcessDpiAwareness,
# el segundo intento de Qt falla con Access Denied. Desactivar el escalado
# automático elimina ese segundo intento sin perder nitidez en monitores HiDPI.
if sys.platform.startswith("win"):
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
    os.environ["QT_SCALE_FACTOR"] = "1"
# ─────────────────────────────────────────────────────────────────────────────

# Evita que Python escriba archivos .pyc o carpetas __pycache__ durante esta ejecución
sys.dont_write_bytecode = True


# Módulos de Acciones
# Conditional import for send_message to avoid DISPLAY error
try:
    from actions.send_message import send_message
    HAS_SEND_MESSAGE = True
except (ImportError, KeyError) as e:
    print(
        f"[WARNING] Could not import send_message due to display issues: {e}. 'send_message' action will be disabled.")
    send_message = None
    HAS_SEND_MESSAGE = False

# Conditional import for computer_settings to avoid DISPLAY error
try:
    from actions.computer_settings import computer_settings
    HAS_COMPUTER_SETTINGS = True
except (ImportError, KeyError) as e:
    print(
        f"[WARNING] Could not import computer_settings due to display issues: {e}. 'computer_settings' action will be disabled.")
    computer_settings = None
    HAS_COMPUTER_SETTINGS = False

# Conditional import for screen_processor to avoid DISPLAY error
try:
    from actions.screen_processor import screen_process
    HAS_SCREEN_PROCESSOR = True
except (ImportError, KeyError) as e:
    print(
        f"[WARNING] Could not import screen_processor due to display issues: {e}. 'screen_process' action will be disabled.")
    screen_process = None
    HAS_SCREEN_PROCESSOR = False

# Conditional import for youtube_video to avoid DISPLAY error
try:
    from actions.youtube_video import youtube_video
    HAS_YOUTUBE_VIDEO = True
except (ImportError, KeyError) as e:
    print(
        f"[WARNING] Could not import youtube_video due to display issues: {e}. 'youtube_video' action will be disabled.")
    youtube_video = None
    HAS_YOUTUBE_VIDEO = False

# Conditional import for desktop_control to avoid DISPLAY error
try:
    from actions.desktop import desktop_control
    HAS_DESKTOP_CONTROL = True
except (ImportError, KeyError) as e:
    print(
        f"[WARNING] Could not import desktop_control due to display issues: {e}. 'desktop_control' action will be disabled.")
    desktop_control = None
    HAS_DESKTOP_CONTROL = False

# Conditional import for browser_control to avoid DISPLAY error
try:
    from actions.browser_control import browser_control
    HAS_BROWSER_CONTROL = True
except (ImportError, KeyError) as e:
    print(
        f"[WARNING] Could not import browser_control due to display issues: {e}. 'browser_control' action will be disabled.")
    browser_control = None
    HAS_BROWSER_CONTROL = False

# Conditional import for file_controller to avoid DISPLAY error
try:
    from actions.file_controller import file_controller
    HAS_FILE_CONTROLLER = True
except (ImportError, KeyError) as e:
    print(
        f"[WARNING] Could not import file_controller due to display issues: {e}. 'file_controller' action will be disabled.")
    file_controller = None
    HAS_FILE_CONTROLLER = False


# Conditional import for computer_control to avoid DISPLAY error
try:
    from actions.computer_control import computer_control
    HAS_COMPUTER_CONTROL = True
except (ImportError, KeyError) as e:
    print(
        f"[WARNING] Could not import computer_control due to display issues: {e}. 'computer_control' action will be disabled.")
    computer_control = None
    HAS_COMPUTER_CONTROL = False


# Conditional import for proteus_automation to avoid DISPLAY error
try:
    from actions.proteus_automation import proteus_automation
    HAS_PROTEUS_AUTOMATION = True
except (ImportError, KeyError) as e:
    print(
        f"[WARNING] Could not import proteus_automation due to display issues: {e}. 'proteus_automation' action will be disabled.")
    proteus_automation = None
    HAS_PROTEUS_AUTOMATION = False

# Conditional import for ltspice_automation to avoid DISPLAY error
try:
    from actions.ltspice_automation import ltspice_automation
    HAS_LTSPICE_AUTOMATION = True
except (ImportError, KeyError) as e:
    print(
        f"[WARNING] Could not import ltspice_automation due to display issues: {e}. 'ltspice_automation' action will be disabled.")
    ltspice_automation = None
    HAS_LTSPICE_AUTOMATION = False


def get_base_dir() -> Path:
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


def limpiar_cache_al_salir():
    """Busca y elimina recursivamente directorios __pycache__ al finalizar el programa."""
    try:
        for raiz, directorios, _ in os.walk(str(BASE_DIR)):
            for directorio in directorios:
                if directorio == "__pycache__":
                    ruta_completa = os.path.join(raiz, directorio)
                    try:
                        shutil.rmtree(ruta_completa)
                    except Exception:
                        pass  # Silenciar excepciones de archivos bloqueados temporalmente
    except Exception:
        pass


# Registro de la función de desecho en el ciclo de vida del proceso
atexit.register(limpiar_cache_al_salir)


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
    from model import RexModel
    from controller import RexController

    # 1. Crear Vista (RexUI)
    ui = RexUI("face.png")

    # 2. Crear Modelo (RexModel)
    model = RexModel()

    # 2.1 Autochequeo de dependencias del proyecto (aviso en UI, sin abortar inicio)
    missing = check_project_dependencies(BASE_DIR / "requirements.txt")
    if missing:
        ui.write_log("ERR: Dependencias faltantes detectadas al iniciar.")
        for dep in missing:
            ui.write_log(f"ERR: - {dep.package} (import: {dep.import_name})")

        install_cmd = build_install_command(
            [d.package for d in missing], sys.executable)
        if install_cmd:
            ui.write_log("SYS: Para corregirlo, instala con este comando:")
            ui.write_log(f"SYS: {install_cmd}")

        ui.update_activity(
            estado="Error",
            progreso=0,
            evento="Dependencias faltantes detectadas"
        )

        try:
            from PyQt6.QtWidgets import QMessageBox, QApplication
            detail = "\n".join(
                f"- {d.package} (import: {d.import_name})" for d in missing)
            box = QMessageBox(ui._win)
            box.setIcon(QMessageBox.Icon.Warning)
            box.setWindowTitle("Dependencias faltantes")
            box.setText(
                "Faltan dependencias de Python para algunas funciones de REX.")
            box.setInformativeText(detail)
            if install_cmd:
                box.setDetailedText(f"Comando sugerido:\n{install_cmd}")
                copy_btn = box.addButton(
                    "Copiar comando", QMessageBox.ButtonRole.ActionRole)
            else:
                copy_btn = None
            close_btn = box.addButton(
                "Cerrar", QMessageBox.ButtonRole.AcceptRole)
            box.setDefaultButton(close_btn)
            box.exec()

            if copy_btn is not None and box.clickedButton() == copy_btn:
                app = QApplication.instance()
                if isinstance(app, QApplication):
                    clipboard = app.clipboard()
                    if clipboard is not None:
                        clipboard.setText(install_cmd)
                        ui.write_log(
                            "SYS: Comando de instalación copiado al portapapeles.")
        except Exception:
            pass
    else:
        ui.write_log("SYS: Autochequeo de dependencias completado: OK")

    # 3. Crear Controlador (RexController) vinculando Vista y Modelo
    controller = RexController(model, ui)

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
