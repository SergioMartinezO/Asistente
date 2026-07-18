"""
test_local_model.py
Prueba rápida: ¿el asistente le está hablando a Qwen local (Ollama)
o está cayendo al respaldo de Gemini?

Uso:
    python test_local_model.py
"""

from core.local_model import ping, load_model_config
from core.config import genai_legacy as genai

print("== Config actual ==")
cfg = load_model_config()
print(f"text_provider: {cfg['text_provider']}")
print(f"base_url:      {cfg['qwen_local']['base_url']}")
print(f"model_name:    {cfg['qwen_local']['model_name']}")
print()

print("== Ping a /v1/models ==")
print(f"Responde: {ping()}")
print()

print("== Prueba de generación ==")
model = genai.GenerativeModel("gemini-2.5-flash-lite")
response = model.generate_content("Responde solo con: funciona")
print(f"Respuesta: {response.text}")