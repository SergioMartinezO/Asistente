import asyncio
import re
import threading
import traceback
import os
import time
from pathlib import Path
import sounddevice as sd
import google.genai as genai
from google.genai import types

from ui import RexUI
from model import RexModel
from core.config import get_gemini_client
from core.output_policy import get_report_base, normalize_tool_outputs

# Importar las declaraciones de herramientas (reutilizadas del main original o importadas)
# Para evitar duplicar el bloque gigante de TOOL_DECLARATIONS, las importaremos o las volveremos a declarar.
# Definiremos las declaraciones de herramientas requeridas por Gemini.
from main import TOOL_DECLARATIONS, _load_system_prompt

LIVE_MODEL = "models/gemini-2.5-flash-native-audio-preview-12-2025"
CHANNELS = 1
SEND_SAMPLE_RATE = 16_000
RECEIVE_SAMPLE_RATE = 24_000
CHUNK_SIZE = 1024
PLAYBACK_BLOCKSIZE = 2048
REPORT_BASE_DIR = Path(r"D:\IA\Asistente\Report")

_CTRL_RE = re.compile(r"<ctrl\d+>", re.IGNORECASE)

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
        self._is_speaking = False
        self._speaking_lock = threading.Lock()
        self._turn_done_event = None
        self._retry_count = 0
        self._pending_web_search = None
        self._current_progress = 0
        self._tool_counter = 0
        self._active_instruction = ""
        self._report_base = get_report_base()
        self._report_base.mkdir(parents=True, exist_ok=True)
        os.environ["REX_REPORT_DIR"] = str(self._report_base)
        self._shutdown_requested = False
        self._shutdown_lock = threading.Lock()
        
        # Servicio de Ingeniería asíncrono para cálculos complejos
        from concurrent.futures import ThreadPoolExecutor
        self.engineering_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="RexEngineering")
        
        # Conectar callbacks de la Vista
        self.ui.on_text_command = self._on_text_command
        self.ui.on_permission_check = self._on_permission_check
        self.ui.on_setup_done = self._on_setup_done
        
        # Iniciar monitor de hardware
        self.model.start_metrics_monitoring()
        
        # Hilo de actualización de métricas UI
        self._metrics_thread_running = True
        self._metrics_thread = threading.Thread(target=self._metrics_update_loop, daemon=True)
        self._metrics_thread.start()

    def _request_shutdown(self, reason: str = "Solicitado por el usuario"):
        """Cierre idempotente y seguro del asistente.

        Evita reentradas, detiene recursos no-daemon y finaliza la UI.
        """
        with self._shutdown_lock:
            if self._shutdown_requested:
                return
            self._shutdown_requested = True

        self.ui.write_log(f"SYS: Iniciando cierre seguro ({reason}).")

        def _shutdown_worker():
            # 1) Detener actualización de métricas y monitoreo
            self._metrics_thread_running = False
            try:
                self.model.stop_metrics_monitoring()
            except Exception:
                pass

            # 2) Guardar sesión
            try:
                self.model.save_conversation_session()
            except Exception:
                pass

            # 3) Cerrar pool de ingeniería (hilos no-daemon que pueden bloquear la salida)
            try:
                self.engineering_executor.shutdown(wait=False, cancel_futures=True)
            except Exception:
                pass

            # 4) Dar un margen breve para limpieza
            time.sleep(0.5)

            # 5) Finalizar app de forma limpia
            try:
                self.ui._app.quit()
            except Exception:
                os._exit(0)

        threading.Thread(target=_shutdown_worker, daemon=True).start()

    def _normalize_output_paths(self, name: str, args: dict) -> dict:
        return normalize_tool_outputs(name, dict(args or {}))

    def _begin_task(self, instruction: str):
        self._active_instruction = instruction or ""
        self._current_progress = 3
        self._tool_counter = 0
        self.ui.update_activity(
            instruccion=self._active_instruction,
            estado="Iniciado",
            progreso=self._current_progress,
            evento="Tarea iniciada"
        )

    def _advance_progress(self, target: int, estado: str | None = None, evento: str | None = None):
        target = max(0, min(100, int(target)))
        if target > self._current_progress:
            self._current_progress = target
        self.ui.update_activity(
            estado=estado,
            progreso=self._current_progress,
            evento=evento
        )

    def _complete_task(self, evento: str = "Tarea completada"):
        self._current_progress = 100
        self.ui.update_activity(
            estado="Completado",
            progreso=100,
            evento=evento
        )

    def _is_affirmative(self, text: str) -> bool:
        t = (text or "").strip().lower()
        return t in {"si", "sí", "s", "yes", "ok", "dale", "confirmo", "confirmar", "de acuerdo"}

    def _is_negative(self, text: str) -> bool:
        t = (text or "").strip().lower()
        return t in {"no", "n", "cancelar", "cancela", "omitir", "stop", "detener"}

    def _start_confirmed_web_search(self, request: dict):
        def _run():
            try:
                from actions.web_search import web_search as web_search_action
                args = dict(request.get("args") or {})
                self._advance_progress(60, estado="En proceso", evento="Ejecutando búsqueda web confirmada")
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
            except Exception as e:
                self.speak_error("web_search", e)
        threading.Thread(target=_run, daemon=True).start()

    def _on_setup_done(self, key: str, os_name: str):
        self.model.save_config(key, os_name)

    def _metrics_update_loop(self):
        import time
        while self._metrics_thread_running:
            try:
                metrics = self.model.get_system_metrics()
                self.ui._win.update_system_metrics(metrics)
            except Exception:
                pass
            time.sleep(2.0)


    def _on_text_command(self, text: str):
        if not self._loop or not self.session:
            return
        if self._shutdown_requested:
            self.ui.write_log("SYS: Ignorando comando: cierre en progreso.")
            return

        # Confirmación explícita pendiente para búsquedas web
        pending = self._pending_web_search
        if pending is not None:
            if self._is_affirmative(text):
                self._pending_web_search = None
                self.ui.write_log("SYS: Confirmación recibida. Iniciando búsqueda web...")
                self._start_confirmed_web_search(pending)
                return
            if self._is_negative(text):
                self._pending_web_search = None
                self.ui.write_log("SYS: Búsqueda web cancelada por el usuario.")
                self.ui.update_activity(
                    estado="Cancelado",
                    progreso=0,
                    evento="Búsqueda web cancelada"
                )
                return
        self._begin_task(text)
        self._advance_progress(10, estado="En proceso", evento="Instrucción recibida")
        # Intercept voice/text triggers for local actions
        try:
            low = text.strip().lower()
            if 'comprobar permisos' in low or 'comprobar permiso' in low:
                all_flag = False
                if 'todas' in low or 'todas las' in low or 'todo' in low:
                    all_flag = True
                # run local permission check
                self._on_permission_check(all_flag)
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

    def speak(self, text: str):
        if text:
            self.ui.write_log(f"REX: {text}")

    def speak_error(self, tool_name: str, error: str):
        short = str(error)[:120]
        self.ui.write_log(f"ERR: {tool_name} — {short}")
        self.speak(f"Se produjo un error en {tool_name}. {short}")

    def _on_permission_check(self, all_flag: bool = False):
        def _run():
            try:
                from actions.permission_check import permission_check
                if all_flag:
                    self.ui.write_log("SYS: Ejecutando comprobación de permisos (TODAS las carpetas)...")
                else:
                    self.ui.write_log("SYS: Ejecutando comprobación de permisos (carpetas comunes)...")
                res = permission_check(parameters={"all": all_flag})
                # write report to log (may be long)
                for line in res.splitlines():
                    self.ui.write_log(line)
                if not self.ui.muted:
                    self.speak("Comprobación de permisos finalizada. Revisa el registro.")
            except Exception as e:
                self.speak_error('permission_check', e)
        threading.Thread(target=_run, daemon=True).start()

    def _iter_nested_exceptions(self, exc: BaseException):
        """Itera recursivamente por excepciones dentro de ExceptionGroup."""
        if isinstance(exc, BaseExceptionGroup):
            for sub in exc.exceptions:
                yield from self._iter_nested_exceptions(sub)
            return
        yield exc

    def _is_recoverable_live_error(self, exc: BaseException) -> bool:
        """Detecta cierres de sesión Live esperables (p.ej. code 1008 / policy)."""
        for sub in self._iter_nested_exceptions(exc):
            text = str(sub).lower()
            code = getattr(sub, "code", None)
            status_code = getattr(sub, "status_code", None)

            if code == 1008 or status_code == 1008:
                return True

            if "1008" in text and (
                "policy violation" in text
                or "operation is not implemented" in text
                or "not supported" in text
                or "not enabled" in text
            ):
                return True

            if "connectionclosed" in sub.__class__.__name__.lower() and "1008" in text:
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

        return types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            output_audio_transcription={},
            input_audio_transcription={},
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

    async def _execute_tool(self, fc) -> types.FunctionResponse:
        name = fc.name
        args = self._normalize_output_paths(name, dict(fc.args or {}))

        print(f"[REX] 🔧 {name}  {args}")
        self.ui.set_state("THINKING")
        self._tool_counter += 1
        start_progress = 25 + min(40, self._tool_counter * 12)
        self._advance_progress(start_progress, estado="En proceso", evento=f"Ejecutando herramienta: {name}")

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
                priority_map = {"low": TaskPriority.LOW, "normal": TaskPriority.NORMAL, "high": TaskPriority.HIGH}
                priority = priority_map.get(args.get("priority", "normal").lower(), TaskPriority.NORMAL)
                task_id = get_queue().submit(goal=args.get("goal", ""), priority=priority, speak=self.speak)
                result = f"Tarea iniciada (ID: {task_id})."
            elif name == "web_search":
                query = args.get("query", "").strip()
                items = args.get("items", [])
                resumen = query or ", ".join(items) or "consulta web"
                self._pending_web_search = {"args": args}
                self.ui.update_activity(
                    estado="En espera",
                    progreso=max(self._current_progress, 30),
                    evento="Esperando confirmación para búsqueda web"
                )
                self.ui.write_log(f"Rex: ¿Deseas que realice una búsqueda web sobre: '{resumen}'? Responde sí o no.")
                result = "Búsqueda web pendiente de confirmación del usuario (sí/no)."
            elif name == "file_processor":
                if not args.get("file_path") and self.ui.current_file:
                    args["file_path"] = self.ui.current_file
                r = await loop.run_in_executor(
                    None,
                    lambda: file_processor(parameters=args, player=self.ui, speak=self.speak)
                )
                result = r or "Hecho."
            elif name == "electronics":
                from actions.electronics import ElectronicsAction
                action_instance = ElectronicsAction()
                r = await loop.run_in_executor(
                    self.engineering_executor,
                    lambda: asyncio.run(action_instance.execute(parameters=args, player=self.ui, speak_callback=self.speak))
                )
                result = r or "Hecho."
            elif name == "engineering_report":
                from actions.engineering_report import engineering_report
                r = await loop.run_in_executor(
                    self.engineering_executor,
                    lambda: engineering_report(parameters=args, player=self.ui, speak=self.speak)
                )
                result = r or "Reporte de ingeniería generado."
            elif name == "matlab_link":
                from actions.matlab_link import MatlabLinkAction
                action_instance = MatlabLinkAction()
                r = await loop.run_in_executor(
                    self.engineering_executor,
                    lambda: asyncio.run(action_instance.execute(parameters=args, player=self.ui, speak_callback=self.speak))
                )
                result = r or "Hecho."
            elif name == "mecatronic_link":
                from actions.mecatronic_link import MecatronicLinkAction
                action_instance = MecatronicLinkAction()
                r = await loop.run_in_executor(
                    self.engineering_executor,
                    lambda: asyncio.run(action_instance.execute(parameters=args, player=self.ui, speak_callback=self.speak))
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
            self._advance_progress(end_progress, estado="En proceso", evento=f"Acción finalizada: {name}")

        print(f"[REX] 📤 {name} → {str(result)[:80]}")
        return types.FunctionResponse(
            id=fc.id, name=name,
            response={"result": result}
        )

    async def _send_realtime(self):
        while True:
            msg = await self.out_queue.get()
            await self.session.send_realtime_input(media=msg)

    async def _listen_audio(self):
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
                            txt = _clean_transcript(sc.output_transcription.text)
                            if txt:
                                out_buf.append(txt)

                        if sc.input_transcription and sc.input_transcription.text:
                            txt = _clean_transcript(sc.input_transcription.text)
                            if txt:
                                in_buf.append(txt)

                        if sc.turn_complete:
                            if self._turn_done_event:
                                self._turn_done_event.set()

                            full_in = " ".join(in_buf).strip()
                            if full_in:
                                self.ui.write_log(f"Usuario: {full_in}")
                                self.model.session_log.append({"role": "user", "text": full_in})
                            in_buf = []

                            full_out = " ".join(out_buf).strip()
                            if full_out:
                                self.ui.write_log(f"Rex: {full_out}")
                                self.model.session_log.append({"role": "rex", "text": full_out})
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
        self.ui.write_log("ACT: Audio estable activado (PCM16 alineado, baja latencia)")

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
                    self.audio_in_queue = asyncio.Queue()
                    self.out_queue = asyncio.Queue(maxsize=10)
                    self._turn_done_event = asyncio.Event()

                    print("[REX] ✅ Conectado....")
                    self.ui.set_state("LISTENING")
                    self.ui.write_log("SYS: REX está en línea.")

                    tg.create_task(self._send_realtime())
                    tg.create_task(self._listen_audio())
                    tg.create_task(self._receive_audio())
                    tg.create_task(self._play_audio())

            except Exception as e:
                recoverable = self._is_recoverable_live_error(e)
                print(f"[REX] ⚠️ {e}")
                if not recoverable:
                    traceback.print_exc()
                self.set_speaking(False)
                self.ui.set_state("THINKING")
                if recoverable:
                    self.ui.write_log("SYS: Sesión Live reiniciada por compatibilidad del servidor (reconectando).")
                else:
                    self.ui.write_log(f"SYS: Error de conexión — {str(e)[:120]}")
                self.ui.update_activity(estado="Error", progreso=0, evento="Error de conexión")
                retry = getattr(self, '_retry_count', 0)
                wait = min(3 * (2 ** retry), 60)
                self._retry_count = retry + 1
                print(f"[REX] 🔄 Reconectando en {wait}s... (intento {self._retry_count})")
                self.ui.write_log(f"SYS: Reconectando en {wait}s...")
                await asyncio.sleep(wait)
            else:
                self._retry_count = 0
