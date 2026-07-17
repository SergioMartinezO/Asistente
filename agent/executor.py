"""
Módulo Executor mejorado con comunicación estructurada por fases.
Informa al usuario: inicio de fase, avances, finalización y pregunta de verificación.
"""

import threading
import time
from typing import Callable, Any
from agent.planner import create_plan, replan
from agent.error_handler import analyze_error, ErrorDecision, generate_fix
from core.config import get_gemini_client


class PhaseReporter:
    """
    Gestor de reportes por fase con cola de voz para evitar cortes.
    Asegura que cada mensaje se reproduzca completamente antes del siguiente.
    """
    
    def __init__(self, speak_callback: Callable | None, ui=None):
        self._speak = speak_callback
        self._ui = ui
        self._queue_lock = threading.Lock()
        self._last_speak_time = 0
        self._min_interval = 0.5  # Segundos mínimos entre mensajes
        
    def report(self, message: str, phase: str = "", progress: int = -1):
        """
        Reporta un mensaje al usuario con control de timing.
        
        Args:
            message: El mensaje a comunicar
            phase: Nombre de la fase actual (para el log visual)
            progress: Porcentaje de progreso (0-100) o -1 si no aplica
        """
        # Actualizar UI si está disponible
        if self._ui and phase:
            try:
                self._ui.update_activity(
                    estado="En proceso",
                    progreso=progress if progress >= 0 else None,
                    evento=f"[{phase}] {message}"
                )
            except Exception:
                pass
        
        # Control de timing para evitar cortes de voz
        with self._queue_lock:
            current_time = time.time()
            elapsed = current_time - self._last_speak_time
            
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
            
            # Enviar mensaje a voz
            if self._speak and message:
                try:
                    self._speak(message)
                    self._last_speak_time = time.time()
                except Exception as e:
                    print(f"[PhaseReporter] ⚠️ Error al hablar: {e}")
    
    def phase_start(self, phase_name: str, description: str, total_steps: int):
        """Reporta el inicio de una nueva fase."""
        msg = f"Iniciando fase: {phase_name}. {description}. Total de pasos: {total_steps}."
        self.report(msg, phase=phase_name, progress=0)
    
    def phase_progress(self, phase_name: str, step_num: int, total_steps: int, description: str):
        """Reporta el avance dentro de una fase."""
        percent = int((step_num / max(1, total_steps)) * 100)
        msg = f"Paso {step_num} de {total_steps}: {description}."
        self.report(msg, phase=phase_name, progress=percent)
    
    def phase_complete(self, phase_name: str, summary: str):
        """Reporta la finalización de una fase."""
        msg = f"Fase {phase_name} completada. {summary}"
        self.report(msg, phase=phase_name, progress=100)
    
    def task_complete(self, goal: str, ask_verify: bool = True):
        """Reporta la finalización de toda la tarea y pregunta si desea verificar."""
        msg = f"Tarea completada exitosamente para: {goal[:80]}."
        if ask_verify:
            msg += " ¿Deseas que verifique el resultado ahora?"
        self.report(msg, phase="Finalización", progress=100)
    
    def task_error(self, error_msg: str):
        """Reporta un error en la tarea."""
        msg = f"Error en la tarea: {error_msg}"
        self.report(msg, phase="Error", progress=0)


