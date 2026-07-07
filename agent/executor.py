import json
import re
import threading
from pathlib import Path
from typing import Callable

from agent.planner       import create_plan, replan
from agent.error_handler import analyze_error, generate_fix, ErrorDecision


from core.config import get_gemini_client

def _inject_context(params: dict, tool: str, step_results: dict, goal: str = "") -> dict:
    if not step_results:
        return params

    params = dict(params)

    if tool == "file_controller" and params.get("action") in ("write", "create_file"):
        content = params.get("content", "")
        if not content or len(content) < 50:
            all_results = [
                v for v in step_results.values()
                if v and len(v) > 100 and v not in ("Done.", "Completed.")
            ]
            if all_results:
                combined = "\n\n---\n\n".join(all_results)
                translated = _translate_to_goal_language(combined, goal)
                params["content"] = translated
                print(f"[Executor] 💉 Injected + translated content")

    return params
def _detect_language(text: str) -> str:
    client = get_gemini_client()
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=(
                f"What language is this text written in? "
                f"Reply with ONLY the language name in English (e.g. Turkish, English, French).\n\n"
                f"Text: {text[:200]}"
            )
        )
        return response.text.strip()
    except Exception:
        return "English"


def _translate_to_goal_language(content: str, goal: str) -> str:
    if not goal:
        return content
    try:
        client = get_gemini_client()

        target_lang = _detect_language(goal)
        print(f"[Executor] 🌐 Translating to: {target_lang}")

        prompt = (
            f"You are a professional translator. "
            f"Translate the following text into {target_lang}.\n"
            f"IMPORTANT:\n"
            f"- Translate EVERYTHING, leave nothing in English\n"
            f"- Keep all facts, numbers, and data intact\n"
            f"- Keep the structure and formatting\n"
            f"- Output ONLY the translated text, nothing else\n\n"
            f"Text to translate:\n{content[:4000]}"
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        translated = response.text.strip()
        print(f"[Executor] ✅ Translation done ({target_lang})")
        return translated
    except Exception as e:
        print(f"[Executor] ⚠️ Translation failed: {e}")
        return content

def _call_tool(tool: str, parameters: dict, speak: Callable | None) -> str:

    if tool == "open_app":
        from actions.open_app import open_app
        return open_app(parameters=parameters, player=None) or "Done."

    elif tool == "web_search":
        from actions.web_search import web_search
        return web_search(parameters=parameters, player=None) or "Done."
    elif tool == "game_updater":
        from actions.game_updater import game_updater
        return game_updater(parameters=parameters, player=None, speak=speak) or "Done."
    elif tool == "browser_control":
        from actions.browser_control import browser_control
        return browser_control(parameters=parameters, player=None) or "Done."

    elif tool == "file_controller":
        from actions.file_controller import file_controller
        return file_controller(parameters=parameters, player=None) or "Done."

    elif tool == "code_helper":
        from actions.code_helper import code_helper
        return code_helper(parameters=parameters, player=None, speak=speak) or "Done."

    elif tool == "dev_agent":
        from actions.dev_agent import dev_agent
        return dev_agent(parameters=parameters, player=None, speak=speak) or "Done."

    elif tool == "screen_process":
        from actions.screen_processor import screen_process
        screen_process(parameters=parameters, player=None)
        return "Screen captured and analyzed."

    elif tool == "send_message":
        from actions.send_message import send_message
        return send_message(parameters=parameters, player=None) or "Done."

    elif tool == "reminder":
        from actions.reminder import reminder
        return reminder(parameters=parameters, player=None) or "Done."

    elif tool == "youtube_video":
        from actions.youtube_video import youtube_video
        return youtube_video(parameters=parameters, player=None) or "Done."

    elif tool == "permission_check":
        from actions.permission_check import permission_check
        return permission_check(parameters=parameters) or "Done."

    elif tool == "weather_report":
        from actions.weather_report import weather_action
        return weather_action(parameters=parameters, player=None) or "Done."

    elif tool == "computer_settings":
        from actions.computer_settings import computer_settings
        return computer_settings(parameters=parameters, player=None) or "Done."

    elif tool == "desktop_control":
        from actions.desktop import desktop_control
        return desktop_control(parameters=parameters, player=None) or "Done."

    elif tool == "computer_control":
        from actions.computer_control import computer_control
        return computer_control(parameters=parameters, player=None) or "Done."

    elif tool == "generated_code":
        raise RuntimeError(
            "Tool 'generated_code' is disabled for security reasons. "
            "Use explicit tools like web_search, file_controller, code_helper, or dev_agent."
        )

    elif tool == "flight_finder":
        from actions.flight_finder import flight_finder
        return flight_finder(parameters=parameters, player=None, speak=speak) or "Done."

    elif tool == "electronics":
        from actions.electronics import electronics
        return electronics(parameters=parameters, player=None, speak=speak) or "Done."

    elif tool == "mechatronics":
        from actions.mechatronics import mechatronics
        return mechatronics(parameters=parameters, player=None, speak=speak) or "Done."

    elif tool == "datasheet_finder":
        from actions.datasheet_finder import datasheet_finder
        return datasheet_finder(parameters=parameters, player=None, speak=speak) or "Done."

    elif tool == "materials_science":
        from actions.materials_science import materials_science
        return materials_science(parameters=parameters, player=None, speak=speak) or "Done."

    elif tool == "proteus_automation":
        from actions.proteus_automation import proteus_automation
        return proteus_automation(parameters=parameters, player=None, speak=speak) or "Done."

    elif tool == "ltspice_automation":
        from actions.ltspice_automation import ltspice_automation
        return ltspice_automation(parameters=parameters, player=None, speak=speak) or "Done."

    else:
        raise ValueError(f"Unknown tool '{tool}'. Security policy blocks implicit code execution fallback.")

class AgentExecutor:

    MAX_REPLAN_ATTEMPTS = 2

    def execute(
        self,
        goal:        str,
        speak:       Callable | None        = None,
        cancel_flag: threading.Event | None = None,
    ) -> str:
        print(f"\n[Executor] 🎯 Goal: {goal}")

        def _say(msg: str):
            if speak and msg:
                try:
                    speak(msg)
                except Exception:
                    pass

        def _progress(phase: str, status: str, percent: int, next_action: str):
            percent = max(0, min(100, int(percent)))
            _say(
                f"Fase: {phase}. "
                f"Estado: {status}. "
                f"Avance: {percent} por ciento. "
                f"Siguiente acción: {next_action}."
            )

        replan_attempts = 0
        completed_steps = []
        step_results    = {} 
        plan            = create_plan(goal)

        _progress(
            "Planificación",
            "en curso",
            5,
            "validar el plan inicial por fases"
        )

        while True:
            steps = plan.get("steps", [])

            if not steps:
                msg = "No pude crear un plan válido para esta tarea."
                if speak: speak(msg)
                return msg

            total_steps = max(1, len(steps))
            _progress(
                "Planificación",
                "confirmada",
                15,
                f"ejecutar {len(steps)} paso{'s' if len(steps) != 1 else ''} del plan"
            )

            success      = True
            failed_step  = None
            failed_error = ""

            for step in steps:
                if cancel_flag and cancel_flag.is_set():
                    if speak: speak("Tarea cancelada.")
                    return "Tarea cancelada."

                step_num = step.get("step", "?")
                tool     = step.get("tool", "web_search")
                desc     = step.get("description", "")
                params   = step.get("parameters", {})

                params = _inject_context(params, tool, step_results, goal=goal)

                print(f"\n[Executor] ▶️ Step {step_num}: [{tool}] {desc}")
                try:
                    step_idx = int(step_num)
                except Exception:
                    step_idx = len(completed_steps) + 1
                start_pct = 15 + int(((max(1, step_idx) - 1) / total_steps) * 70)
                _progress(
                    f"Ejecución del paso {step_num}",
                    "en curso",
                    start_pct,
                    desc or f"ejecutar herramienta {tool}"
                )

                attempt = 1
                step_ok = False

                while attempt <= 3:
                    if cancel_flag and cancel_flag.is_set():
                        break
                    try:
                        result = _call_tool(tool, params, speak)
                        step_results[step_num] = result 
                        completed_steps.append(step)
                        print(f"[Executor] ✅ Step {step_num} done: {str(result)[:100]}")
                        done_pct = 15 + int((len(completed_steps) / total_steps) * 70)
                        _progress(
                            f"Ejecución del paso {step_num}",
                            "confirmada",
                            done_pct,
                            "continuar con el siguiente paso del plan"
                        )
                        step_ok = True
                        break

                    except Exception as e:
                        error_msg = str(e)
                        print(f"[Executor] ❌ Step {step_num} attempt {attempt} failed: {error_msg}")

                        recovery = analyze_error(step, error_msg, attempt=attempt)
                        decision = recovery["decision"]
                        user_msg = recovery.get("user_message", "")

                        if speak and user_msg:
                            speak(user_msg)

                        if decision == ErrorDecision.RETRY:
                            _progress(
                                f"Ejecución del paso {step_num}",
                                "bloqueada",
                                start_pct,
                                "reintentar con ajuste automático"
                            )
                            attempt += 1
                            import time; time.sleep(2)
                            continue

                        elif decision == ErrorDecision.SKIP:
                            print(f"[Executor] ⏭️ Skipping step {step_num}")
                            _progress(
                                f"Ejecución del paso {step_num}",
                                "confirmada",
                                start_pct,
                                "continuar con el siguiente paso porque no era crítico"
                            )
                            completed_steps.append(step)
                            step_ok = True
                            break

                        elif decision == ErrorDecision.ABORT:
                            msg = f"Tarea abortada. {recovery.get('reason', '')}"
                            if speak: speak(msg)
                            return msg

                        else: 
                            fix_suggestion = recovery.get("fix_suggestion", "")
                            if fix_suggestion and tool != "generated_code":
                                try:
                                    fixed_step = generate_fix(step, error_msg, fix_suggestion)
                                    if speak: speak("Intentando un enfoque alternativo.")
                                    res = _call_tool(
                                        fixed_step["tool"],
                                        fixed_step["parameters"],
                                        speak
                                    )
                                    step_results[step_num] = res
                                    completed_steps.append(step)
                                    done_pct = 15 + int((len(completed_steps) / total_steps) * 70)
                                    _progress(
                                        f"Ejecución del paso {step_num}",
                                        "confirmada",
                                        done_pct,
                                        "continuar tras recuperación con enfoque alternativo"
                                    )
                                    step_ok = True
                                    break
                                except Exception as fix_err:
                                    print(f"[Executor] ⚠️ Fix failed: {fix_err}")

                            failed_step  = step
                            failed_error = error_msg
                            success      = False
                            break

                if not step_ok and not failed_step:
                    failed_step  = step
                    failed_error = "Max retries exceeded"
                    success      = False

                if not success:
                    break

            if success:
                _progress(
                    "Ejecución",
                    "confirmada",
                    90,
                    "emitir resumen final de pasos realizados"
                )
                return self._summarize(goal, completed_steps, speak)

            if replan_attempts >= self.MAX_REPLAN_ATTEMPTS:
                msg = f"La tarea falló tras {replan_attempts} replanificaciones."
                if speak: speak(msg)
                return msg

            if speak: speak("Ajustando el enfoque.")
            _progress(
                "Replanificación",
                "en curso",
                35,
                "recalcular plan restante y retomar ejecución"
            )

            replan_attempts += 1
            plan = replan(goal, completed_steps, failed_step, failed_error)

    def _summarize(self, goal: str, completed_steps: list, speak: Callable | None) -> str:
        fallback = f"Listo. Se completaron {len(completed_steps)} pasos para: {goal[:60]}."
        try:
            client = get_gemini_client()
            steps_str = "\n".join(f"- {s.get('description', '')}" for s in completed_steps)
            prompt    = (
                f'User goal: "{goal}"\n'
                f"Completed steps:\n{steps_str}\n\n"
                "Write a single natural sentence summarizing what was accomplished in Spanish. "
                "Be direct, positive, and avoid honorifics."
            )
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            summary  = response.text.strip()
            if speak: speak(summary)
            return summary
        except Exception:
            if speak: speak(fallback)
            return fallback