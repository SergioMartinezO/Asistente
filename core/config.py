import json
import os
import sys
import warnings
from pathlib import Path
from google import genai

# El SDK puede emitir este warning cuando alguien accede a response.text en
# respuestas mixtas (text/thought). Aquí ya usamos extracción segura en
# _safe_response_text, por lo que silenciamos el warning para evitar ruido.
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message=r".*non-data parts in the response.*",
)


def _safe_response_text(response) -> str:
    """Extrae texto sin usar response.text (evita warning por non-data parts)."""
    chunks: list[str] = []
    try:
        candidates = getattr(response, "candidates", None) or []
        for cand in candidates:
            content = getattr(cand, "content", None)
            if content is None:
                continue
            parts = getattr(content, "parts", None) or []
            for part in parts:
                txt = getattr(part, "text", None)
                if isinstance(txt, str) and txt.strip():
                    chunks.append(txt)
    except Exception:
        pass
    return "\n".join(chunks).strip()


def _describe_response_parts(response) -> str:
    """Describe tipos de partes presentes para diagnóstico rápido."""
    kinds: list[str] = []
    try:
        candidates = getattr(response, "candidates", None) or []
        for cand in candidates:
            content = getattr(cand, "content", None)
            if content is None:
                continue
            parts = getattr(content, "parts", None) or []
            for part in parts:
                if getattr(part, "text", None):
                    kinds.append("text")
                if getattr(part, "thought", None):
                    kinds.append("thought")
                if getattr(part, "inline_data", None):
                    kinds.append("inline_data")
                if getattr(part, "function_call", None):
                    kinds.append("function_call")
                if getattr(part, "function_response", None):
                    kinds.append("function_response")
    except Exception:
        return "unknown"

    if not kinds:
        return "none"
    return ",".join(sorted(set(kinds)))


class _ResponseWrapper:
    """Wrapper de respuesta para exponer .text sin activar warning de la librería."""

    def __init__(self, raw_response):
        self._raw = raw_response

    @property
    def text(self) -> str:
        text = _safe_response_text(self._raw)
        if not text and os.environ.get("REX_LOG_EMPTY_GENAI", "0") == "1":
            model = getattr(self._raw, "model_version", None) or "unknown-model"
            parts = _describe_response_parts(self._raw)
            print(f"[REX] ⚠️ Respuesta Gemini sin texto extraíble (model={model}, parts={parts})")
        return text

    def __getattr__(self, item):
        return getattr(self._raw, item)


class _ModelsWrapper:
    def __init__(self, raw_models):
        self._raw_models = raw_models

    def generate_content(self, *args, **kwargs):
        raw = self._raw_models.generate_content(*args, **kwargs)
        return _ResponseWrapper(raw)

    def __getattr__(self, item):
        return getattr(self._raw_models, item)


class _ClientWrapper:
    """Wrapper de cliente para normalizar respuestas de models.generate_content."""

    def __init__(self, raw_client):
        self._raw = raw_client
        self.models = _ModelsWrapper(raw_client.models)

    def __getattr__(self, item):
        return getattr(self._raw, item)

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
    raw_client = genai.Client(
        api_key=api_key or os.environ.get("GEMINI_API_KEY", ""),
        http_options={"api_version": "v1beta"}
    )
    _client_cache = _ClientWrapper(raw_client)
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
