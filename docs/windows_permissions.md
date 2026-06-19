# Windows write permissions / Permisos de escritura en Windows

## Español

Pasos para otorgar permisos al usuario actual sobre las carpetas de su perfil (`Desktop`, `Documents`, `Downloads`, `Pictures`, `Music`, `Videos`).

1. Abre PowerShell (se recomienda ejecutar como Administrador si necesitas cambiar ACLs protegidas).
2. Ejecuta el script incluido `scripts\grant_permissions.ps1` desde la carpeta del proyecto.

Uso básico (aplica a carpetas comunes):

```powershell
# Desde el directorio del proyecto
.\scripts\grant_permissions.ps1
```

Aplicar a todas las carpetas del perfil (pide confirmación y omite `AppData` por seguridad):

```powershell
.\scripts\grant_permissions.ps1 -All
```

Qué hace el script:

- Por defecto asigna permisos `Modify` al usuario actual en las carpetas visibles más comunes.
- Con `-All`, intentará aplicar permisos a todos los directorios en `%USERPROFILE%` (requiere confirmar escribiendo `YES`).
- Resuelve la identidad del usuario usando cuenta de Windows (`DOMINIO\\Usuario`) para evitar errores de traducción de SID en ACL.
- Omite enlaces simbólicos/junctions (`ReparsePoint`) para reducir errores y evitar cambios recursivos no deseados.

Precauciones:

- Modificar permisos en todo el perfil puede afectar aplicaciones y datos; revisa el script antes de ejecutarlo.
- El script omite `AppData` por seguridad cuando se usa `-All`.
- Si una carpeta falla, el script continúa con las demás y muestra el mensaje de error puntual.

Solución de problemas rápida:

- Si aparece `Cannot convert 'System.Object[]'... Join-Path`, usa la versión actual del script (ya corregida).
- Si aparece `identity references could not be translated`, abre PowerShell con el mismo usuario de sesión y vuelve a ejecutar el script actualizado.
- Para minimizar riesgos, ejecuta primero sin `-All` y luego amplía solo si es necesario.

Alternativa manual (GUI):

1. Navega a `C:\Users\TuUsuario\Desktop`.
2. Click derecho → Propiedades → Seguridad → Editar.
3. Selecciona tu usuario y marca `Modificar` / `Escritura`.
4. Aplicar.

## English

Steps to grant write permissions to the current user on common profile folders (`Desktop`, `Documents`, `Downloads`, `Pictures`, `Music`, `Videos`).

1. Open PowerShell (running as Administrator is recommended if protected ACLs must be changed).
2. Run the included script `scripts\grant_permissions.ps1` from the project directory.

Basic usage (common folders):

```powershell
# From the project directory
.\scripts\grant_permissions.ps1
```

Apply to all profile folders (asks for confirmation and skips `AppData` for safety):

```powershell
.\scripts\grant_permissions.ps1 -All
```

What the script does:

- By default, it grants `Modify` permission to the current user on the most common visible folders.
- With `-All`, it attempts to apply permissions to all directories under `%USERPROFILE%` (requires typing `YES` to confirm).
- It resolves the current user as a Windows account (`DOMAIN\\User`) to prevent SID translation ACL errors.
- It skips symbolic links/junctions (`ReparsePoint`) to avoid unintended recursive ACL changes.

Precautions:

- Changing permissions across the full profile may impact apps and data; review the script before running it.
- The script skips `AppData` for safety when using `-All`.
- If a folder fails, the script continues with the next one and prints the specific error.

Quick troubleshooting:

- If you see `Cannot convert 'System.Object[]'... Join-Path`, use the updated script version (already fixed).
- If you see `identity references could not be translated`, run PowerShell under the same signed-in user and re-run the updated script.
- To reduce risk, run without `-All` first, then expand scope only if needed.

Manual alternative (GUI):

1. Go to `C:\Users\YourUser\Desktop`.
2. Right click → Properties → Security → Edit.
3. Select your user and enable `Modify` / `Write`.
4. Apply.

---

Related file / Archivo relacionado: `scripts/grant_permissions.ps1`
