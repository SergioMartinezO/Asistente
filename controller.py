# Al inicio de controller.py:

import asyncio
import re
import threading
import traceback
import os
import time
from collections import deque
from pathlib import Path
import sounddevice as sd
import google.genai as genai
from google.genai import types
from agent.voice_queue import get_voice_queue, shutdown_voice_queue
from ui import RexUI
from model import RexModel
from core.config import get_gemini_client
from core.output_policy import get_report_base, normalize_tool_outputs

# Importar las declaraciones de herramientas
from main import TOOL_DECLARATIONS, _load_system_prompt

LIVE_MODEL = "models/gemini-2.5-flash-native-audio-preview-12-2025"
CHANNELS = 1
SEND_SAMPLE_RATE = 16_000
RECEIVE_SAMPLE_RATE = 24_000
CHUNK_SIZE = 1024
PLAYBACK_BLOCKSIZE = 2048
REPORT_BASE_DIR = Path(r"D:\IA\Asistente\Report")

_CTRL_RE = re.compile(r"<ctrl\d+>", re.IGNORECASE)
_HONORIFIC_RE = re.compile(
    r"\b(?:sir|ma'am|madam)\b[\s,.:;!?-]*", re.IGNORECASE)


def _clean_transcript(text: str) -> str:
    text = _CTRL_RE.sub("", text)
    text = re.sub(r"[\x00-\x08\x0b-\x1f]", "", text)
    return text.strip()


