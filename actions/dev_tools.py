import math

def dev_tools(parameters: dict, player=None, speak=None):
    action = parameters.get("action", "").lower()

    def log(msg):
        if player:
            player.write_log(f"DEV: {msg}")

    def say(msg):
        if speak:
            speak(msg)
        log(msg)

    # ── Complejidad Big-O ────────────────────────────────────────
    if action == "big_o":
        algoritmos = {
            "bubble sort":       ("O(n²)", "O(1)",    "Ineficiente para grandes datos. Solo útil didácticamente."),
            "selection sort":    ("O(n²)", "O(1)",    "Similar a bubble sort, siempre O(n²)."),
            "insertion sort":    ("O(n²)", "O(1)",    "Eficiente para datos casi ordenados."),
            "merge sort":        ("O(n log n)", "O(n)","Estable, divide y conquista. Recomendado para listas grandes."),
            "quick sort":        ("O(n log n)", "O(log n)", "Rápido en promedio, O(n²) en peor caso."),
            "heap sort":         ("O(n log n)", "O(1)", "In-place, no estable."),
            "binary search":     ("O(log n)", "O(1)", "Solo funciona en arreglos ordenados."),
            "linear search":     ("O(n)",     "O(1)", "Búsqueda secuencial simple."),
            "bfs":               ("O(V+E)",   "O(V)", "Recorre grafos por niveles."),
            "dfs":               ("O(V+E)",   "O(V)", "Recorre grafos en profundidad."),
            "dijkstra":          ("O(V²)",    "O(V)", "Camino más corto, sin pesos negativos."),
            "hash table lookup": ("O(1)",     "O(n)", "Acceso promedio constante."),
        }
        nombre = parameters.get("algorithm", "").lower()
        if nombre in algoritmos:
            tiempo, espacio, nota = algoritmos[nombre]
            result = f"{nombre.title()}: Tiempo={tiempo} | Espacio={espacio} | {nota}"
        else:
            lista = ", ".join(algoritmos.keys())
            result = f"Algoritmo no encontrado. Disponibles: {lista}"
        say(result)
        return result

    # ── Patrones de diseño ───────────────────────────────────────
    elif action == "patron_diseno":
        patrones = {
            "singleton": (
                "Creacional",
                "Garantiza una sola instancia de una clase.",
                "class Singleton:\n    _instance = None\n    @classmethod\n    def get_instance(cls):\n        if not cls._instance:\n            cls._instance = cls()\n        return cls._instance"
            ),
            "factory": (
                "Creacional",
                "Crea objetos sin especificar la clase exacta.",
                "class AnimalFactory:\n    @staticmethod\n    def crear(tipo):\n        if tipo == 'perro': return Perro()\n        if tipo == 'gato': return Gato()"
            ),
            "observer": (
                "Comportamiento",
                "Notifica cambios a múltiples objetos suscritos.",
                "class Evento:\n    def __init__(self):\n        self._subs = []\n    def suscribir(self, fn): self._subs.append(fn)\n    def notificar(self, data):\n        for fn in self._subs: fn(data)"
            ),
            "decorator": (
                "Estructural",
                "Agrega comportamiento a objetos dinámicamente.",
                "def log_decorator(func):\n    def wrapper(*args, **kwargs):\n        print('Llamando:', func.__name__)\n        return func(*args, **kwargs)\n    return wrapper"
            ),
            "mvc": (
                "Arquitectural",
                "Separa Modelo, Vista y Controlador.",
                "Modelo: datos y lógica de negocio\nVista: interfaz de usuario\nControlador: intermediario entre modelo y vista"
            ),
            "repository": (
                "Arquitectural",
                "Abstrae el acceso a datos detrás de una interfaz.",
                "class UserRepository:\n    def get(self, id): ...\n    def save(self, user): ...\n    def delete(self, id): ..."
            ),
        }
        nombre = parameters.get("pattern", "").lower()
        if nombre in patrones:
            tipo, desc, ejemplo = patrones[nombre]
            result = f"Patrón {nombre.title()} ({tipo}): {desc}\nEjemplo:\n{ejemplo}"
        else:
            lista = ", ".join(patrones.keys())
            result = f"Patrón no encontrado. Disponibles: {lista}"
        say(result)
        return result

    # ── Estructuras de datos ─────────────────────────────────────
    elif action == "estructura_datos":
        estructuras = {
            "array":        ("O(1) acceso", "O(n) búsqueda", "Tamaño fijo, acceso por índice"),
            "lista enlazada":("O(n) acceso", "O(1) inserción al inicio", "Dinámica, no contigua en memoria"),
            "pila":         ("O(1) push/pop", "LIFO", "Útil para recursión, deshacer acciones"),
            "cola":         ("O(1) enqueue/dequeue", "FIFO", "Útil para procesos, BFS"),
            "hash table":   ("O(1) promedio", "O(n) peor caso", "Clave-valor, búsqueda rápida"),
            "árbol binario":("O(log n) balanceado", "O(n) desbalanceado", "Búsqueda, inserción, eliminación"),
            "grafo":        ("O(V+E)", "Dirigido o no dirigido", "Redes, mapas, dependencias"),
            "heap":         ("O(log n) inserción", "O(1) máximo/mínimo", "Colas de prioridad"),
        }
        nombre = parameters.get("structure", "").lower()
        if nombre in estructuras:
            op1, op2, uso = estructuras[nombre]
            result = f"{nombre.title()}: {op1} | {op2} | Uso: {uso}"
        else:
            lista = ", ".join(estructuras.keys())
            result = f"Estructura no encontrada. Disponibles: {lista}"
        say(result)
        return result

    # ── Conversión de bases numéricas ────────────────────────────
    elif action == "conversion_base":
        valor  = parameters.get("value", "0")
        origen = int(parameters.get("from_base", 10))
        destino= int(parameters.get("to_base", 2))
        try:
            decimal = int(str(valor), origen)
            if destino == 2:
                resultado = bin(decimal)[2:]
                prefijo = "0b"
            elif destino == 8:
                resultado = oct(decimal)[2:]
                prefijo = "0o"
            elif destino == 16:
                resultado = hex(decimal)[2:].upper()
                prefijo = "0x"
            else:
                resultado = str(decimal)
                prefijo = ""
            result = f"{valor} (base {origen}) = {prefijo}{resultado} (base {destino})"
        except ValueError:
            result = f"No se puede convertir '{valor}' de base {origen}."
        say(result)
        return result

    # ── Generador de pseudocódigo a Python ───────────────────────
    elif action == "pseudocodigo":
        descripcion = parameters.get("description", "")
        plantillas = {
            "factorial": (
                "def factorial(n):\n"
                "    if n == 0 or n == 1:\n"
                "        return 1\n"
                "    return n * factorial(n - 1)"
            ),
            "fibonacci": (
                "def fibonacci(n):\n"
                "    a, b = 0, 1\n"
                "    for _ in range(n):\n"
                "        a, b = b, a + b\n"
                "    return a"
            ),
            "busqueda binaria": (
                "def busqueda_binaria(arr, objetivo):\n"
                "    izq, der = 0, len(arr) - 1\n"
                "    while izq <= der:\n"
                "        mid = (izq + der) // 2\n"
                "        if arr[mid] == objetivo: return mid\n"
                "        elif arr[mid] < objetivo: izq = mid + 1\n"
                "        else: der = mid - 1\n"
                "    return -1"
            ),
            "ordenar lista": (
                "def bubble_sort(arr):\n"
                "    n = len(arr)\n"
                "    for i in range(n):\n"
                "        for j in range(0, n-i-1):\n"
                "            if arr[j] > arr[j+1]:\n"
                "                arr[j], arr[j+1] = arr[j+1], arr[j]\n"
                "    return arr"
            ),
        }
        for clave, codigo in plantillas.items():
            if clave in descripcion.lower():
                result = f"Código Python para '{clave}':\n{codigo}"
                say(result)
                return result
        result = f"Usa code_helper para generar código personalizado de: {descripcion}"
        say(result)
        return result

    # ── Conceptos de redes ───────────────────────────────────────
    elif action == "redes":
        conceptos = {
            "osi": "Modelo OSI: 7 capas — Física, Enlace, Red, Transporte, Sesión, Presentación, Aplicación.",
            "tcp/ip": "TCP/IP: 4 capas — Acceso a red, Internet (IP), Transporte (TCP/UDP), Aplicación.",
            "tcp vs udp": "TCP: orientado a conexión, confiable, más lento. UDP: sin conexión, rápido, puede perder paquetes.",
            "http vs https": "HTTP: sin cifrado, puerto 80. HTTPS: cifrado TLS/SSL, puerto 443.",
            "dns": "DNS: traduce nombres de dominio a direcciones IP. Puerto 53.",
            "dhcp": "DHCP: asigna IPs automáticamente a dispositivos en la red.",
            "nat": "NAT: traduce IPs privadas a una IP pública para acceder a internet.",
            "subnet": "Subred: divide una red en segmentos más pequeños usando máscara de subred.",
        }
        tema = parameters.get("topic", "").lower()
        if tema in conceptos:
            result = conceptos[tema]
        else:
            lista = ", ".join(conceptos.keys())
            result = f"Tema no encontrado. Disponibles: {lista}"
        say(result)
        return result

    # ── Conceptos de bases de datos ──────────────────────────────
    elif action == "base_datos":
        conceptos = {
            "normalización": "Proceso de organizar BD para reducir redundancia. Formas normales: 1FN, 2FN, 3FN, BCNF.",
            "acid": "ACID: Atomicidad, Consistencia, Aislamiento, Durabilidad. Propiedades de transacciones.",
            "sql vs nosql": "SQL: estructurado, relacional, ACID. NoSQL: flexible, escalable, eventual consistency.",
            "índice": "Índice: estructura que acelera búsquedas. Costo: más espacio y escrituras más lentas.",
            "join": "JOIN: combina filas de tablas. INNER, LEFT, RIGHT, FULL OUTER JOIN.",
            "transacción": "Transacción: conjunto de operaciones que se ejecutan como unidad atómica.",
        }
        tema = parameters.get("topic", "").lower()
        if tema in conceptos:
            result = conceptos[tema]
        else:
            lista = ", ".join(conceptos.keys())
            result = f"Tema no encontrado. Disponibles: {lista}"
        say(result)
        return result

    else:
        say(f"Acción de dev_tools no reconocida: {action}")
        return f"Acción desconocida: {action}"