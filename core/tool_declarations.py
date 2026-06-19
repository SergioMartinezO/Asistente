# Tool declarations for Gemini Live API

TOOL_DECLARATIONS = [
    {
        "name": "open_app",
        "description": (
            "Opens any application on the computer. "
            "Use this whenever the user asks to open, launch, or start any app, "
            "website, or program. Always call this tool ÔÇö never just say you opened it."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "app_name": {
                    "type": "STRING",
                    "description": "Exact name of the application (e.g. 'WhatsApp', 'Chrome', 'Spotify')"
                }
            },
            "required": ["app_name"]
        }
    },
    {
        "name": "web_search",
        "description": "Searches the web for any information.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query":  {"type": "STRING", "description": "Search query"},
                "mode":   {"type": "STRING", "description": "search (default) or compare"},
                "items":  {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Items to compare"},
                "aspect": {"type": "STRING", "description": "price | specs | reviews"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "weather_report",
        "description": "Gives the weather report to user",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "city": {"type": "STRING", "description": "City name"}
            },
            "required": ["city"]
        }
    },
    {
        "name": "send_message",
        "description": "Sends a text message via WhatsApp, Telegram, or other messaging platform.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "receiver":     {"type": "STRING", "description": "Recipient contact name"},
                "message_text": {"type": "STRING", "description": "The message to send"},
                "platform":     {"type": "STRING", "description": "Platform: WhatsApp, Telegram, etc."}
            },
            "required": ["receiver", "message_text", "platform"]
        }
    },
    {
        "name": "reminder",
        "description": "Sets a timed reminder using Task Scheduler.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "date":    {"type": "STRING", "description": "Date in YYYY-MM-DD format"},
                "time":    {"type": "STRING", "description": "Time in HH:MM format (24h)"},
                "message": {"type": "STRING", "description": "Reminder message text"}
            },
            "required": ["date", "time", "message"]
        }
    },
    {
        "name": "youtube_video",
        "description": (
            "Controls YouTube. Use for: playing videos, summarizing a video's content, "
            "getting video info, or showing trending videos."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "play | summarize | get_info | trending (default: play)"},
                "query":  {"type": "STRING", "description": "Search query for play action"},
                "save":   {"type": "BOOLEAN", "description": "Save summary to Notepad (summarize only)"},
                "region": {"type": "STRING", "description": "Country code for trending e.g. TR, US"},
                "url":    {"type": "STRING", "description": "Video URL for get_info action"},
            },
            "required": []
        }
    },
    {
        "name": "screen_process",
        "description": (
            "Captures and analyzes the screen or webcam image. "
            "MUST be called when user asks what is on screen, what you see, "
            "analyze my screen, look at camera, etc. "
            "You have NO visual ability without this tool. "
            "After calling this tool, stay SILENT ÔÇö the vision module speaks directly."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "angle": {"type": "STRING", "description": "'screen' to capture display, 'camera' for webcam. Default: 'screen'"},
                "text":  {"type": "STRING", "description": "The question or instruction about the captured image"}
            },
            "required": ["text"]
        }
    },
    {
        "name": "computer_settings",
        "description": (
            "Controls the computer: volume, brightness, window management, keyboard shortcuts, "
            "typing text on screen, closing apps, fullscreen, dark mode, WiFi, restart, shutdown, "
            "scrolling, tab management, zoom, screenshots, lock screen, refresh/reload page. "
            "Use for ANY single computer control command. NEVER route to agent_task."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":      {"type": "STRING", "description": "The action to perform"},
                "description": {"type": "STRING", "description": "Natural language description of what to do"},
                "value":       {"type": "STRING", "description": "Optional value: volume level, text to type, etc."}
            },
            "required": []
        }
    },
    {
        "name": "browser_control",
        "description": (
            "Controls any web browser. Use for: opening websites, searching the web, "
            "clicking elements, filling forms, scrolling, screenshots, navigation, any web-based task. "
            "Always pass the 'browser' parameter when the user specifies a browser (e.g. 'open in Edge', "
            "'use Firefox', 'open Chrome'). Multiple browsers can run simultaneously."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":      {"type": "STRING", "description": "go_to | search | click | type | scroll | fill_form | smart_click | smart_type | get_text | get_url | press | new_tab | close_tab | screenshot | back | forward | reload | switch | list_browsers | close | close_all"},
                "browser":     {"type": "STRING", "description": "Target browser: chrome | edge | firefox | opera | operagx | brave | vivaldi | safari. Omit to use the currently active browser."},
                "url":         {"type": "STRING", "description": "URL for go_to / new_tab action"},
                "query":       {"type": "STRING", "description": "Search query for search action"},
                "engine":      {"type": "STRING", "description": "Search engine: google | bing | duckduckgo | yandex (default: google)"},
                "selector":    {"type": "STRING", "description": "CSS selector for click/type"},
                "text":        {"type": "STRING", "description": "Text to click or type"},
                "description": {"type": "STRING", "description": "Element description for smart_click/smart_type"},
                "direction":   {"type": "STRING", "description": "up | down for scroll"},
                "amount":      {"type": "INTEGER", "description": "Scroll amount in pixels (default: 500)"},
                "key":         {"type": "STRING", "description": "Key name for press action (e.g. Enter, Escape, F5)"},
                "path":        {"type": "STRING", "description": "Save path for screenshot"},
                "incognito":   {"type": "BOOLEAN", "description": "Open in private/incognito mode"},
                "clear_first": {"type": "BOOLEAN", "description": "Clear field before typing (default: true)"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "file_controller",
        "description": "Manages files and folders: list, create, delete, move, copy, rename, read, write, find, disk usage.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":      {"type": "STRING", "description": "list | open | create_file | create_folder | delete | move | copy | rename | read | write | find | largest | disk_usage | organize_desktop | info"},
                "path":        {"type": "STRING", "description": "File/folder path or shortcut: desktop, downloads, documents, home"},
                "destination": {"type": "STRING", "description": "Destination path for move/copy"},
                "overwrite":   {"type": "BOOLEAN", "description": "Overwrite destination if it already exists for move/copy"},
                "recursive":   {"type": "BOOLEAN", "description": "Recursively list nested folders and files for list action"},
                "show_hidden": {"type": "BOOLEAN", "description": "Include hidden files/folders in list action"},
                "new_name":    {"type": "STRING", "description": "New name for rename"},
                "content":     {"type": "STRING", "description": "Content for create_file/write"},
                "name":        {"type": "STRING", "description": "File name to search for, or name of file/folder to open"},
                "extension":   {"type": "STRING", "description": "File extension to search (e.g. .pdf)"},
                "count":       {"type": "INTEGER", "description": "Number of results for largest"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "desktop_control",
        "description": "Controls the desktop: wallpaper, organize, clean, list, stats.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "wallpaper | wallpaper_url | organize | clean | list | stats | task"},
                "path":   {"type": "STRING", "description": "Image path for wallpaper"},
                "url":    {"type": "STRING", "description": "Image URL for wallpaper_url"},
                "mode":   {"type": "STRING", "description": "by_type or by_date for organize"},
                "task":   {"type": "STRING", "description": "Natural language desktop task"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "code_helper",
        "description": "Writes, edits, explains, runs, or builds code files.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":      {"type": "STRING", "description": "write | edit | explain | run | build | auto (default: auto)"},
                "description": {"type": "STRING", "description": "What the code should do or what change to make"},
                "language":    {"type": "STRING", "description": "Programming language (default: python)"},
                "output_path": {"type": "STRING", "description": "Where to save the file"},
                "file_path":   {"type": "STRING", "description": "Path to existing file for edit/explain/run/build"},
                "code":        {"type": "STRING", "description": "Raw code string for explain"},
                "args":        {"type": "STRING", "description": "CLI arguments for run/build"},
                "timeout":     {"type": "INTEGER", "description": "Execution timeout in seconds (default: 30)"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "dev_agent",
        "description": "Builds complete multi-file projects from scratch: plans, writes files, installs deps, opens VSCode, runs and fixes errors.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "description":  {"type": "STRING", "description": "What the project should do"},
                "language":     {"type": "STRING", "description": "Programming language (default: python)"},
                "project_name": {"type": "STRING", "description": "Optional project folder name"},
                "timeout":      {"type": "INTEGER", "description": "Run timeout in seconds (default: 30)"},
            },
            "required": ["description"]
        }
    },
    {
        "name": "agent_task",
        "description": (
            "Executes complex multi-step tasks requiring multiple different tools. "
            "Examples: 'research X and save to file', 'find and organize files'. "
            "DO NOT use for single commands. NEVER use for Steam/Epic ÔÇö use game_updater."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "goal":     {"type": "STRING", "description": "Complete description of what to accomplish"},
                "priority": {"type": "STRING", "description": "low | normal | high (default: normal)"}
            },
            "required": ["goal"]
        }
    },
    {
        "name": "computer_control",
        "description": "Direct computer control: type, click, hotkeys, scroll, move mouse, screenshots, find elements on screen.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":      {"type": "STRING", "description": "type | smart_type | click | double_click | right_click | hotkey | press | scroll | move | copy | paste | screenshot | wait | clear_field | focus_window | screen_find | screen_click | random_data | user_data"},
                "text":        {"type": "STRING", "description": "Text to type or paste"},
                "x":           {"type": "INTEGER", "description": "X coordinate"},
                "y":           {"type": "INTEGER", "description": "Y coordinate"},
                "keys":        {"type": "STRING", "description": "Key combination e.g. 'ctrl+c'"},
                "key":         {"type": "STRING", "description": "Single key e.g. 'enter'"},
                "direction":   {"type": "STRING", "description": "up | down | left | right"},
                "amount":      {"type": "INTEGER", "description": "Scroll amount (default: 3)"},
                "seconds":     {"type": "NUMBER",  "description": "Seconds to wait"},
                "title":       {"type": "STRING",  "description": "Window title for focus_window"},
                "description": {"type": "STRING",  "description": "Element description for screen_find/screen_click"},
                "type":        {"type": "STRING",  "description": "Data type for random_data"},
                "field":       {"type": "STRING",  "description": "Field for user_data: name|email|city"},
                "clear_first": {"type": "BOOLEAN", "description": "Clear field before typing (default: true)"},
                "path":        {"type": "STRING",  "description": "Save path for screenshot"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "game_updater",
        "description": (
            "THE ONLY tool for ANY Steam or Epic Games request. "
            "Use for: installing, downloading, updating games, listing installed games, "
            "checking download status, scheduling updates. "
            "ALWAYS call directly for any Steam/Epic/game request. "
            "NEVER use agent_task, browser_control, or web_search for Steam/Epic."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":    {"type": "STRING",  "description": "update | install | list | download_status | schedule | cancel_schedule | schedule_status (default: update)"},
                "platform":  {"type": "STRING",  "description": "steam | epic | both (default: both)"},
                "game_name": {"type": "STRING",  "description": "Game name (partial match supported)"},
                "app_id":    {"type": "STRING",  "description": "Steam AppID for install (optional)"},
                "hour":      {"type": "INTEGER", "description": "Hour for scheduled update 0-23 (default: 3)"},
                "minute":    {"type": "INTEGER", "description": "Minute for scheduled update 0-59 (default: 0)"},
                "shutdown_when_done": {"type": "BOOLEAN", "description": "Shut down PC when download finishes"},
            },
            "required": []
        }
    },
    {
        "name": "flight_finder",
        "description": "Searches Google Flights and speaks the best options.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "origin":      {"type": "STRING",  "description": "Departure city or airport code"},
                "destination": {"type": "STRING",  "description": "Arrival city or airport code"},
                "date":        {"type": "STRING",  "description": "Departure date (any format)"},
                "return_date": {"type": "STRING",  "description": "Return date for round trips"},
                "passengers":  {"type": "INTEGER", "description": "Number of passengers (default: 1)"},
                "cabin":       {"type": "STRING",  "description": "economy | premium | business | first"},
                "save":        {"type": "BOOLEAN", "description": "Save results to Notepad"},
            },
            "required": ["origin", "destination", "date"]
        }
    },
    {
        "name": "shutdown_rex",
        "description": (
            "Shuts down the assistant completely. "
            "Call this when the user expresses intent to end the conversation, "
            "close the assistant, say goodbye, or stop Rex. "
            "The user can say this in ANY language."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {},
        }
    },
    {
    "name": "file_processor",
    "description": (
        "Processes any file that the user has uploaded or dropped onto the interface. "
        "Use this when the user refers to an uploaded file and wants an action on it. "
        "Supports: images (describe/ocr/resize/compress/convert), "
        "PDFs (summarize/extract_text/to_word), "
        "Word docs & text files (summarize/fix/reformat/translate), "
        "CSV/Excel (analyze/stats/filter/sort/convert), "
        "JSON/XML (validate/format/analyze), "
        "code files (explain/review/fix/optimize/run/document/test), "
        "audio (transcribe/trim/convert/info), "
        "video (trim/extract_audio/extract_frame/compress/transcribe/info), "
        "archives (list/extract), "
        "presentations (summarize/extract_text). "
        "ALWAYS call this tool when a file has been uploaded and the user gives a command about it. "
        "If the user's command is ambiguous, pick the most logical action for that file type."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "file_path": {
                "type": "STRING",
                "description": "Full path to the uploaded file. Leave empty to use the currently uploaded file."
            },
            "action": {
                "type": "STRING",
                "description": (
                    "What to do with the file. Examples by type:\n"
                    "image: describe | ocr | resize | compress | convert | info\n"
                    "pdf: summarize | extract_text | to_word | info\n"
                    "docx/txt: summarize | fix | reformat | translate_hint | word_count | to_bullet\n"
                    "csv/excel: analyze | stats | filter | sort | convert | info\n"
                    "json: validate | format | analyze | to_csv\n"
                    "code: explain | review | fix | optimize | run | document | test\n"
                    "audio: transcribe | trim | convert | info\n"
                    "video: trim | extract_audio | extract_frame | compress | transcribe | info | convert\n"
                    "archive: list | extract\n"
                    "pptx: summarize | extract_text | analyze"
                )
            },
            "instruction": {
                "type": "STRING",
                "description": "Free-form instruction if action doesn't cover it. E.g. 'translate this to Turkish', 'find all email addresses'"
            },
            "format": {
                "type": "STRING",
                "description": "Target format for conversion. E.g. 'mp3', 'pdf', 'csv', 'png'"
            },
            "width":     {"type": "INTEGER", "description": "Target width for image resize"},
            "height":    {"type": "INTEGER", "description": "Target height for image resize"},
            "scale":     {"type": "NUMBER",  "description": "Scale factor for image resize (e.g. 0.5)"},
            "quality":   {"type": "INTEGER", "description": "Quality 1-100 for image/video compress"},
            "start":     {"type": "STRING",  "description": "Start time for trim: seconds or HH:MM:SS"},
            "end":       {"type": "STRING",  "description": "End time for trim: seconds or HH:MM:SS"},
            "timestamp": {"type": "STRING",  "description": "Timestamp for video frame extraction HH:MM:SS"},
            "column":    {"type": "STRING",  "description": "Column name for CSV filter/sort"},
            "value":     {"type": "STRING",  "description": "Filter value for CSV filter"},
            "condition": {"type": "STRING",  "description": "Filter condition: equals|contains|gt|lt"},
            "ascending": {"type": "BOOLEAN", "description": "Sort order for CSV sort (default: true)"},
            "save":      {"type": "BOOLEAN", "description": "Save result to file (default: true)"},
            "destination": {"type": "STRING", "description": "Output folder for archive extract"},
        },
        "required": []
    }
},
    {
        "name": "save_memory",
        "description": (
            "Save an important personal fact about the user to long-term memory. "
            "Call this silently whenever the user reveals something worth remembering: "
            "name, age, city, job, preferences, hobbies, relationships, projects, or future plans. "
            "Do NOT call for: weather, reminders, searches, or one-time commands. "
            "Do NOT announce that you are saving ÔÇö just call it silently. "
            "Values must be in English regardless of the conversation language."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "category": {
                    "type": "STRING",
                    "description": (
                        "identity ÔÇö name, age, birthday, city, job, language, nationality | "
                        "preferences ÔÇö favorite food/color/music/film/game/sport, hobbies | "
                        "projects ÔÇö active projects, goals, things being built | "
                        "relationships ÔÇö friends, family, partner, colleagues | "
                        "wishes ÔÇö future plans, things to buy, travel dreams | "
                        "notes ÔÇö habits, schedule, anything else worth remembering"
                    )
                },
                "key":   {"type": "STRING", "description": "Short snake_case key (e.g. name, favorite_food, sister_name)"},
                "value": {"type": "STRING", "description": "Concise value in English (e.g. Fatih, pizza, older sister)"},
            },
            "required": ["category", "key", "value"]
        }
    },
    {
    "name": "electronics",
    "description": (
        "Resuelve c├ílculos de ingenier├¡a electr├│nica. "
        "Usa para: Ley de Ohm, resistencias en serie/paralelo, divisor de tensi├│n, "
        "reactancia capacitiva/inductiva, frecuencia de corte RC/RL, "
        "conversi├│n dBm/mW, Vrms/Vpp, c├│digo de colores de resistencias, prefijos SI. "
        "Ejemplos: 'calcula la reactancia de un condensador de 10uF a 60Hz', "
        "'resistencia rojo rojo naranja dorado', 'convierte 100mW a dBm'."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "ohm | serie | paralelo | divisor_tension | reactancia_c | reactancia_l | frecuencia_corte | dbm_mw | vrms_vpp | codigo_colores | prefijo_si"},
            "voltage":     {"type": "NUMBER", "description": "Voltaje en voltios"},
            "current":     {"type": "NUMBER", "description": "Corriente en amperios"},
            "resistance":  {"type": "NUMBER", "description": "Resistencia en ohmios"},
            "power":       {"type": "NUMBER", "description": "Potencia en vatios"},
            "values":      {"type": "ARRAY",  "items": {"type": "NUMBER"}, "description": "Lista de resistencias"},
            "vin":         {"type": "NUMBER", "description": "Voltaje de entrada"},
            "r1":          {"type": "NUMBER", "description": "Resistencia 1"},
            "r2":          {"type": "NUMBER", "description": "Resistencia 2"},
            "frequency":   {"type": "NUMBER", "description": "Frecuencia en Hz"},
            "capacitance": {"type": "NUMBER", "description": "Capacitancia en Faradios"},
            "inductance":  {"type": "NUMBER", "description": "Inductancia en Henrios"},
            "dbm":         {"type": "NUMBER", "description": "Potencia en dBm"},
            "mw":          {"type": "NUMBER", "description": "Potencia en milivatios"},
            "vrms":        {"type": "NUMBER", "description": "Voltaje RMS"},
            "vpp":         {"type": "NUMBER", "description": "Voltaje pico a pico"},
            "bands":       {"type": "ARRAY",  "items": {"type": "STRING"}, "description": "Colores de bandas"},
            "value":       {"type": "NUMBER", "description": "Valor num├®rico para conversi├│n SI"},
            "from_prefix": {"type": "STRING", "description": "Prefijo origen: nano, micro, mili, kilo, mega"},
            "to_prefix":   {"type": "STRING", "description": "Prefijo destino: nano, micro, mili, kilo, mega, base"}
        },
        "required": ["action"]
    }
},
{
    "name": "datasheet_finder",
    "description": (
        "Busca datasheets y especificaciones t├®cnicas de componentes electr├│nicos. "
        "Usa para: buscar datasheet de cualquier componente, CI, transistor, sensor, "
        "microcontrolador, etc. Abre el navegador con los resultados. "
        "Ejemplos: 'busca el datasheet del NE555', "
        "'datasheet del LM741', 'especificaciones del BC547'."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "component": {"type": "STRING", "description": "Nombre o n├║mero de parte del componente (ej: NE555, LM741, BC547, ATmega328)"},
            "action":    {"type": "STRING", "description": "search (default) | pdf | alldatasheet | digikey | mouser | octopart"},
        },
        "required": ["component"]
    }
},
{
    "name": "dev_tools",
    "description": (
        "Herramientas de ingenier├¡a de software y sistemas. "
        "Usa para: complejidad Big-O de algoritmos, patrones de dise├▒o, "
        "estructuras de datos, conversi├│n de bases num├®ricas, conceptos de redes, "
        "bases de datos. Ejemplos: 'complejidad de merge sort', 'patr├│n singleton', "
        "'convierte 255 de decimal a binario', 'qu├® es TCP vs UDP'."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "big_o | patron_diseno | estructura_datos | conversion_base | pseudocodigo | redes | base_datos"},
            "algorithm": {"type": "STRING", "description": "Nombre del algoritmo para big_o"},
            "pattern": {"type": "STRING", "description": "Nombre del patr├│n para patron_diseno"},
            "structure": {"type": "STRING", "description": "Nombre de estructura para estructura_datos"},
            "value": {"type": "STRING", "description": "Valor para conversi├│n de base"},
            "from_base": {"type": "INTEGER", "description": "Base origen (2, 8, 10, 16)"},
            "to_base": {"type": "INTEGER", "description": "Base destino (2, 8, 10, 16)"},
            "topic": {"type": "STRING", "description": "Tema para redes o base_datos"},
            "description": {"type": "STRING", "description": "Descripci├│n para pseudocodigo"},
        },
        "required": ["action"]
    }
},
{
    "name": "mechatronics",
    "description": (
        "Resuelve c├ílculos de mecatr├│nica e ingenier├¡a mec├ínica, incluyendo cinem├ítica inversa y sintonizaci├│n PID. "
        "Usa para: torque, potencia mec├ínica, conversi├│n RPM/rad┬ÀsÔü╗┬╣, "
        "relaciones de transmisi├│n, cinem├ítica lineal, cinem├ítica inversa de brazo de 2-DOF, sintonizaci├│n de lazo cerrado PID, "
        "info de motores DC/servo/stepper/BLDC, sensores (HC-SR04, DHT22, MPU-6050, encoders), Arduino (PWM, I2C, SPI). "
        "Ejemplos: 'calcula la cinem├ítica inversa para brazo en (10, 5)', 'sintoniza un PID con kp=2, ki=0.5, kd=0.1', "
        "'potencia de motor a 1500 RPM', 'info del sensor ultrasonico'."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "torque | potencia | rpm_rad | transmision | cinematica | motor_info | sensor_info | arduino | pid_tuning | cinematica_inversa"},
            "force": {"type": "NUMBER", "description": "Fuerza en Newton"},
            "distance": {"type": "NUMBER", "description": "Distancia en metros"},
            "torque": {"type": "NUMBER", "description": "Torque en N┬Àm"},
            "rpm": {"type": "NUMBER", "description": "Velocidad angular en RPM"},
            "rad_s": {"type": "NUMBER", "description": "Velocidad angular en rad/s"},
            "velocity": {"type": "NUMBER", "description": "Velocidad lineal en m/s"},
            "teeth_input": {"type": "INTEGER", "description": "Dientes engranaje entrada"},
            "teeth_output": {"type": "INTEGER", "description": "Dientes engranaje salida"},
            "rpm_input": {"type": "NUMBER", "description": "RPM de entrada para transmision"},
            "v0": {"type": "NUMBER", "description": "Velocidad inicial m/s"},
            "vf": {"type": "NUMBER", "description": "Velocidad final m/s"},
            "acceleration": {"type": "NUMBER", "description": "Aceleraci├│n m/s┬▓"},
            "time": {"type": "NUMBER", "description": "Tiempo en segundos"},
            "motor_type": {"type": "STRING", "description": "dc | paso a paso | servo | bldc"},
            "sensor_type": {"type": "STRING", "description": "ultrasonico | temperatura | infrarrojo | acelerometro | encoder"},
            "topic": {"type": "STRING", "description": "Tema Arduino: pwm | i2c | spi | interrupcion | watchdog"},
            "kp": {"type": "NUMBER", "description": "Ganancia proporcional Kp para PID"},
            "ki": {"type": "NUMBER", "description": "Ganancia integral Ki para PID"},
            "kd": {"type": "NUMBER", "description": "Ganancia derivativa Kd para PID"},
            "setpoint": {"type": "NUMBER", "description": "Valor deseado de referencia (default: 1.0)"},
            "duration": {"type": "NUMBER", "description": "Duraci├│n de la simulaci├│n en segundos (default: 5.0)"},
            "dt": {"type": "NUMBER", "description": "Intervalo de muestreo temporal dt en segundos (default: 0.02)"},
            "x": {"type": "NUMBER", "description": "Coordenada X objetivo para cinem├ítica inversa"},
            "y": {"type": "NUMBER", "description": "Coordenada Y objetivo para cinem├ítica inversa"},
            "l1": {"type": "NUMBER", "description": "Longitud del eslab├│n 1 del brazo rob├│tico"},
            "l2": {"type": "NUMBER", "description": "Longitud del eslab├│n 2 del brazo rob├│tico"},
        },
        "required": ["action"]
    }
},
{
    "name": "materials_science",
    "description": (
        "Resuelve problemas y c├ílculos de ciencia de materiales. "
        "Usa para: esfuerzo mec├ínico, deformaci├│n unitaria, Ley de Hooke, "
        "esfuerzo t├®rmico por cambios de temperatura y consulta de base de datos "
        "de propiedades de materiales industriales comunes (aluminio, acero, cobre, silicio, titanio). "
        "Ejemplos: 'calcula el esfuerzo si se aplica 5000N sobre 10mm2', "
        "'esfuerzo t├®rmico de barra de acero de 20 a 100 grados', "
        "'propiedades del titanio grado 5'."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "esfuerzo_deformacion | esfuerzo_termico | seleccion_materiales"},
            "load": {"type": "NUMBER", "description": "Fuerza de carga en Newtons (N)"},
            "area": {"type": "NUMBER", "description": "├ürea de secci├│n transversal"},
            "area_unit": {"type": "STRING", "description": "mm2 (default) | m2"},
            "length": {"type": "NUMBER", "description": "Longitud inicial L0"},
            "delta_length": {"type": "NUMBER", "description": "Cambio de longitud (deformaci├│n)"},
            "length_unit": {"type": "STRING", "description": "mm (default) | m"},
            "young_modulus": {"type": "NUMBER", "description": "M├│dulo de Young (E) en GPa"},
            "alpha": {"type": "NUMBER", "description": "Coeficiente de expansi├│n lineal lineal x 10^-6 / ┬░C"},
            "delta_temp": {"type": "NUMBER", "description": "Gradiente de temperatura en ┬░C"},
            "material_name": {"type": "STRING", "description": "Nombre del material (ej: aluminio 6061-t6, acero aisi 1020, cobre, silicio, titanio grado 5)"}
        },
        "required": ["action"]
    }
},
{
    "name": "proteus_automation",
    "description": (
        "Automatiza la simulaci├│n de circuitos en Proteus VSM. "
        "Abre el archivo de dise├▒o de circuito, inicia la simulaci├│n activa durante "
        "un tiempo determinado y cierra el programa de manera limpia."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "simulate (default)"},
            "dsn_path": {"type": "STRING", "description": "Ruta completa del archivo .DSN del circuito. Omitir para valor predeterminado."},
            "exe_path": {"type": "STRING", "description": "Ruta del ejecutable de Proteus BIN\\PDS.EXE. Omitir para valor predeterminado."},
            "duration": {"type": "NUMBER", "description": "Duraci├│n de la simulaci├│n activa en segundos (default: 12.0)"}
        },
        "required": []
    }
},
{
    "name": "ltspice_automation",
    "description": (
        "Ejecuta simulaciones en lote de LTspice y extrae resultados del archivo .log. "
        "Usa esto para validar circuitos en lote sin abrir la interfaz gr├ífica."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "simulate (default)"},
            "asc_path": {"type": "STRING", "description": "Ruta del archivo .asc de LTspice. Omitir para buscar en el Escritorio."},
            "exe_path": {"type": "STRING", "description": "Ruta del ejecutable de LTspice (por ejemplo, LTspice.exe o XVIIist.exe). Omitir para autodetectar."}
        },
        "required": []
    }
},
]
