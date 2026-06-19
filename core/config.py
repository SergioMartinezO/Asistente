import json
import os
import sys
from pathlib import Path
from google import genai

_base_dir_cache = None

def get_base_dir() -> Path:
    global _base_dir_cache
    if _base_dir_cache is not None:
        return _base_dir_cache
    if getattr(sys, "frozen", False):
        _base_dir_cache = Path(sys.executable).parent
    else:
        # __file__ is in core/config.py, its parent is core/, grandparent is the root
        _base_dir_cache = Path(__file__).resolve().parent.parent
    return _base_dir_cache

BASE_DIR = get_base_dir()
CONFIG_DIR = BASE_DIR / "config"
API_FILE = CONFIG_DIR / "api_keys.json"

_config_cache = None

def load_config() -> dict:
    global _config_cache
    if _config_cache is not None:
        return _config_cache
    if not API_FILE.exists():
        return {}
    try:
        _config_cache = json.loads(API_FILE.read_text(encoding="utf-8"))
        return _config_cache
    except Exception:
        return {}

def save_config(api_key: str, os_name: str):
    global _config_cache
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config_data = {"gemini_api_key": api_key, "os_system": os_name}
    API_FILE.write_text(json.dumps(config_data, indent=4), encoding="utf-8")
    _config_cache = config_data

def get_api_key() -> str:
    return load_config().get("gemini_api_key", "")

def get_os_system() -> str:
    return load_config().get("os_system", "windows").lower()

_client_cache = None

def get_gemini_client() -> genai.Client:
    global _client_cache
    if _client_cache is not None:
        return _client_cache
    api_key = get_api_key()
    _client_cache = genai.Client(
        api_key=api_key or os.environ.get("GEMINI_API_KEY", ""),
        http_options={"api_version": "v1beta"}
    )
    return _client_cache

def reset_client():
    global _client_cache, _config_cache
    _client_cache = None
    _config_cache = None

class _GenaiMock:
    @staticmethod
    def configure(*args, **kwargs):
        pass

    @staticmethod
    def GenerativeModel(model_name: str = "gemini-2.5-flash", system_instruction: str = None):
        class GenerativeModelWrapper:
            def __init__(self, m_name, sys_inst):
                self.m_name = m_name
                # Map old models to new ones if necessary
                if "lite" in m_name:
                    self.m_name = "gemini-2.5-flash"
                elif "gemini-2.0" in m_name:
                    self.m_name = "gemini-2.5-flash"
                self.sys_inst = sys_inst
                self.client = get_gemini_client()

            def generate_content(self, contents, **kwargs):
                config = {}
                if self.sys_inst:
                    config["system_instruction"] = self.sys_inst
                
                # Check for config parameter and map it
                if "config" in kwargs:
                    config.update(kwargs["config"])

                return self.client.models.generate_content(
                    model=self.m_name,
                    contents=contents,
                    config=config
                )
        return GenerativeModelWrapper(model_name, system_instruction)

genai_legacy = _GenaiMock()
