import asyncio
import re
import threading
import traceback
import sounddevice as sd
import google.genai as genai
from google.genai import types

from ui import JarvisUI
from model import JarvisModel

# Importar las declaraciones de herramientas (reutilizadas del main original o importadas)
# Para evitar duplicar el bloque gigante de TOOL_DECLARATIONS, las importaremos o las volveremos a declarar.
# Definiremos las declaraciones de herramientas requeridas por Gemini.
from main import TOOL_DECLARATIONS, _load_system_prompt

LIVE_MODEL = "models/gemini-2.5-flash-native-audio-preview-12-2025"
CHANNELS = 1
SEND_SAMPLE_RATE = 16_000
RECEIVE_SAMPLE_RATE = 24_000
CHUNK_SIZE = 4096

_CTRL_RE = re.compile(r"<ctrl\d+>", re.IGNORECASE)

def _clean_transcript(text: str) -> str:
    text = _CTRL_RE.sub("", text)
    text = re.sub(r"[\x00-\x08\x0b-\x1f]", "", text)
    return text.strip()

class JarvisController:
    def __init__(self, model: JarvisModel, ui: JarvisUI):
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
        
        # Servicio de Ingeniería asíncrono para cálculos complejos
        from concurrent.futures import ThreadPoolExecutor
        self.engineering_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="JarvisEngineering")
        
        # Conectar callbacks de la Vista
        self.ui.on_text_command = self._on_text_command
        self.ui.on_setup_done = self._on_setup_done
        
        # Iniciar monitor de hardware
        self.model.start_metrics_monitoring()
        
        # Hilo de actualización de métricas UI
        self._metrics_thread_running = True
        self._metrics_thread = threading.Thread(target=self._metrics_update_loop, daemon=True)
        self._metrics_thread.start()

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
        asyncio.run_coroutine_threadsafe(
            self.session.send_client_content(
                turns={"parts": [{"text": text}]},
                turn_complete=True
            ),
            self._loop
        )

    def set_speaking(self, value: bool):
        with self._speaking_lock:
            self._is_speaking = value
        if value:
            self.ui.set_state("SPEAKING")
        elif not self.ui.muted:
            self.ui.set_state("LISTENING")

    def speak(self, text: str):
        self._on_text_command(text)

    def speak_error(self, tool_name: str, error: str):
        short = str(error)[:120]
        self.ui.write_log(f"ERR: {tool_name} — {short}")
        self.speak(f"Sir, {tool_name} encountered an error. {short}")

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
            session_resumption=types.SessionResumptionConfig(),
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
        args = dict(fc.args or {})

        print(f"[JARVIS] 🔧 {name}  {args}")
        self.ui.set_state("THINKING")

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
        result = "Done."

        # Importar dinámicamente las herramientas correspondientes
        from actions.file_processor import file_processor
        from actions.flight_finder import flight_finder
        from actions.electronics import electronics
        from actions.dev_tools import dev_tools
        from actions.mechatronics import mechatronics
        from actions.open_app import open_app
        from actions.weather_report import weather_action
        from actions.send_message import send_message
        from actions.reminder import reminder
        from actions.computer_settings import computer_settings
        from actions.screen_processor import screen_process
        from actions.youtube_video import youtube_video
        from actions.desktop import desktop_control
        from actions.browser_control import browser_control
        from actions.file_controller import file_controller
        from actions.code_helper import code_helper
        from actions.dev_agent import dev_agent
        from actions.web_search import web_search as web_search_action
        from actions.computer_control import computer_control
        from actions.game_updater import game_updater
        from actions.datasheet_finder import datasheet_finder
        from actions.materials_science import materials_science
        from actions.proteus_automation import proteus_automation
        from actions.ltspice_automation import ltspice_automation

        try:
            if name == "open_app":
                r = await loop.run_in_executor(None, lambda: open_app(parameters=args, response=None, player=self.ui))
                result = r or f"Opened {args.get('app_name')}."
            elif name == "weather_report":
                r = await loop.run_in_executor(None, lambda: weather_action(parameters=args, player=self.ui))
                result = r or "Weather delivered."
            elif name == "browser_control":
                r = await loop.run_in_executor(None, lambda: browser_control(parameters=args, player=self.ui))
                result = r or "Done."
            elif name == "file_controller":
                r = await loop.run_in_executor(None, lambda: file_controller(parameters=args, player=self.ui))
                result = r or "Done."
            elif name == "send_message":
                r = await loop.run_in_executor(None, lambda: send_message(parameters=args, response=None, player=self.ui, session_memory=None))
                result = r or f"Message sent to {args.get('receiver')}."
            elif name == "reminder":
                r = await loop.run_in_executor(None, lambda: reminder(parameters=args, response=None, player=self.ui))
                result = r or "Reminder set."
            elif name == "youtube_video":
                r = await loop.run_in_executor(None, lambda: youtube_video(parameters=args, response=None, player=self.ui))
                result = r or "Done."
            elif name == "screen_process":
                threading.Thread(
                    target=screen_process,
                    kwargs={"parameters": args, "response": None,
                            "player": self.ui, "session_memory": None},
                    daemon=True
                ).start()
                result = "Vision module activated. Stay completely silent — vision module will speak directly."
            elif name == "computer_settings":
                r = await loop.run_in_executor(None, lambda: computer_settings(parameters=args, response=None, player=self.ui))
                result = r or "Done."
            elif name == "desktop_control":
                r = await loop.run_in_executor(None, lambda: desktop_control(parameters=args, player=self.ui))
                result = r or "Done."
            elif name == "code_helper":
                r = await loop.run_in_executor(None, lambda: code_helper(parameters=args, player=self.ui, speak=self.speak))
                result = r or "Done."
            elif name == "dev_agent":
                r = await loop.run_in_executor(None, lambda: dev_agent(parameters=args, player=self.ui, speak=self.speak))
                result = r or "Done."
            elif name == "agent_task":
                from agent.task_queue import get_queue, TaskPriority
                priority_map = {"low": TaskPriority.LOW, "normal": TaskPriority.NORMAL, "high": TaskPriority.HIGH}
                priority = priority_map.get(args.get("priority", "normal").lower(), TaskPriority.NORMAL)
                task_id = get_queue().submit(goal=args.get("goal", ""), priority=priority, speak=self.speak)
                result = f"Task started (ID: {task_id})."
            elif name == "web_search":
                r = await loop.run_in_executor(None, lambda: web_search_action(parameters=args, player=self.ui))
                result = r or "Done."
            elif name == "file_processor":
                if not args.get("file_path") and self.ui.current_file:
                    args["file_path"] = self.ui.current_file
                r = await loop.run_in_executor(
                    None,
                    lambda: file_processor(parameters=args, player=self.ui, speak=self.speak)
                )
                result = r or "Done."
            elif name == "computer_control":
                r = await loop.run_in_executor(None, lambda: computer_control(parameters=args, player=self.ui))
                result = r or "Done."
            elif name == "game_updater":
                r = await loop.run_in_executor(None, lambda: game_updater(parameters=args, player=self.ui, speak=self.speak))
                result = r or "Done."
            elif name == "electronics":
                from actions.electronics import ElectronicsAction
                action_instance = ElectronicsAction()
                r = await loop.run_in_executor(
                    self.engineering_executor,
                    lambda: asyncio.run(action_instance.execute(parameters=args, player=self.ui, speak_callback=self.speak))
                )
                result = r or "Done."
            elif name == "dev_tools":
                r = await loop.run_in_executor(None, lambda: dev_tools(parameters=args, player=self.ui, speak=self.speak))
                result = r or "Done."
            elif name == "mechatronics":
                r = await loop.run_in_executor(None, lambda: mechatronics(parameters=args, player=self.ui, speak=self.speak))
                result = r or "Done."
            elif name == "datasheet_finder":
                r = await loop.run_in_executor(None, lambda: datasheet_finder(parameters=args, player=self.ui, speak=self.speak))
                result = r or "Done."
            elif name == "materials_science":
                r = await loop.run_in_executor(None, lambda: materials_science(parameters=args, player=self.ui, speak=self.speak))
                result = r or "Done."
            elif name == "proteus_automation":
                r = await loop.run_in_executor(None, lambda: proteus_automation(parameters=args, player=self.ui, speak=self.speak))
                result = r or "Done."
            elif name == "ltspice_automation":
                r = await loop.run_in_executor(None, lambda: ltspice_automation(parameters=args, player=self.ui, speak=self.speak))
                result = r or "Done."
            elif name == "matlab_link":
                from actions.matlab_link import MatlabLinkAction
                action_instance = MatlabLinkAction()
                r = await loop.run_in_executor(
                    self.engineering_executor,
                    lambda: asyncio.run(action_instance.execute(parameters=args, player=self.ui, speak_callback=self.speak))
                )
                result = r or "Done."
            elif name == "mecatronic_link":
                from actions.mecatronic_link import MecatronicLinkAction
                action_instance = MecatronicLinkAction()
                r = await loop.run_in_executor(
                    self.engineering_executor,
                    lambda: asyncio.run(action_instance.execute(parameters=args, player=self.ui, speak_callback=self.speak))
                )
                result = r or "Done."
            elif name == "flight_finder":
                r = await loop.run_in_executor(None, lambda: flight_finder(parameters=args, player=self.ui))
                result = r or "Done."
            elif name == "shutdown_jarvis":
                self.ui.write_log("SYS: Shutdown requested.")
                self.model.save_conversation_session()
                self.speak("Hasta luego. Sesión guardada.")
                def _shutdown():
                    import time, os
                    time.sleep(2)
                    self.model.stop_metrics_monitoring()
                    self._metrics_thread_running = False
                    os._exit(0)
                threading.Thread(target=_shutdown, daemon=True).start()
            else:
                result = f"Unknown tool: {name}"
        except Exception as e:
            result = f"Tool '{name}' failed: {e}"
            traceback.print_exc()
            self.speak_error(name, e)

        if not self.ui.muted:
            self.ui.set_state("ESCUCHANDO Y ANALIZANDO")

        print(f"[JARVIS] 📤 {name} → {str(result)[:80]}")
        return types.FunctionResponse(
            id=fc.id, name=name,
            response={"result": result}
        )

    async def _send_realtime(self):
        while True:
            msg = await self.out_queue.get()
            await self.session.send_realtime_input(media=msg)

    async def _listen_audio(self):
        print("[JARVIS] 🎤 Mic started")
        loop = asyncio.get_event_loop()

        def callback(indata, frames, time_info, status):
            with self._speaking_lock:
                jarvis_speaking = self._is_speaking
            if not jarvis_speaking and not self.ui.muted:
                data = indata.tobytes()
                loop.call_soon_threadsafe(
                    self.out_queue.put_nowait,
                    {"data": data, "mime_type": "audio/pcm"}
                )

        try:
            with sd.InputStream(
                samplerate=SEND_SAMPLE_RATE,
                channels=CHANNELS,
                dtype="int16",
                blocksize=CHUNK_SIZE,
                callback=callback,
            ):
                print("[JARVIS] 🎤 Mic stream open")
                while True:
                    await asyncio.sleep(0.1)
        except Exception as e:
            print(f"[JARVIS] ❌ Mic: {e}")
            raise

    async def _receive_audio(self):
        print("[JARVIS] 👂 Recv started")
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
                                self.ui.write_log(f"You: {full_in}")
                                self.model.session_log.append({"role": "user", "text": full_in})
                            in_buf = []

                            full_out = " ".join(out_buf).strip()
                            if full_out:
                                self.ui.write_log(f"Jarvis: {full_out}")
                                self.model.session_log.append({"role": "jarvis", "text": full_out})
                            out_buf = []

                    if response.tool_call:
                        fn_responses = []
                        for fc in response.tool_call.function_calls:
                            print(f"[JARVIS] 📞 {fc.name}")
                            fr = await self._execute_tool(fc)
                            fn_responses.append(fr)
                        await self.session.send_tool_response(
                            function_responses=fn_responses
                        )
        except Exception as e:
            print(f"[JARVIS] ❌ Recv: {e}")
            traceback.print_exc()
            raise

    async def _play_audio(self):
        print("[JARVIS] 🔊 Play started")

        stream = sd.RawOutputStream(
            samplerate=RECEIVE_SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            blocksize=CHUNK_SIZE,
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
                await asyncio.to_thread(stream.write, chunk)
        except Exception as e:
            print(f"[JARVIS] ❌ Play: {e}")
            raise
        finally:
            self.set_speaking(False)
            stream.stop()
            stream.close()

    async def run(self):
        # Auto-guardar sesión en caso de desconexiones repentinas
        import atexit
        atexit.register(self.model.save_conversation_session)
        
        client = genai.Client(
            api_key=self.model.get_gemini_api_key(),
            http_options={"api_version": "v1beta"}
        )

        while True:
            try:
                print("[JARVIS] 🔌 Conectando...")
                self.ui.set_state("Pensando....")
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

                    print("[JARVIS] ✅ Conectado....")
                    self.ui.set_state("Escuchando y Analizando")
                    self.ui.write_log("SYS: JARVIS esta en linea.")

                    tg.create_task(self._send_realtime())
                    tg.create_task(self._listen_audio())
                    tg.create_task(self._receive_audio())
                    tg.create_task(self._play_audio())

            except Exception as e:
                print(f"[JARVIS] ⚠️ {e}")
                traceback.print_exc()
                self.set_speaking(False)
                self.ui.set_state("Pensando")
                retry = getattr(self, '_retry_count', 0)
                wait = min(3 * (2 ** retry), 60)
                self._retry_count = retry + 1
                print(f"[JARVIS] 🔄 Reconectando en {wait}s... (intento {self._retry_count})")
                self.ui.write_log(f"SYS: Reconectando en {wait}s...")
                await asyncio.sleep(wait)
            else:
                self._retry_count = 0