def _call_tool(tool: str, parameters: dict, speak: Callable | None) -> str:
    """Llama a una herramienta específica con los parámetros dados."""
    if tool == "open_app":
        from actions.open_app import open_app
        return open_app(parameters=parameters, player=None) or "Hecho."
    elif tool == "web_search":
        from actions.web_search import web_search
        return web_search(parameters=parameters, player=None) or "Hecho."
    elif tool == "file_controller":
        from actions.file_controller import file_controller
        return file_controller(parameters=parameters, player=None) or "Hecho."
    elif tool == "browser_control":
        from actions.browser_control import browser_control
        return browser_control(parameters=parameters, player=None) or "Hecho."
    elif tool == "computer_control":
        from actions.computer_control import computer_control
        return computer_control(parameters=parameters, player=None) or "Hecho."
    elif tool == "computer_settings":
        from actions.computer_settings import computer_settings
        return computer_settings(parameters=parameters, player=None) or "Hecho."
    elif tool == "send_message":
        from actions.send_message import send_message
        return send_message(parameters=parameters, response=None, player=None, session_memory=None) or "Hecho."
    elif tool == "reminder":
        from actions.reminder import reminder
        return reminder(parameters=parameters, response=None, player=None) or "Hecho."
    elif tool == "youtube_video":
        from actions.youtube_video import youtube_video
        return youtube_video(parameters=parameters, response=None, player=None) or "Hecho."
    elif tool == "desktop_control":
        from actions.desktop import desktop_control
        return desktop_control(parameters=parameters, player=None) or "Hecho."
    elif tool == "weather_report":
        from actions.weather_report import weather_action
        return weather_action(parameters=parameters, player=None) or "Hecho."
    elif tool == "code_helper":
        from actions.code_helper import code_helper
        return code_helper(parameters=parameters, player=None, speak=speak) or "Hecho."
    elif tool == "dev_agent":
        from actions.dev_agent import dev_agent
        return dev_agent(parameters=parameters, player=None, speak=speak) or "Hecho."
    elif tool == "game_updater":
        from actions.game_updater import game_updater
        return game_updater(parameters=parameters, player=None, speak=speak) or "Hecho."
    elif tool == "dev_tools":
        from actions.dev_tools import dev_tools
        return dev_tools(parameters=parameters, player=None, speak=speak) or "Hecho."
    elif tool == "mechatronics":
        from actions.mechatronics import mechatronics
        return mechatronics(parameters=parameters, player=None, speak=speak) or "Hecho."
    elif tool == "datasheet_finder":
        from actions.datasheet_finder import datasheet_finder
        return datasheet_finder(parameters=parameters, player=None, speak=speak) or "Hecho."
    elif tool == "materials_science":
        from actions.materials_science import materials_science
        return materials_science(parameters=parameters, player=None, speak=speak) or "Hecho."
    elif tool == "proteus_automation":
        from actions.proteus_automation import proteus_automation
        return proteus_automation(parameters=parameters, player=None, speak=speak) or "Hecho."
    elif tool == "ltspice_automation":
        from actions.ltspice_automation import ltspice_automation
        return ltspice_automation(parameters=parameters, player=None, speak=speak) or "Hecho."
    elif tool == "flight_finder":
        from actions.flight_finder import flight_finder
        return flight_finder(parameters=parameters, player=None) or "Hecho."
    elif tool == "screen_process":
        from actions.screen_process import screen_process
        return screen_process(parameters=parameters, player=None) or "Hecho."
    else:
        raise ValueError(f"Unknown tool '{tool}'. Security policy blocks implicit code execution fallback.")


def _inject_context(params: dict, tool: str, step_results: dict, goal: str = "") -> dict:
    """Inyecta contexto previo en los parámetros si es necesario."""
    # Implementación básica - puedes expandir según necesidades
    return params


