# Otorgar permisos de escritura en Windows

Pasos para otorgar permisos al usuario actual sobre las carpetas de su perfil (Desktop, Documents, Downloads, Pictures, Music, Videos).

1. Abrir PowerShell (se recomienda ejecutar como Administrador si necesita cambiar ACLs protegidas).
2. Ejecutar el script incluido `scripts\grant_permissions.ps1` desde la carpeta del proyecto.

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
- Con `-All` intentará aplicar permisos a todos los directorios en `%USERPROFILE%` (se requiere confirmar escribiendo `YES`).

Precauciones:
- Modificar permisos a todo el perfil puede afectar aplicaciones y datos; revisa el script antes de ejecutar.
- El script omite `AppData` por seguridad cuando se usa `-All`.

Alternativa manual (GUI):

1. Navega a `C:\Users\TuUsuario\Desktop`.
2. Click derecho → Propiedades → Seguridad → Editar.
3. Selecciona tu usuario y marca `Modificar` / `Escritura`.
4. Aplicar.

---
Archivo relacionado: `scripts/grant_permissions.ps1`
