import json
import os
import platform
import sys
from pathlib import Path
import threading
from memory.memory_manager import load_memory, update_memory, format_memory_for_prompt
from memory.conversation_history import load_history, save_session, format_history_for_prompt
import psutil
import subprocess
import time

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent

class SysMetricsTracker:
    def __init__(self):
        self.cpu = 0.0
        self.mem = 0.0
        self.net = 0.0
        self.gpu = -1.0
        self.tmp = -1.0
        self._lock = threading.Lock()
        self._last_net = psutil.net_io_counters()
        self._last_net_t = time.time()
        self._running = False
        self._thread = None
        self._os = platform.system()

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            try:
                self._update()
            except Exception:
                pass
            time.sleep(1.5)

    def _update(self):
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory().percent

        nc = psutil.net_io_counters()
        now = time.time()
        dt = now - self._last_net_t
        if dt > 0:
            sent = (nc.bytes_sent - self._last_net.bytes_sent) / dt
            recv = (nc.bytes_recv - self._last_net.bytes_recv) / dt
            net = (sent + recv) / (1024 * 1024)
        else:
            net = 0.0
        self._last_net = nc
        self._last_net_t = now

        gpu = self._get_gpu()
        tmp = self._get_temp()

        with self._lock:
            self.cpu = cpu
            self.mem = mem
            self.net = net
            self.gpu = gpu
            self.tmp = tmp

    def _get_gpu(self) -> float:
        try:
            r = subprocess.run(
                ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=2
            )
            if r.returncode == 0:
                vals = [float(v.strip()) for v in r.stdout.strip().split("\n") if v.strip()]
                if vals:
                    return sum(vals) / len(vals)
        except Exception:
            pass
        return -1.0

    def _get_temp(self) -> float:
        try:
            temps = psutil.sensors_temperatures()
            candidates = ["coretemp", "k10temp", "cpu_thermal", "acpitz", "cpu-thermal", "zenpower", "it8688"]
            for name in candidates:
                if name in temps:
                    entries = temps[name]
                    if entries:
                        return entries[0].current
        except Exception:
            pass
        return -1.0

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "cpu": self.cpu,
                "mem": self.mem,
                "net": self.net,
                "gpu": self.gpu,
                "tmp": self.tmp,
            }

class RexModel:
    def __init__(self):
        self.base_dir = get_base_dir()
        self.config_dir = self.base_dir / "config"
        self.api_file = self.config_dir / "api_keys.json"
        
        self._config_cache = None
        self._config_lock = threading.Lock()
        
        self.metrics_tracker = SysMetricsTracker()
        self.session_log = []
        
    def start_metrics_monitoring(self):
        """Inicia el rastreador de métricas bajo demanda."""
        self.metrics_tracker.start()
        
    def stop_metrics_monitoring(self):
        """Detiene el rastreador de métricas."""
        self.metrics_tracker.stop()
        
    def get_config(self) -> dict:
        """Carga con caché en memoria la configuración."""
        with self._config_lock:
            if self._config_cache is not None:
                return self._config_cache
            
            if not self.api_file.exists():
                return {}
            try:
                self._config_cache = json.loads(self.api_file.read_text(encoding="utf-8"))
                return self._config_cache
            except Exception:
                return {}

    def save_config(self, key: str, os_name: str):
        """Guarda la configuración y actualiza el caché."""
        with self._config_lock:
            os.makedirs(self.config_dir, exist_ok=True)
            config_data = {"gemini_api_key": key, "os_system": os_name}
            self.api_file.write_text(
                json.dumps(config_data, indent=4),
                encoding="utf-8",
            )
            self._config_cache = config_data

    def get_gemini_api_key(self) -> str:
        return self.get_config().get("gemini_api_key", "")

    def get_os_system(self) -> str:
        return self.get_config().get("os_system", "windows").lower()

    def get_system_metrics(self) -> dict:
        return self.metrics_tracker.snapshot()
        
    def load_long_term_memory(self) -> dict:
        return load_memory()
        
    def save_long_term_memory(self, category: str, key: str, value: str):
        update_memory({category: {key: {"value": value}}})
        
    def get_formatted_memory(self) -> str:
        return format_memory_for_prompt(self.load_long_term_memory())
        
    def get_formatted_history(self) -> str:
        return format_history_for_prompt()

    def save_conversation_session(self):
        """Guarda la sesión actual de conversación de forma segura."""
        if self.session_log:
            save_session(self.session_log)
