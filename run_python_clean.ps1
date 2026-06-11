# Limpia archivos de caché de Python en el proyecto
Write-Host "Eliminando __pycache__ y archivos .pyc..."
Get-ChildItem -Recurse -Include __pycache__ | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Include *.pyc | Remove-Item -Force -ErrorAction SilentlyContinue

# Activa el entorno virtual
Write-Host "Activando entorno virtual..."
& "D:\IA\Asistente\venv\Scripts\Activate.ps1"

# Ejecuta tu programa principal en Python
Write-Host "Ejecutando programa en Python..."
python D:\IA\Asistente\main.py
