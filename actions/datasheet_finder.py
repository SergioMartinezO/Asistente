import webbrowser
import urllib.parse

def datasheet_finder(parameters: dict, player=None, speak=None):
    component = parameters.get("component", "").strip()
    action    = parameters.get("action", "search").lower()

    def log(msg):
        if player:
            player.write_log(f"DS: {msg}")

    def say(msg):
        if speak:
            speak(msg)
        log(msg)

    if not component:
        say("Necesito el nombre o número de parte del componente.")
        return "Falta el componente."

    encoded = urllib.parse.quote(component)

    fuentes = {
        "alldatasheet": f"https://www.alldatasheet.com/search.jsp?Searchword={encoded}",
        "datasheetspdf": f"https://www.datasheetspdf.com/search/{encoded}.html",
        "digikey":      f"https://www.digikey.com/en/products/filter?keywords={encoded}",
        "mouser":       f"https://www.mouser.com/Search/Refine?Keyword={encoded}",
        "octopart":     f"https://octopart.com/search?q={encoded}",
    }

    # ── Búsqueda directa PDF ─────────────────────────────────────
    if action == "pdf":
        url = f"https://www.alldatasheet.com/search.jsp?Searchword={encoded}"
        webbrowser.open(url)
        result = f"Buscando datasheet PDF de {component} en AllDatasheet."
        say(result)
        return result

    # ── Búsqueda en fuente específica ────────────────────────────
    elif action in fuentes:
        webbrowser.open(fuentes[action])
        result = f"Buscando {component} en {action}."
        say(result)
        return result

    # ── Búsqueda general — abre las 2 mejores fuentes ────────────
    else:
        # Open a single browser destination to avoid spawning duplicate tabs/windows.
        webbrowser.open(fuentes["alldatasheet"])
        result = (
            f"Buscando datasheet de {component} en AllDatasheet. "
            f"También puedes buscar en Octopart, Digi-Key y Mouser para disponibilidad y precio."
        )
        say(result)
        return result