class AgentExecutor:
    """
    Ejecutor de tareas con comunicación estructurada por fases.
    Informa al usuario sobre: inicio, avances, finalización y verificación.
    """
    
    MAX_REPLAN_ATTEMPTS = 2
    
    def execute(
        self,
        goal: str,
        speak: Callable | None = None,
        cancel_flag: threading.Event | None = None,
        ui=None,
    ) -> str:
        """
        Ejecuta una tarea completa con reportes de progreso estructurados.
        
        Args:
            goal: Descripción de la tarea a realizar
            speak: Callback para comunicación por voz
            cancel_flag: Evento para cancelación externa
            ui: Referencia a la UI para actualizaciones visuales
        
        Returns:
            str: Resumen de la ejecución
        """
        print(f"\n[Executor] 🎯 Goal: {goal}")
        
        # Inicializar reportero de fases
        reporter = PhaseReporter(speak_callback=speak, ui=ui)
        
        # ===== FASE 1: PLANIFICACIÓN =====
        reporter.phase_start("Planificación", "Analizando objetivo y creando plan de acción", 1)
        
        plan = create_plan(goal)
        steps = plan.get("steps", [])
        
        if not steps:
            error_msg = "No pude crear un plan válido para esta tarea."
            reporter.task_error(error_msg)
            return error_msg
        
        total_steps = len(steps)
        reporter.phase_complete("Planificación", f"Plan creado con {total_steps} pasos identificados.")
        
        # ===== FASE 2: EJECUCIÓN =====
        reporter.phase_start("Ejecución", f"Ejecutando {total_steps} pasos del plan", total_steps)
        
        replan_attempts = 0
        completed_steps = []
        step_results = {}
        
        while True:
            steps = plan.get("steps", [])
            if not steps:
                msg = "No pude crear un plan válido para esta tarea."
                reporter.task_error(msg)
                return msg
            
            total_steps = max(1, len(steps))
            success = True
            failed_step = None
            failed_error = ""
            
            for idx, step in enumerate(steps):
                # Verificar cancelación
                if cancel_flag and cancel_flag.is_set():
                    reporter.report("Tarea cancelada por el usuario.", phase="Cancelación")
                    return "Tarea cancelada."
                
                step_num = step.get("step", idx + 1)
                tool = step.get("tool", "web_search")
                desc = step.get("description", "")
                params = step.get("parameters", {})
                params = _inject_context(params, tool, step_results, goal=goal)
                
                print(f"\n[Executor] ▶️ Step {step_num}: [{tool}] {desc}")
                
                # Reportar inicio del paso
                reporter.phase_progress("Ejecución", idx + 1, total_steps, desc)
                
                # Intentar ejecutar el paso con reintentos
                attempt = 1
                step_ok = False
                max_attempts = 3
                
                while attempt <= max_attempts:
                    if cancel_flag and cancel_flag.is_set():
                        break
                    
                    try:
                        result = _call_tool(tool, params, speak)
                        step_results[step_num] = result
                        completed_steps.append(step)
                        print(f"[Executor] ✅ Step {step_num} done: {str(result)[:100]}")
                        step_ok = True
                        break
                        
                    except Exception as e:
                        error_msg = str(e)
                        print(f"[Executor] ❌ Step {step_num} attempt {attempt} failed: {error_msg}")
                        
                        # Analizar error y decidir acción
                        recovery = analyze_error(step, error_msg, attempt=attempt)
                        decision = recovery["decision"]
                        user_msg = recovery.get("user_message", "")
                        
                        if speak and user_msg:
                            reporter.report(user_msg, phase=f"Paso {step_num}")
                        
                        if decision == ErrorDecision.RETRY:
                            reporter.report(
                                f"Reintentando paso {step_num}. Intento {attempt + 1} de {max_attempts}.",
                                phase=f"Paso {step_num}"
                            )
                            attempt += 1
                            time.sleep(2)
                            continue
                            
                        elif decision == ErrorDecision.SKIP:
                            print(f"[Executor] ⏭️ Skipping step {step_num}")
                            reporter.report(
                                f"Paso {step_num} omitido por no ser crítico.",
                                phase=f"Paso {step_num}"
                            )
                            completed_steps.append(step)
                            step_ok = True
                            break
                            
                        elif decision == ErrorDecision.ABORT:
                            abort_msg = f"Tarea abortada. {recovery.get('reason', '')}"
                            reporter.task_error(abort_msg)
                            return abort_msg
                            
                        else:
                            # Intentar fix alternativo
                            fix_suggestion = recovery.get("fix_suggestion", "")
                            if fix_suggestion and tool != "generated_code":
                                try:
                                    reporter.report(
                                        f"Intentando enfoque alternativo para paso {step_num}.",
                                        phase=f"Paso {step_num}"
                                    )
                                    fixed_step = generate_fix(step, error_msg, fix_suggestion)
                                    res = _call_tool(
                                        fixed_step["tool"],
                                        fixed_step["parameters"],
                                        speak
                                    )
                                    step_results[step_num] = res
                                    completed_steps.append(step)
                                    step_ok = True
                                    break
                                except Exception as fix_err:
                                    print(f"[Executor] ⚠️ Fix failed: {fix_err}")
                                    failed_step = step
                                    failed_error = error_msg
                                    success = False
                                    break
                
                if not step_ok and not failed_step:
                    failed_step = step
                    failed_error = "Max retries exceeded"
                    success = False
                
                if not success:
                    break
            
            # ===== RESULTADO DE EJECUCIÓN =====
            if success:
                # ===== FASE 3: RESUMEN Y VERIFICACIÓN =====
                reporter.phase_complete("Ejecución", f"Completados {len(completed_steps)} de {total_steps} pasos.")
                
                # Generar resumen final
                summary = self._summarize(goal, completed_steps, speak)
                
                # Preguntar al usuario si desea verificar el resultado
                reporter.task_complete(goal, ask_verify=True)
                
                return summary
            
            # ===== REPLANIFICACIÓN =====
            if replan_attempts >= self.MAX_REPLAN_ATTEMPTS:
                error_msg = f"La tarea falló tras {replan_attempts} replanificaciones."
                reporter.task_error(error_msg)
                return error_msg
            
            reporter.report(
                f"Error detectado. Replanificando enfoque. Intento {replan_attempts + 1} de {self.MAX_REPLAN_ATTEMPTS}.",
                phase="Replanificación"
            )
            
            replan_attempts += 1
            plan = replan(goal, completed_steps, failed_step, failed_error)
    
    def _summarize(self, goal: str, completed_steps: list, speak: Callable | None) -> str:
        """Genera un resumen natural de la tarea completada."""
        fallback = f"Listo. Se completaron {len(completed_steps)} pasos para: {goal[:60]}."
        
        try:
            client = get_gemini_client()
            steps_str = "\n".join(f"- {s.get('description', '')}" for s in completed_steps)
            
            prompt = (
                f'User goal: "{goal}"\n'
                f"Completed steps:\n{steps_str}\n\n"
                "Write a single natural sentence summarizing what was accomplished in Spanish. "
                "Be direct, positive, and avoid honorifics. Keep it under 30 words."
            )
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            summary = response.text.strip()
            
            if speak:
                speak(summary)
            
            return summary
            
        except Exception as e:
            print(f"[Executor] ⚠️ Summary generation failed: {e}")
            if speak:
                speak(fallback)
            return fallback