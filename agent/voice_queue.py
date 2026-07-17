"""
Cola de voz para gestionar la síntesis de voz sin cortes.
Asegura que los mensajes se reproduzcan secuencialmente.
"""

import threading
import queue
import time
from typing import Callable, Optional


class VoiceQueue:
    """
    Cola thread-safe para mensajes de voz.
    Previene que múltiples llamadas a speak() se interrumpan entre sí.
    """
    
    def __init__(self, speak_callback: Callable, min_interval: float = 0.8):
        """
        Args:
            speak_callback: Función que reproduce el texto (ej: controller.speak)
            min_interval: Segundos mínimos entre mensajes para evitar cortes
        """
        self._speak = speak_callback
        self._min_interval = min_interval
        self._queue = queue.Queue()
        self._worker_thread: Optional[threading.Thread] = None
        self._running = False
        self._last_speak_time = 0
        self._lock = threading.Lock()
        
    def start(self):
        """Inicia el worker thread que procesa la cola."""
        if self._running:
            return
        
        self._running = True
        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            daemon=True,
            name="VoiceQueue-Worker"
        )
        self._worker_thread.start()
        print("[VoiceQueue] ✅ Started")
    
    def stop(self):
        """Detiene el worker thread."""
        self._running = False
        # Enviar mensaje vacío para desbloquear la cola
        self._queue.put(None)
        if self._worker_thread:
            self._worker_thread.join(timeout=2.0)
        print("[VoiceQueue] 🔴 Stopped")
    
    def enqueue(self, message: str, priority: bool = False):
        """
        Agrega un mensaje a la cola de voz.
        
        Args:
            message: Texto a reproducir
            priority: Si es True, se coloca al frente de la cola
        """
        if not message or not message.strip():
            return
        
        if priority:
            # Para mensajes prioritarios, limpiar la cola primero
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    break
        
        self._queue.put(message)
    
    def speak_now(self, message: str):
        """
        Reproduce un mensaje inmediatamente, bloqueando hasta que termine.
        Útil para mensajes críticos que no pueden esperar.
        
        Args:
            message: Texto a reproducir
        """
        if not message or not message.strip():
            return
        
        with self._lock:
            # Respetar intervalo mínimo
            current_time = time.time()
            elapsed = current_time - self._last_speak_time
            
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
            
            try:
                self._speak(message)
                self._last_speak_time = time.time()
            except Exception as e:
                print(f"[VoiceQueue] ❌ Error speaking: {e}")
    
    def clear(self):
        """Limpia todos los mensajes pendientes en la cola."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
    
    def _worker_loop(self):
        """Loop principal del worker que procesa mensajes de la cola."""
        while self._running:
            try:
                # Obtener mensaje con timeout para poder verificar _running
                message = self._queue.get(timeout=0.5)
                
                if message is None:
                    # Señal de parada
                    continue
                
                # Respetar intervalo mínimo entre mensajes
                with self._lock:
                    current_time = time.time()
                    elapsed = current_time - self._last_speak_time
                    
                    if elapsed < self._min_interval:
                        time.sleep(self._min_interval - elapsed)
                    
                    try:
                        self._speak(message)
                        self._last_speak_time = time.time()
                    except Exception as e:
                        print(f"[VoiceQueue] ❌ Error in worker: {e}")
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[VoiceQueue] ❌ Worker error: {e}")


# Instancia global
_voice_queue: Optional[VoiceQueue] = None
_queue_lock = threading.Lock()


def get_voice_queue(speak_callback: Callable = None) -> VoiceQueue:
    """
    Obtiene o crea la instancia global de VoiceQueue.
    
    Args:
        speak_callback: Callback de voz (solo necesario en la primera llamada)
    
    Returns:
        VoiceQueue: Instancia global de la cola de voz
    """
    global _voice_queue
    
    with _queue_lock:
        if _voice_queue is None:
            if speak_callback is None:
                raise ValueError("speak_callback must be provided on first call")
            _voice_queue = VoiceQueue(speak_callback)
            _voice_queue.start()
        
        return _voice_queue


def speak_queued(message: str, priority: bool = False):
    """
    Función conveniente para enviar un mensaje a la cola de voz global.
    
    Args:
        message: Texto a reproducir
        priority: Si es True, se coloca al frente de la cola
    """
    if _voice_queue:
        _voice_queue.enqueue(message, priority=priority)
    else:
        print("[VoiceQueue] ⚠️ Queue not initialized. Call get_voice_queue() first.")


def shutdown_voice_queue():
    """Detiene y limpia la cola de voz global."""
    global _voice_queue
    
    with _queue_lock:
        if _voice_queue:
            _voice_queue.stop()
            _voice_queue = None