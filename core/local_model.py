"""
core/local_model.py

Cliente para un modelo local (Qwen3.6 en F:\\blobs) servido mediante un
endpoint compatible con la API de OpenAI (LM Studio, llama.cpp server,
vLLM, text-generation-webui, Ollama con /v1, etc.).

Expone la MISMA interfaz que usa el resto del proyecto a través de
core.config.genai_legacy:

    model = <algo>.GenerativeModel(model_name, system_instruction=...)
    response = model.generate_content(prompt)
    response.text  -> str

De modo que actions/dev_agent.py, actions/code_helper.py,
actions/computer_settings.py, actions/desktop.py,
actions/youtube_video.py y actions/flight_finder.py NO necesitan
modificarse: solo cambia el "proveedor" en config/model_config.json.
"""

import json
import os
import threading
from pathlib import Path

import requests

_here = Path(__file__).resolve().parent.parent
MODEL_CONFIG_FILE = _here / "config" / "model_config.json"

_config_lock = threading.Lock()
_config_cache = None

_DEFAULT_CONFIG = {
    # "gemini" | "qwen_local"
    "text_provider": "qwen_local",
    "qwen_local": {
        # Ajusta esto según el servidor que uses para exponer F:\blobs:
        #   LM Studio           -> http://localhost:1234/v1
        #   llama.cpp (llama-server) -> http://localhost:8080/v1
        #   Ollama (con soporte /v1) -> http://localhost:11434/v1
        "base_url": "http://localhost:1234/v1",
        # Nombre EXACTO tal como lo reporta el servidor (ver /v1/models)
        "model_name": "qwen3.6-instruct",
        "timeout_seconds": 120,
        "temperature": 0.4,
        "max_tokens": 4096,
        # Si el servidor local falla (apagado, timeout, error), usar
        # Gemini como respaldo automático en vez de romper la ejecución.
        "fallback_to_gemini": True,
        "fallback_model": "gemini-2.5-flash",
    },
}


def load_model_config() -> dict:
    global _config_cache
    with _config_lock:
        if _config_cache is not None:
            return _config_cache
        if MODEL_CONFIG_FILE.exists():
            try:
                data = json.loads(MODEL_CONFIG_FILE.read_text(encoding="utf-8"))
                merged = {**_DEFAULT_CONFIG, **data}
                merged["qwen_local"] = {
                    **_DEFAULT_CONFIG["qwen_local"],
                    **data.get("qwen_local", {}),
                }
                _config_cache = merged
                return _config_cache
            except Exception:
                pass
        _config_cache = _DEFAULT_CONFIG
        return _config_cache


def reset_model_config_cache():
    global _config_cache
    with _config_lock:
        _config_cache = None


def get_text_provider() -> str:
    """'gemini' o 'qwen_local'. Variable de entorno REX_TEXT_PROVIDER tiene prioridad."""
    env_override = os.environ.get("REX_TEXT_PROVIDER")
    if env_override:
        return env_override.strip().lower()
    return load_model_config().get("text_provider", "gemini").lower()


class _LocalResponse:
    """Imita la interfaz .text de _ResponseWrapper (core/config.py)."""

    def __init__(self, text: str):
        self._text = text or ""

    @property
    def text(self) -> str:
        return self._text


class QwenLocalGenerativeModel:
    """
    Reemplazo de core.config._GenaiMock.GenerativeModel() que habla con
    un servidor OpenAI-compatible sirviendo Qwen3.6 desde F:\\blobs.
    """

    def __init__(self, model_name: str = None, system_instruction: str = None):
        cfg = load_model_config()["qwen_local"]
        self.cfg = cfg
        self.system_instruction = system_instruction
        # Se ignora el model_name de Gemini que pida el código original
        # (ej. "gemini-2.5-flash-lite"); se usa siempre el modelo local
        # configurado, salvo que el que llama pase uno explícito distinto
        # a los nombres típicos de Gemini.
        if model_name and "gemini" not in model_name.lower():
            self.model_name = model_name
        else:
            self.model_name = cfg["model_name"]

    def generate_content(self, contents, **kwargs):
        prompt_text = self._contents_to_text(contents)

        messages = []
        if self.system_instruction:
            messages.append({"role": "system", "content": self.system_instruction})
        messages.append({"role": "user", "content": prompt_text})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.cfg.get("temperature", 0.4),
            "max_tokens": self.cfg.get("max_tokens", 4096),
        }

        url = self.cfg["base_url"].rstrip("/") + "/chat/completions"

        try:
            r = requests.post(
                url,
                json=payload,
                timeout=self.cfg.get("timeout_seconds", 120),
            )
            if not r.ok:
                # Loguear el cuerpo real del error (Ollama suele decir
                # "model 'X' not found" aquí) en vez de solo el status code.
                raise RuntimeError(f"{r.status_code} en {url}: {r.text[:500]}")
            data = r.json()
            text = data["choices"][0]["message"]["content"]
            return _LocalResponse(text)
        except Exception as e:
            if self.cfg.get("fallback_to_gemini", True):
                print(f"[REX] ⚠️ Qwen local no disponible ({e}). Usando Gemini de respaldo.")
                return self._fallback_gemini(prompt_text)
            raise

    def _fallback_gemini(self, prompt_text: str):
        from core.config import get_gemini_client

        client = get_gemini_client()
        fallback_model = self.cfg.get("fallback_model", "gemini-2.5-flash-lite")
        config = {}
        if self.system_instruction:
            config["system_instruction"] = self.system_instruction
        response = client.models.generate_content(
            model=fallback_model,
            contents=prompt_text,
            config=config,
        )
        return response

    @staticmethod
    def _contents_to_text(contents) -> str:
        """El resto del proyecto solo pasa strings, pero por robustez
        soportamos listas simples de strings también."""
        if isinstance(contents, str):
            return contents
        if isinstance(contents, (list, tuple)):
            return "\n".join(str(c) for c in contents)
        return str(contents)


def ping() -> bool:
    """Comprueba si el servidor local de Qwen responde (para diagnósticos)."""
    cfg = load_model_config()["qwen_local"]
    url = cfg["base_url"].rstrip("/") + "/models"
    try:
        r = requests.get(url, timeout=5)
        return r.ok
    except Exception:
        return False