class RexController:
    def __init__(self, model: RexModel, ui: RexUI):
        self.model = model
        self.ui = ui
        self.session = None
        self.audio_in_queue = None
        self.out_queue = None
        self._loop = None
        self._main_loop = None  # Referencia al event loop principal
        self._is_speaking = False
        self._speaking_lock = threading.Lock()
        self._turn_done_event = None
        self._retry_count = 0
        self._pending_web_search = None
        self._awaiting_confirmation = False
        self._confirmation_timeout = None
        self._web_search_executed = False
        self._current_progress = 0
        self._tool_counter = 0
        self._active_instruction = ""
        self._report_base = get_report_base()
        self._report_base.mkdir(parents=True, exist_ok=True)
        os.environ["REX_REPORT_DIR"] = str(self._report_base)
        self._shutdown_requested = False
        self._shutdown_lock = threading.Lock()
        self._live_diag_enabled = os.environ.get("REX_LIVE_DIAG", "0") == "1"
        self._strict_phases_enabled = os.environ.get(
            "REX_STRICT_PHASES", "0") == "1"
        self._strict_phases_failfast = os.environ.get(
            "REX_STRICT_PHASES_FAILFAST", "0") == "1"
        self._live_disconnect_ts = deque()
        self._live_disconnect_total = 0
        self._live_disconnect_code_counts = {}
        self._audio_input_enabled = True
        self._audio_input_disabled_reason = ""

        # Inicializar cola de voz para mensajes del executor
        self._voice_queue = get_voice_queue(
            speak_callback=self._speak_to_gemini)

        # Conectar callbacks de la Vista
        self.ui.on_text_command = self._on_text_command
        self.ui.on_permission_check = self._on_permission_check
        self.ui.on_setup_done = self._on_setup_done

        # Servicio de Ingeniería asíncrono para cálculos complejos
        from concurrent.futures import ThreadPoolExecutor
        self.engineering_executor = ThreadPoolExecutor(
            max_workers=2, thread_name_prefix="RexEngineering")

        # Cierre limpio al cerrar la ventana
        self.ui._win.on_close_callback = lambda: self._request_shutdown(
            "Ventana cerrada por el usuario")

        # Iniciar monitor de hardware
        self.model.start_metrics_monitoring()

        # Hilo de actualización de métricas UI
        self._metrics_thread_running = True
        self._metrics_thread = threading.Thread(
            target=self._metrics_update_loop, daemon=True)
        self._metrics_thread.start()

    # Envía texto a la API de Gemini Live para síntesis de voz.
    # Este método es llamado por la VoiceQueue para reproducir mensajes.
    def _speak_to_gemini(self, text: str):
        if not text or not text.strip():
            return

        # Normalizar texto
        cleaned = self._normalize_assistant_text(text)
        if not cleaned:
            return

        # Escribir en log
        self.ui.write_log(f"REX: {cleaned}")

        # Enviar a Gemini Live para síntesis de voz
        try:
            if hasattr(self, 'session') and self.session and self._main_loop:
                # Usar el event loop principal guardado, no el del hilo actual
                if self._main_loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        self.session.send_realtime_input(
                            text=cleaned
                        ),
                        self._main_loop
                    )
                else:
                    # Fallback: usar TTS local si el loop no está corriendo
                    self._fallback_tts(cleaned)
            else:
                # Fallback: usar TTS local si no hay sesión o loop
                self._fallback_tts(cleaned)
        except Exception as e:
            print(f"[Controller] ⚠️ Error sending to Gemini: {e}")
            self._fallback_tts(cleaned)

    # TTS de respaldo usando pyttsx3 o gTTS si Gemini no está disponible.
    def _fallback_tts(self, text: str):
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
        except ImportError:
            print(f"[Controller] ⚠️ pyttsx3 not available. Message: {text}")
        except Exception as e:
            print(f"[Controller] ❌ Fallback TTS error: {e}")

    def _normalize_assistant_text(self, text: str) -> str:
        if not text:
            return ""
        t = _HONORIFIC_RE.sub("", str(text))
        t = re.sub(r"\s{2,}", " ", t)
        return t.strip()

    # Cierre idempotente y seguro del asistente.
    def _request_shutdown(self, reason: str = "Solicitado por el usuario"):
        with self._shutdown_lock:
            if self._shutdown_requested:
                return
            self._shutdown_requested = True

        self.ui.write_log("━" * 42)
        self.ui.write_log(f"SYS: Iniciando cierre seguro — {reason}")
        self.ui.write_log("SYS: Guardando sesión y liberando recursos...")

        def _shutdown_worker():
            # 1) Detener actualización de métricas y monitoreo
            self._metrics_thread_running = False
            try:
                self.model.stop_metrics_monitoring()
            except Exception:
                pass

            # 2) Detener cola de voz
            try:
                shutdown_voice_queue()
            except Exception:
                pass

            # 3) Guardar sesión
            try:
                self.model.save_conversation_session()
                self.ui.write_log("SYS: Sesión guardada correctamente.")
            except Exception:
                pass

            # 4) Cerrar pool de ingeniería
            try:
                self.engineering_executor.shutdown(
                    wait=False, cancel_futures=True)
            except Exception:
                pass

            # 5) Cerrar sesión de Gemini si existe
            try:
                if self.session and self._main_loop and self._main_loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        self.session.close(),
                        self._main_loop
                    )
            except Exception:
                pass

            # 6) Dar un margen breve para limpieza
            time.sleep(0.3)

            # 7) Finalizar app de forma limpia
            try:
                self.ui._app.quit()
            except Exception:
                os._exit(0)

        threading.Thread(target=_shutdown_worker, daemon=True).start()

    def _normalize_output_paths(self, name: str, args: dict) -> dict:
        return normalize_tool_outputs(name, dict(args or {}))

    def _infer_phase(self, estado: str | None, evento: str | None) -> str:
        e = (estado or "").lower()
        ev = (evento or "").lower()
        text = f"{e} {ev}"
        if "espera" in text or "confirm" in text:
            return "Confirmación"
        if "analizando" in text or "ejecutando" in text or "proceso" in text:
            return "Ejecución"
        if "complet" in text or "finalizada" in text or "listo" in text:
            return "Cierre"
        if "error" in text or "cancel" in text or "bloque" in text:
            return "Incidencia"
        if "línea" in text or "conect" in text or "sistema" in text:
            return "Sistema"
        return "Planificación"

    def _infer_next_action(self, estado: str | None, evento: str | None) -> str:
        e = (estado or "").lower()
        ev = (evento or "").lower()
        text = f"{e} {ev}"
        if "confirm" in text:
            return "esperar respuesta de confirmación del usuario"
        if "cancel" in text:
            return "esperar una nueva instrucción"
        if "complet" in text or "finalizada" in text:
            return "presentar resultado final al usuario"
        if "error" in text:
            return "reintentar conexión o ajustar estrategia"
        if "conect" in text or "línea" in text:
            return "esperar siguiente solicitud"
        return "continuar con el siguiente paso"

    def _format_activity_event(
        self,
        estado: str | None,
        progreso: int,
        evento: str | None = None,
        fase: str | None = None,
        siguiente_accion: str | None = None,
    ) -> str:
        f = fase or self._infer_phase(estado, evento)
        nxt = siguiente_accion or self._infer_next_action(estado, evento)
        p = max(0, min(100, int(progreso)))
        detail = f" | Detalle: {evento}" if evento else ""
        return (
            f"Fase: {f} | Estado: {estado or 'en curso'} | "
            f"Avance: {p}% | Siguiente acción: {nxt}{detail}"
        )

    # Si el modo estricto está activo, fuerza plantilla mínima de fase.
    def _enforce_strict_phase_message(self, text: str) -> str:
        raw = (text or "").strip()
        if not raw:
            return raw

        task_active = bool(self._active_instruction) or (
            0 < self._current_progress < 100)
        if not self._strict_phases_enabled or not task_active:
            return raw

        lower = raw.lower()
        has_phase = "fase:" in lower
        has_state = "estado:" in lower
        has_progress = "avance:" in lower
        has_confirm = "confirm" in lower
        has_next = "siguiente acción:" in lower or "siguiente accion:" in lower

        if has_phase and has_state and has_progress and has_confirm and has_next:
            return raw

        inferred_phase = self._infer_phase("En proceso", raw)
        inferred_next = self._infer_next_action("En proceso", raw)
        confirm_label = "Confirmación de fase: realizada" if "complet" in lower else "Confirmación de fase: en curso"
        progress = max(0, min(100, int(self._current_progress or 0)))

        strict_block = (
            f"Fase: {inferred_phase} | Estado: en curso | Avance: {progress}% | "
            f"{confirm_label} | Siguiente acción: {inferred_next}."
        )

        if self._strict_phases_failfast:
            self.ui.write_log(
                "SYS: Salida no conforme bloqueada por modo estricto fail-fast; se entrega formato estructurado."
            )
            return strict_block

        if raw.endswith("."):
            return f"{raw} {strict_block}"
        return f"{raw}. {strict_block}"

    def _begin_task(self, instruction: str):
        self._active_instruction = instruction or ""
        self._current_progress = 3
        self._tool_counter = 0
        evento = self._format_activity_event(
            estado="Iniciado",
            progreso=self._current_progress,
            evento="Tarea iniciada",
            fase="Planificación",
            siguiente_accion="analizar la instrucción y preparar ejecución"
        )
        self.ui.update_activity(
            instruccion=self._active_instruction,
            estado="Iniciado",
            progreso=self._current_progress,
            evento=evento
        )

    def _advance_progress(self, target: int, estado: str | None = None, evento: str | None = None):
        target = max(0, min(100, int(target)))
        if target > self._current_progress:
            self._current_progress = target
        evento_fmt = self._format_activity_event(
            estado=estado,
            progreso=self._current_progress,
            evento=evento,
        )
        self.ui.update_activity(
            estado=estado,
            progreso=self._current_progress,
            evento=evento_fmt
        )

    def _complete_task(self, evento: str = "Tarea completada"):
        self._current_progress = 100
        evento_fmt = self._format_activity_event(
            estado="Completado",
            progreso=100,
            evento=evento,
            fase="Cierre",
            siguiente_accion="informar resultado final y quedar en espera"
        )
        self.ui.update_activity(
            estado="Completado",
            progreso=100,
            evento=evento_fmt
        )
        self._active_instruction = ""

    def _is_affirmative(self, text: str) -> bool:
        t = (text or "").strip().lower()
        return t in {"si", "sí", "s", "yes", "ok", "dale", "confirmo", "confirmar", "de acuerdo"}

    def _is_negative(self, text: str) -> bool:
        t = (text or "").strip().lower()
        return t in {"no", "n", "cancelar", "cancela", "omitir", "stop", "detener"}

    # Encadena automáticamente screen_process → electronics para analizar
    # el circuito visible en pantalla sin que el usuario especifique herramientas.
    async def _run_circuit_screen_analysis(self):
        loop = asyncio.get_event_loop()
        self.ui.write_log(
            "SYS: Paso 1/2 — Capturando pantalla y extrayendo componentes...")
        self._advance_progress(20, estado="Analizando",
                               evento="Capturando pantalla")
        try:
            screen_text = await loop.run_in_executor(
                None,
                lambda: __import__("actions.screen_processor",
                                   fromlist=["screen_process"])
                .screen_process(
                    parameters={"action": "ocr",
                                "extract_components": True},
                    player=self.ui
                )
            )
            if not screen_text or "error" in str(screen_text).lower():
                self.speak(
                    "No pude capturar la pantalla o extraer texto del circuito.")
                return
            self.ui.write_log(
                f"SYS: Texto extraído: {str(screen_text)[:200]}...")
            self._advance_progress(
                50, estado="Analizando", evento="Identificando componentes")

            # Paso 2: pasar el texto a electronics para análisis
            self.ui.write_log(
                "SYS: Paso 2/2 — Analizando componentes con módulo de electrónica...")
            analysis = await loop.run_in_executor(
                self.engineering_executor,
                lambda: __import__("actions.electronics",
                                   fromlist=["electronics"])
                .electronics(
                    parameters={
                        "action": "analyze_from_text",
                        "source_text": str(screen_text),
                    },
                    player=self.ui,
                    speak=self.speak,
                )
            )
            result = str(analysis or "Análisis completado.").strip()
            self.ui.write_log(f"ACT: Análisis de circuito: {result[:300]}")
            self.speak(f"Análisis completado. {result[:250]}")
            self._complete_task("Análisis de circuito en pantalla")

        except Exception as e:
            self.speak_error("circuit_screen_analysis", e)

    # Inicia búsqueda web después de confirmación explícita.
    def _start_confirmed_web_search(self, request: dict):
        # Marcar como ejecutada ANTES de iniciar
        self._web_search_executed = True
        
        def _run():
            try:
                from actions.web_search import web_search as web_search_action
                args = dict(request.get("args") or {})
                query = request.get("query", "búsqueda web")
                
                self.ui.write_log(f"ACT: Ejecutando búsqueda web: {query}")
                self._advance_progress(
                    60, estado="En proceso", evento="Ejecutando búsqueda web confirmada")
                
                result = web_search_action(parameters=args, player=self.ui) or "Sin resultados."
                result_text = str(result).strip() or "Sin resultados."
                
                self.ui.write_log("ACT: Búsqueda web finalizada")
                self.ui.write_log("Rex: Búsqueda web completada. Estos son los resultados encontrados.")
                
                for block in [part.strip() for part in result_text.split("\n\n") if part.strip()]:
                    self.ui.write_log(f"WEB: {block}")
                    self.ui.add_recent_web_results(block)
                
                if not self.ui.muted:
                    self.speak("La búsqueda web ha finalizado. Ya mostré los resultados en pantalla.")
                
                self._complete_task("Búsqueda web finalizada")
                
                # Resetear flag después de completar
                self._web_search_executed = False
                
            except Exception as e:
                self.speak_error("web_search", e)
                self._web_search_executed = False  # Resetear en caso de error
        
        threading.Thread(target=_run, daemon=True).start()

    def _on_setup_done(self, key: str, os_name: str):
        self.model.save_config(key, os_name)

    def _metrics_update_loop(self):
        import time
        _last_alert: dict[str, float] = {}
        _COOLDOWN = 60.0

        while self._metrics_thread_running:
            try:
                metrics = self.model.get_system_metrics()
                self.ui._win.update_system_metrics(metrics)

                # Alertas proactivas
                alerts = self.model.metrics_tracker.check_alerts()
                now = time.time()
                for alert in alerts:
                    m = alert["metric"]
                    last = _last_alert.get(m, 0.0)
                    if now - last >= _COOLDOWN:
                        _last_alert[m] = now
                        lvl = "⚠️" if alert["level"] == "warn" else "🔴"
                        self.ui.write_log(f"SYS {lvl}: {alert['msg']}")
                        self.speak(alert["msg"])
                        if alert["level"] == "crit" and m == "CPU":
                            try:
                                import psutil
                                import os
                                p = psutil.Process(os.getpid())
                                p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS
                                       if hasattr(psutil, "BELOW_NORMAL_PRIORITY_CLASS")
                                       else 10)
                                self.ui.write_log(
                                    "SYS: Prioridad del proceso reducida para liberar CPU.")
                            except Exception:
                                pass
            except Exception:
                pass

            # Verificar timeout de confirmación pendiente
            if (self._awaiting_confirmation and 
                self._confirmation_timeout and 
                time.time() > self._confirmation_timeout):
                self.ui.write_log("SYS: ⏱ Timeout de confirmación (60s). Cancelando búsqueda web pendiente.")
                self._pending_web_search = None
                self._awaiting_confirmation = False
                self._confirmation_timeout = None
                self.speak("No recibí confirmación a tiempo. La búsqueda web ha sido cancelada.")
                self._complete_task("Búsqueda web cancelada por timeout")

            time.sleep(2.0)

    def _on_text_command(self, text: str):
        if not self._loop or not self.session:
            return
        if self._shutdown_requested:
            self.ui.write_log("SYS: Ignorando comando: cierre en progreso.")
            return

        # INTERCEPTAR confirmación pendiente ANTES de enviar al modelo
        pending = self._pending_web_search
        if pending is not None and self._awaiting_confirmation:
            self.ui.write_log(f"SYS: Detectada respuesta de texto durante confirmación: '{text}'")
            
            if self._is_affirmative(text):
                self._pending_web_search = None
                self._awaiting_confirmation = False
                self._confirmation_timeout = None
                self.ui.write_log("SYS: ✓ Confirmación afirmativa recibida por texto")
                self.speak("Entendido. Iniciando la búsqueda web ahora.")
                self._start_confirmed_web_search(pending)
                return  # NO enviar al modelo
            
            if self._is_negative(text):
                self._pending_web_search = None
                self._awaiting_confirmation = False
                self._confirmation_timeout = None
                self.ui.write_log("SYS: ✗ Confirmación negativa recibida por texto")
                self.speak("Búsqueda web cancelada. ¿En qué más puedo ayudarte?")
                evento = self._format_activity_event(
                    estado="Cancelado",
                    progreso=0,
                    evento="Búsqueda web cancelada",
                    fase="Confirmación",
                    siguiente_accion="esperar una nueva instrucción"
                )
                self.ui.update_activity(
                    estado="Cancelado",
                    progreso=0,
                    evento=evento
                )
                return  # NO enviar al modelo
            
            # Si no es ni sí ni no, pedir aclaración
            self.ui.write_log(f"SYS: ⚠ Respuesta no clara recibida: '{text}'")
            self.speak("No entendí tu respuesta. Por favor responde sí o no para confirmar la búsqueda web.")
            return  # NO enviar al modelo

        # Flujo normal: enviar al modelo
        self._begin_task(text)
        self._advance_progress(10, estado="En proceso", evento="Instrucción recibida")
        
        try:
            low = text.strip().lower()
            if 'comprobar permisos' in low or 'comprobar permiso' in low:
                all_flag = False
                if 'todas' in low or 'todas las' in low or 'todo' in low:
                    all_flag = True
                self._on_permission_check(all_flag)
                return

            # Comando contextual: análisis de circuito en pantalla
            _circuit_triggers = [
                "analiza el circuito", "analiza el esquematico", "analiza el esquemático",
                "analiza la pantalla", "identifica los componentes",
                "qué circuito ves", "que circuito ves",
                "analiza el diagrama en pantalla", "scan circuito",
            ]
            if any(t in low for t in _circuit_triggers):
                self.ui.write_log("SYS: Comando contextual — Análisis de circuito en pantalla.")
                self.speak("Analizando el circuito en pantalla. Dame un momento.")
                asyncio.run_coroutine_threadsafe(
                    self._run_circuit_screen_analysis(), self._loop
                )
                return
        except Exception:
            pass

        asyncio.run_coroutine_threadsafe(
            self.session.send_client_content(
                turns={"parts": [{"text": text}]},
                turn_complete=True
            ),
            self._loop
        )
        self._advance_progress(18, estado="En proceso", evento="Solicitud enviada al modelo")

    def set_speaking(self, value: bool):
        with self._speaking_lock:
            self._is_speaking = value
        if value:
            self.ui.set_state("SPEAKING")
        elif not self.ui.muted:
            self.ui.set_state("LISTENING")

    # Método speak mejorado que usa la cola de voz.
    def speak(self, text: str):
        if text:
            enforced = self._enforce_strict_phase_message(text)
            cleaned = self._normalize_assistant_text(enforced)
            if cleaned:
                self.ui.write_log(f"REX: {cleaned}")
                # Enviar a la cola de voz para reproducción ordenada
                self._voice_queue.enqueue(cleaned)

    def speak_error(self, tool_name: str, error: str):
        short = str(error)[:120]
        self.ui.write_log(f"ERR: {tool_name} — {short}")
        self.speak(f"Se produjo un error en {tool_name}. {short}")

    def _on_permission_check(self, all_flag: bool = False):
        def _run():
            try:
                from actions.permission_check import permission_check
                if all_flag:
                    self.ui.write_log(
                        "SYS: Ejecutando comprobación de permisos (TODAS las carpetas)...")
                else:
                    self.ui.write_log(
                        "SYS: Ejecutando comprobación de permisos (carpetas comunes)...")
                res = permission_check(parameters={"all": all_flag})
                for line in res.splitlines():
                    self.ui.write_log(line)
                if not self.ui.muted:
                    self.speak(
                        "Comprobación de permisos finalizada. Revisa el registro.")
            except Exception as e:
                self.speak_error('permission_check', e)
        threading.Thread(target=_run, daemon=True).start()

    # Itera recursivamente por excepciones dentro de ExceptionGroup.
    def _iter_nested_exceptions(self, exc: BaseException):
        if isinstance(exc, BaseExceptionGroup):
            for sub in exc.exceptions:
                yield from self._iter_nested_exceptions(sub)
            return
        yield exc

    # Detecta cierres de sesión Live esperables (p.ej. 1008/1011).
    def _is_recoverable_live_error(self, exc: BaseException) -> bool:
        for sub in self._iter_nested_exceptions(exc):
            text = str(sub).lower()
            code = getattr(sub, "code", None)
            status_code = getattr(sub, "status_code", None)

            if code == 1007 or status_code == 1007:
                if (
                    "content_type_audio" in text
                    or "audio content type" in text
                    or "not supported for this model configuration" in text
                ):
                    return True

            if code == 1008 or status_code == 1008:
                return True

            if code == 1011 or status_code == 1011:
                return True

            if "1008" in text and (
                "policy violation" in text
                or "operation is not implemented" in text
                or "not supported" in text
                or "not enabled" in text
            ):
                return True

            if "1011" in text and (
                "internal error" in text
                or "internal error occurred" in text
            ):
                return True

            if "connectionclosed" in sub.__class__.__name__.lower() and "1008" in text:
                return True

            if "connectionclosed" in sub.__class__.__name__.lower() and "1011" in text:
                return True

        return False

    # Detecta específicamente rechazo de audio de entrada (1007 CONTENT_TYPE_AUDIO).
    def _is_audio_content_unsupported(self, exc: BaseException) -> bool:
        for sub in self._iter_nested_exceptions(exc):
            text = str(sub).lower()
            code = getattr(sub, "code", None)
            status_code = getattr(sub, "status_code", None)
            if code == 1007 or status_code == 1007 or "1007" in text:
                if (
                    "content_type_audio" in text
                    or "audio content type" in text
                    or "not supported for this model configuration" in text
                ):
                    return True
        return False

    def _build_config(self) -> types.LiveConnectConfig:
        from datetime import datetime

        mem_str = self.model.get_formatted_memory()
        sys_prompt = _load_system_prompt()

        now = datetime.now()
        time_str = now.strftime("%A, %B %d, %Y — %I:%M %p")
        time_ctx = (
            f"[CURRENT DATE & TIME]\n"
            f"Right now it is: {time_str}\n"
            f"Use this to calculate exact times for reminders.\n\n"
        )

        history_str = self.model.get_formatted_history()
        parts = [time_ctx]
        if mem_str:
            parts.append(mem_str)
        if history_str:
            parts.append(history_str)
        parts.append(sys_prompt)

        # Configurar modalidades según si el audio está habilitado
        if self._audio_input_enabled:
            response_modalities = ["AUDIO"]
            input_audio_transcription = {}
        else:
            # Modo texto: solo salida de audio, sin entrada de micrófono
            response_modalities = ["AUDIO"]
            input_audio_transcription = None

        return types.LiveConnectConfig(
            response_modalities=response_modalities,
            output_audio_transcription={},
            input_audio_transcription=input_audio_transcription,
            system_instruction="\n".join(parts),
            tools=[{"function_declarations": TOOL_DECLARATIONS}],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Aoede"
                    )
                )
            ),
        )

    # Extrae códigos de error relevantes desde excepciones anidadas.
    def _extract_live_error_codes(self, exc: BaseException) -> list[int]:
        found: list[int] = []
        for sub in self._iter_nested_exceptions(exc):
            code = getattr(sub, "code", None)
            status_code = getattr(sub, "status_code", None)
            if isinstance(code, int):
                found.append(code)
            if isinstance(status_code, int):
                found.append(status_code)

            text = str(sub)
            if "1011" in text:
                found.append(1011)
            if "1008" in text:
                found.append(1008)

        # únicos, orden estable
        uniq = []
        seen = set()
        for c in found:
            if c in seen:
                continue
            seen.add(c)
            uniq.append(c)
        return uniq

    # Registra métricas de desconexión Live (solo si diagnóstico está habilitado).
    def _record_live_disconnect(self, exc: BaseException, recoverable: bool):
        if not self._live_diag_enabled:
            return

        now = time.time()
        self._live_disconnect_total += 1
        self._live_disconnect_ts.append(now)

        # ventana móvil 1h
        while self._live_disconnect_ts and now - self._live_disconnect_ts[0] > 3600:
            self._live_disconnect_ts.popleft()

        codes = self._extract_live_error_codes(exc)
        if not codes:
            codes = [0]

        for c in codes:
            self._live_disconnect_code_counts[c] = self._live_disconnect_code_counts.get(
                c, 0) + 1

        per_hour = len(self._live_disconnect_ts)
        code_str = ", ".join(str(c) for c in codes)
        mode = "recoverable" if recoverable else "fatal"
        diag_msg = (
            f"SYS-DIAG: Live disconnect ({mode}) codes=[{code_str}] | "
            f"1h={per_hour} total={self._live_disconnect_total}"
        )
        print(f"[REX] {diag_msg}")
        self.ui.write_log(diag_msg)

    async def _execute_tool(self, fc) -> types.FunctionResponse:
        name = fc.name
        args = self._normalize_output_paths(name, dict(fc.args or {}))

        print(f"[REX] 🔧 {name}  {args}")
        self.ui.set_state("THINKING")
        self._tool_counter += 1
        start_progress = 25 + min(40, self._tool_counter * 12)
        self._advance_progress(
            start_progress, estado="En proceso", evento=f"Ejecutando herramienta: {name}")

        if name == "save_memory":
            category = args.get("category", "notes")
            key = args.get("key", "")
            value = args.get("value", "")
            if key and value:
                self.model.save_long_term_memory(category, key, value)
                print(f"[Memory] 💾 save_memory: {category}/{key} = {value}")
            if not self.ui.muted:
                self.ui.set_state("LISTENING")
            return types.FunctionResponse(
                id=fc.id, name=name,
                response={"result": "ok", "silent": True}
            )

        if name == "remember_technical":
            from memory.memory_manager import remember_technical
            key = args.get("key", "")
            value = args.get("value", "")
            cat = args.get("category") or None
            result_mem = remember_technical(
                key, value, cat) if key and value else "Parámetros insuficientes."
            print(f"[TechMemory] 💾 {result_mem}")
            return types.FunctionResponse(
                id=fc.id, name=name,
                response={"result": result_mem, "silent": True}
            )

        if name == "recall_technical":
            from memory.memory_manager import recall_technical, format_tech_memory_for_prompt
            query = args.get("query", "")
            results = recall_technical(query, top_k=5)
            if results:
                summary = "\n".join(
                    f"[{r['category'].upper()}] {r['key']}: {r['value'][:200]}" for r in results
                )
            else:
                summary = "No se encontraron soluciones técnicas previas para esa consulta."
            return types.FunctionResponse(
                id=fc.id, name=name,
                response={"result": summary}
            )

        loop = asyncio.get_event_loop()
        result = "Hecho."

        def _tool_unavailable(tool: str, err: Exception) -> str:
            return f"La herramienta '{tool}' no está disponible en este entorno: {err}"

        def _run_sync(module_name: str, attr: str, *call_args, **call_kwargs):
            try:
                mod = __import__(module_name, fromlist=[attr])
                fn = getattr(mod, attr)
            except Exception as imp_err:
                return _tool_unavailable(module_name.split(".")[-1], imp_err)
            try:
                return fn(*call_args, **call_kwargs)
            except Exception as run_err:
                raise run_err

        try:
            common_handlers = {
                "open_app": lambda: loop.run_in_executor(None, lambda: _run_sync("actions.open_app", "open_app", parameters=args, response=None, player=self.ui)),
                "weather_report": lambda: loop.run_in_executor(None, lambda: _run_sync("actions.weather_report", "weather_action", parameters=args, player=self.ui)),
                "browser_control": lambda: loop.run_in_executor(None, lambda: _run_sync("actions.browser_control", "browser_control", parameters=args, player=self.ui)),
                "file_controller": lambda: loop.run_in_executor(None, lambda: _run_sync("actions.file_controller", "file_controller", parameters=args, player=self.ui)),
                "send_message": lambda: loop.run_in_executor(None, lambda: _run_sync("actions.send_message", "send_message", parameters=args, response=None, player=self.ui, session_memory=None)),
                "reminder": lambda: loop.run_in_executor(None, lambda: _run_sync("actions.reminder", "reminder", parameters=args, response=None, player=self.ui)),
                "youtube_video": lambda: loop.run_in_executor(None, lambda: _run_sync("actions.youtube_video", "youtube_video", parameters=args, response=None, player=self.ui)),
                "computer_settings": lambda: loop.run_in_executor(None, lambda: _run_sync("actions.computer_settings", "computer_settings", parameters=args, response=None, player=self.ui)),
                "desktop_control": lambda: loop.run_in_executor(None, lambda: _run_sync("actions.desktop", "desktop_control", parameters=args, player=self.ui)),
                "code_helper": lambda: loop.run_in_executor(None, lambda: _run_sync("actions.code_helper", "code_helper", parameters=args, player=self.ui, speak=self.speak)),
                "dev_agent": lambda: loop.run_in_executor(None, lambda: _run_sync("actions.dev_agent", "dev_agent", parameters=args, player=self.ui, speak=self.speak)),
                "computer_control": lambda: loop.run_in_executor(None, lambda: _run_sync("actions.computer_control", "computer_control", parameters=args, player=self.ui)),
                "game_updater": lambda: loop.run_in_executor(None, lambda: _run_sync("actions.game_updater", "game_updater", parameters=args, player=self.ui, speak=self.speak)),
                "dev_tools": lambda: loop.run_in_executor(None, lambda: _run_sync("actions.dev_tools", "dev_tools", parameters=args, player=self.ui, speak=self.speak)),
                "mechatronics": lambda: loop.run_in_executor(None, lambda: _run_sync("actions.mechatronics", "mechatronics", parameters=args, player=self.ui, speak=self.speak)),
                "datasheet_finder": lambda: loop.run_in_executor(None, lambda: _run_sync("actions.datasheet_finder", "datasheet_finder", parameters=args, player=self.ui, speak=self.speak)),
                "materials_science": lambda: loop.run_in_executor(None, lambda: _run_sync("actions.materials_science", "materials_science", parameters=args, player=self.ui, speak=self.speak)),
                "proteus_automation": lambda: loop.run_in_executor(None, lambda: _run_sync("actions.proteus_automation", "proteus_automation", parameters=args, player=self.ui, speak=self.speak)),
                "ltspice_automation": lambda: loop.run_in_executor(None, lambda: _run_sync("actions.ltspice_automation", "ltspice_automation", parameters=args, player=self.ui, speak=self.speak)),
                "flight_finder": lambda: loop.run_in_executor(None, lambda: _run_sync("actions.flight_finder", "flight_finder", parameters=args, player=self.ui)),
            }

            if name == "screen_process":
                try:
                    from actions.screen_processor import screen_process
                except Exception as imp_err:
                    result = _tool_unavailable(name, imp_err)
                    raise RuntimeError(result)
                threading.Thread(
                    target=screen_process,
                    kwargs={"parameters": args, "response": None,
                            "player": self.ui, "session_memory": None},
                    daemon=True
                ).start()
                result = "Módulo de visión activado. Mantén silencio: el módulo de visión hablará directamente."

            elif name == "agent_task":
                from agent.task_queue import get_queue, TaskPriority
                priority_map = {
                    "low": TaskPriority.LOW,
                    "normal": TaskPriority.NORMAL,
                    "high": TaskPriority.HIGH
                }
                priority = priority_map.get(
                    args.get("priority", "normal").lower(), TaskPriority.NORMAL)

                # Pasar la función de voz mejorada y la UI
                task_id = get_queue().submit(
                    goal=args.get("goal", ""),
                    priority=priority,
                    speak=self._speak_to_gemini,
                    ui=self.ui
                )
                result = f"Tarea iniciada (ID: {task_id})."

            elif name == "web_search":
                # Si ya estamos esperando confirmación, ignorar completamente
                if self._awaiting_confirmation:
                    self.ui.write_log("SYS: ⚠ web_search llamado mientras se espera confirmación. Ignorando.")
                    # Devolver resultado que NO genere más llamadas
                    result = "BÚSQUEDA_PENDIENTE: Ya se está esperando confirmación del usuario. No hagas nada. Solo espera."
                else:
                    query = args.get("query", "").strip()
                    items = args.get("items", [])
                    resumen = query or ", ".join(items) or "consulta web"
                    
                    # ESTABLECER modo de confirmación
                    self._pending_web_search = {"args": args, "query": resumen}
                    self._awaiting_confirmation = True
                    self._confirmation_timeout = time.time() + 60
                    self._web_search_executed = False
                    
                    evento = self._format_activity_event(
                        estado="En espera",
                        progreso=max(self._current_progress, 30),
                        evento="Esperando confirmación para búsqueda web",
                        fase="Confirmación",
                        siguiente_accion="esperar respuesta sí/no del usuario"
                    )
                    self.ui.update_activity(
                        estado="En espera",
                        progreso=max(self._current_progress, 30),
                        evento=evento
                    )
                    
                    # Mensaje claro al usuario
                    confirm_msg = f"¿Deseas que realice una búsqueda web sobre: '{resumen}'? Responde sí o no."
                    self.ui.write_log(f"Rex: {confirm_msg}")
                    self.speak(confirm_msg)
                    
                    # Resultado MUY EXPLÍCITO para el modelo
                    result = (
                        "⚠️ ACCIÓN REQUERIDA: Espera en silencio. "
                        "NO llames a web_search nuevamente. "
                        "NO llames a ninguna otra herramienta. "
                        "NO digas nada al usuario. "
                        "Solo espera la respuesta del usuario (sí/no). "
                        "Cuando el usuario confirme, la búsqueda se ejecutará automáticamente. "
                        "Tu única acción ahora es esperar."
                    )
                
            elif name == "file_processor":
                if not args.get("file_path") and self.ui.current_file:
                    args["file_path"] = self.ui.current_file
                r = await loop.run_in_executor(
                    None,
                    lambda: file_processor(
                        parameters=args, player=self.ui, speak=self.speak)
                )
                result = r or "Hecho."
            elif name == "electronics":
                from actions.electronics import ElectronicsAction
                action_instance = ElectronicsAction()
                r = await loop.run_in_executor(
                    self.engineering_executor,
                    lambda: asyncio.run(action_instance.execute(
                        parameters=args, player=self.ui, speak_callback=self.speak))
                )
                result = r or "Hecho."
            elif name == "engineering_report":
                from actions.engineering_report import engineering_report
                r = await loop.run_in_executor(
                    self.engineering_executor,
                    lambda: engineering_report(
                        parameters=args, player=self.ui, speak=self.speak)
                )
                result = r or "Reporte de ingeniería generado."
            elif name == "matlab_link":
                from actions.matlab_link import MatlabLinkAction
                action_instance = MatlabLinkAction()
                r = await loop.run_in_executor(
                    self.engineering_executor,
                    lambda: asyncio.run(action_instance.execute(
                        parameters=args, player=self.ui, speak_callback=self.speak))
                )
                result = r or "Hecho."
            elif name == "mecatronic_link":
                from actions.mecatronic_link import MecatronicLinkAction
                action_instance = MecatronicLinkAction()
                r = await loop.run_in_executor(
                    self.engineering_executor,
                    lambda: asyncio.run(action_instance.execute(
                        parameters=args, player=self.ui, speak_callback=self.speak))
                )
                result = r or "Hecho."
            elif name == "shutdown_rex":
                self.ui.write_log("SYS: Apagado solicitado.")
                self.ui.write_log("Rex: Hasta luego. Sesión guardada.")
                self._request_shutdown("Herramienta shutdown_rex")
                result = "Cierre seguro iniciado."
            elif name in common_handlers:
                r = await common_handlers[name]()
                result = r or "Hecho."
            else:
                result = f"Herramienta desconocida: {name}"
        except Exception as e:
            result = f"La herramienta '{name}' falló: {e}"
            traceback.print_exc()
            self.speak_error(name, e)

        if not self.ui.muted:
            self.ui.set_state("LISTENING")

        if name != "web_search":
            end_progress = min(90, self._current_progress + 15)
            self._advance_progress(
                end_progress, estado="En proceso", evento=f"Acción finalizada: {name}")

        result = self._normalize_assistant_text(str(result))
        print(f"[REX] 📤 {name} → {result[:80]}")
        return types.FunctionResponse(
            id=fc.id, name=name,
            response={"result": result}
        )

    async def _send_realtime(self):
        if not self._audio_input_enabled:
            return
        while True:
            msg = await self.out_queue.get()
            await self.session.send_realtime_input(media=msg)

    async def _listen_audio(self):
        if not self._audio_input_enabled:
            self.ui.write_log(
                "SYS: Micrófono desactivado por compatibilidad de modelo Live.")
            self.ui.write_log(
                "SYS: Modo texto activo — usa el chat para comunicarte.")
            # Mantener el hilo vivo pero sin capturar audio
            while True:
                await asyncio.sleep(1.0)
            return

        print("[REX] 🎤 Mic started")
        loop = asyncio.get_event_loop()

        def _enqueue_audio(payload):
            try:
                self.out_queue.put_nowait(payload)
            except asyncio.QueueFull:
                pass

        def callback(indata, frames, time_info, status):
            if status:
                print(f"[REX] Mic status: {status}")
            with self._speaking_lock:
                rex_speaking = self._is_speaking
            if not rex_speaking and not self.ui.muted:
                loop.call_soon_threadsafe(
                    _enqueue_audio,
                    {"data": indata.tobytes(), "mime_type": "audio/pcm"},
                )

        try:
            with sd.InputStream(
                samplerate=SEND_SAMPLE_RATE,
                channels=CHANNELS,
                dtype="int16",
                blocksize=CHUNK_SIZE,
                callback=callback,
            ):
                print("[REX] 🎤 Mic stream open")
                while True:
                    await asyncio.sleep(0.1)
        except Exception as e:
            print(f"[REX] ❌ Mic: {e}")
            self.ui.write_log(f"SYS: Error de micrófono — {e}")
            raise

    async def _receive_audio(self):
        print("[REX] 👂 Recv started")
        out_buf, in_buf = [], []

        try:
            while True:
                async for response in self.session.receive():
                    if response.data:
                        if self._turn_done_event and self._turn_done_event.is_set():
                            self._turn_done_event.clear()
                        self.audio_in_queue.put_nowait(response.data)

                    if response.server_content:
                        sc = response.server_content

                        if sc.output_transcription and sc.output_transcription.text:
                            txt = _clean_transcript(
                                sc.output_transcription.text)
                            if txt:
                                out_buf.append(txt)

                        if sc.input_transcription and sc.input_transcription.text:
                            txt = _clean_transcript(
                                sc.input_transcription.text)
                            if txt:
                                # INTERCEPTAR confirmación pendiente por VOZ ANTES de agregar al buffer
                                if self._awaiting_confirmation and self._pending_web_search is not None:
                                    self.ui.write_log(f"SYS: Detectada respuesta de voz durante confirmación: '{txt}'")
                                    
                                    if self._is_affirmative(txt):
                                        pending = self._pending_web_search
                                        self._pending_web_search = None
                                        self._awaiting_confirmation = False
                                        self._confirmation_timeout = None
                                        self.ui.write_log("SYS: ✓ Confirmación afirmativa recibida por voz")
                                        self.speak("Entendido. Iniciando la búsqueda web ahora.")
                                        self._start_confirmed_web_search(pending)
                                        # NO agregar al buffer, NO enviar al modelo
                                        continue
                                    
                                    if self._is_negative(txt):
                                        self._pending_web_search = None
                                        self._awaiting_confirmation = False
                                        self._confirmation_timeout = None
                                        self.ui.write_log("SYS: ✗ Confirmación negativa recibida por voz")
                                        self.speak("Búsqueda web cancelada. ¿En qué más puedo ayudarte?")
                                        evento = self._format_activity_event(
                                            estado="Cancelado",
                                            progreso=0,
                                            evento="Búsqueda web cancelada por voz",
                                            fase="Confirmación",
                                            siguiente_accion="esperar una nueva instrucción"
                                        )
                                        self.ui.update_activity(
                                            estado="Cancelado",
                                            progreso=0,
                                            evento=evento
                                        )
                                        # NO agregar al buffer, NO enviar al modelo
                                        continue
                                    
                                    # Respuesta no clara
                                    self.ui.write_log(f"SYS: ⚠ Respuesta no clara recibida: '{txt}'")
                                    self.speak("No entendí tu respuesta. Por favor responde claramente sí o no.")
                                    # NO agregar al buffer, NO enviar al modelo
                                    continue
                                
                                # Si no hay confirmación pendiente, agregar al buffer normalmente
                                in_buf.append(txt)

                        if sc.turn_complete:
                            if self._turn_done_event:
                                self._turn_done_event.set()

                            full_in = " ".join(in_buf).strip()
                            if full_in:
                                self.ui.write_log(f"Usuario: {full_in}")
                                self.model.session_log.append(
                                    {"role": "user", "text": full_in})
                            in_buf = []

                            full_out = " ".join(out_buf).strip()
                            if full_out:
                                full_out = self._normalize_assistant_text(
                                    full_out)
                                self.ui.write_log(f"Rex: {full_out}")
                                self.model.session_log.append(
                                    {"role": "rex", "text": full_out})
                            out_buf = []

                            if self._pending_web_search is None:
                                self._complete_task("Solicitud completada")

                    if response.tool_call:
                        fn_responses = []
                        for fc in response.tool_call.function_calls:
                            print(f"[REX] 📞 {fc.name}")
                            fr = await self._execute_tool(fc)
                            fn_responses.append(fr)
                        await self.session.send_tool_response(
                            function_responses=fn_responses
                        )
        except Exception as e:
            if self._is_recoverable_live_error(e):
                print(f"[REX] ⚠️ Recv recoverable: {e}")
            else:
                print(f"[REX] ❌ Recv: {e}")
                traceback.print_exc()
            raise

    async def _play_audio(self):
        print("[REX] 🔊 Play started")
        self.ui.write_log(
            "ACT: Audio estable activado (PCM16 alineado, baja latencia)")

        stream = sd.RawOutputStream(
            samplerate=RECEIVE_SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            blocksize=PLAYBACK_BLOCKSIZE,
            latency="low",
        )
        stream.start()

        try:
            while True:
                try:
                    chunk = await asyncio.wait_for(
                        self.audio_in_queue.get(),
                        timeout=0.1
                    )
                except asyncio.TimeoutError:
                    if (
                        self._turn_done_event
                        and self._turn_done_event.is_set()
                        and self.audio_in_queue.empty()
                    ):
                        self.set_speaking(False)
                        self._turn_done_event.clear()
                    continue
                self.set_speaking(True)
                # Asegura alineación PCM16 por frame para evitar distorsión.
                frame_bytes = 2 * CHANNELS  # int16 * channels
                if not isinstance(chunk, (bytes, bytearray)):
                    chunk = bytes(chunk)
                if len(chunk) < frame_bytes:
                    continue
                rem = len(chunk) % frame_bytes
                if rem:
                    chunk = chunk[:len(chunk) - rem]
                await asyncio.to_thread(stream.write, chunk)
        except Exception as e:
            print(f"[REX] ❌ Play: {e}")
            raise
        finally:
            self.set_speaking(False)
            stream.stop()
            stream.close()

    async def run(self):
        # Auto-guardar sesión en caso de desconexiones repentinas
        import atexit
        atexit.register(self.model.save_conversation_session)
        atexit.register(shutdown_voice_queue)

        client = get_gemini_client()

        while True:
            try:
                print("[REX] 🔌 Conectando...")
                self.ui.set_state("THINKING")
                config = self._build_config()

                async with (
                    client.aio.live.connect(model=LIVE_MODEL, config=config) as session,
                    asyncio.TaskGroup() as tg,
                ):
                    self.session = session
                    self._loop = asyncio.get_event_loop()
                    self._main_loop = self._loop  # Guardar referencia para otros hilos
                    self.audio_in_queue = asyncio.Queue()
                    self.out_queue = asyncio.Queue(maxsize=10)
                    self._turn_done_event = asyncio.Event()

                    print("[REX] ✅ Conectado....")
                    self.ui.set_state("LISTENING")
                    self.ui.write_log("━" * 42)
                    self.ui.write_log("  ◈  MARK XXXIX  —  SISTEMA EN LÍNEA")
                    self.ui.write_log("━" * 42)
                    self.ui.write_log(
                        "SYS: Conexión con Gemini Live establecida.")
                    self.ui.write_log(
                        "SYS: Micrófono activo — habla para comenzar.")
                    self.ui.write_log(
                        "SYS: [F4] Silenciar · [F11] Pantalla completa")
                    evento_online = self._format_activity_event(
                        estado="En línea",
                        progreso=100,
                        evento="Sistema listo",
                        fase="Sistema",
                        siguiente_accion="esperar solicitud del usuario"
                    )
                    self.ui.update_activity(
                        estado="En línea",
                        progreso=100,
                        evento=evento_online
                    )

                    tg.create_task(self._send_realtime())
                    tg.create_task(self._listen_audio())
                    tg.create_task(self._receive_audio())
                    tg.create_task(self._play_audio())

            except Exception as e:
                if self._is_audio_content_unsupported(e) and self._audio_input_enabled:
                    self._audio_input_enabled = False
                    self._audio_input_disabled_reason = (
                        "El backend Live rechazó CONTENT_TYPE_AUDIO para esta configuración"
                    )
                    self.ui.write_log(
                        "SYS: Audio de entrada no soportado por el modelo activo. "
                        "Se continuará en modo texto (micrófono desactivado)."
                    )
                    self.ui.write_log(
                        "SYS: Puedes seguir operando con comandos de texto en el chat."
                    )
                    self.ui.write_log(
                        "SYS: El asistente responderá por voz pero no escuchará por micrófono."
                    )
                    # Forzar reconexión inmediata sin esperar
                    self._retry_count = 0
                    continue

                recoverable = self._is_recoverable_live_error(e)
                self._record_live_disconnect(e, recoverable)
                if recoverable:
                    print("[REX] ⚠️ Live session closed by server (recoverable).")
                else:
                    print(f"[REX] ⚠️ {e}")
                if not recoverable:
                    traceback.print_exc()
                self.set_speaking(False)
                self.ui.set_state("THINKING")
                if recoverable:
                    self.ui.write_log(
                        "SYS: Sesión Live reiniciada por compatibilidad del servidor (reconectando).")
                else:
                    self.ui.write_log(
                        f"SYS: Error de conexión — {str(e)[:120]}")
                evento_err = self._format_activity_event(
                    estado="Error",
                    progreso=0,
                    evento="Error de conexión",
                    fase="Incidencia",
                    siguiente_accion="reconectar automáticamente"
                )
                self.ui.update_activity(
                    estado="Error", progreso=0, evento=evento_err)
                retry = getattr(self, '_retry_count', 0)
                wait = min(3 * (2 ** retry), 60)
                self._retry_count = retry + 1
                print(
                    f"[REX] 🔄 Reconectando en {wait}s... (intento {self._retry_count})")
                self.ui.write_log(f"SYS: Reconectando en {wait}s...")
                await asyncio.sleep(wait)
            else:
                self._retry_count = 0