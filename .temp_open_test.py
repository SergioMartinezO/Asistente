from actions import file_controller as fc
from pathlib import Path
path = r'C:\Users\seyo2\Desktop\Informacion medica'
print('path', path)
print('resolved', fc._resolve_path(path))
print('exists', fc._resolve_path(path).exists())
print('safe', fc._is_safe_path(fc._resolve_path(path)))
print('open result', fc._open_target(fc._resolve_path(path)))
