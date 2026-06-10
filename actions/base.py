from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable

class BaseAction(ABC):
    """Clase base abstracta para definir el contrato de las herramientas de JARVIS.
    
    Establece las directrices de tipado estricto y asincronía obligatorias
    para garantizar la mantenibilidad y la robustez del framework de ingeniería.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Retorna el identificador único de la acción/herramienta."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Retorna la documentación de uso y firma de parámetros de la acción."""
        pass

    @abstractmethod
    async def execute(
        self,
        parameters: Dict[str, Any],
        player: Optional[Any] = None,
        speak_callback: Optional[Callable[[str], None]] = None
    ) -> str:
        """Ejecuta de forma asíncrona la acción con los parámetros especificados.
        
        Args:
            parameters: Diccionario con los valores de entrada estructurados.
            player: Instancia de la interfaz de usuario para reportar logs visuales.
            speak_callback: Función de retorno opcional para emitir síntesis de voz.
            
        Returns:
            str: Mensaje de resultado de la ejecución de la acción.
        """
        pass
