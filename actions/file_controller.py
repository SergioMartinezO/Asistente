import os
import shutil
import subprocess
import platform
import stat
import tempfile
from pathlib import Path
from datetime import datetime

try:
    import send2trash
    _SEND2TRASH = True
except ImportError:
    _SEND2TRASH = False

_OS = platform.system()  # "Windows" | "Darwin" | "Linux"

_SAFE_ROOTS: list[Path] = [
    Path.home(),
]


def _get_windows_shell_folder(name: str) -> Path | None:
    try:
        import winreg
        for hive_path in [
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders",
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
        ]:
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, hive_path) as key:
                    value = winreg.QueryValueEx(key, name)[0]
                    if value:
                        return Path(os.path.expandvars(value))
            except OSError:
                continue
    except Exception:
        pass
    return None


def _get_user_folder(name: str, fallback: str) -> Path:
    if _OS == "Windows":
        path = _get_windows_shell_folder(name)
        if path and path.exists():
            return path
    return Path.home() / fallback


def _is_safe_path(target: Path) -> bool:
    """Return True if target is inside a trusted user folder."""
    try:
        resolved = target.resolve()
        return any(
            resolved == root.resolve() or resolved.is_relative_to(root.resolve())
            for root in _SAFE_ROOTS
        )
    except Exception:
        try:
            resolved_parent = target.parent.resolve()
            return any(
                resolved_parent == root.resolve() or resolved_parent.is_relative_to(root.resolve())
                for root in _SAFE_ROOTS
            )
        except Exception:
            return False


def _get_desktop() -> Path:
    if _OS == "Linux":
        xdg = os.environ.get("XDG_DESKTOP_DIR", "")
        if xdg and Path(xdg).exists():
            return Path(xdg)
    return _get_user_folder("Desktop", "Desktop")


def _get_downloads() -> Path:
    if _OS == "Linux":
        xdg = os.environ.get("XDG_DOWNLOAD_DIR", "")
        if xdg and Path(xdg).exists():
            return Path(xdg)
    return _get_user_folder("{374DE290-123F-4565-9164-39C4925E467B}", "Downloads")


def _get_documents() -> Path:
    if _OS == "Linux":
        xdg = os.environ.get("XDG_DOCUMENTS_DIR", "")
        if xdg and Path(xdg).exists():
            return Path(xdg)
    return _get_user_folder("Personal", "Documents")


def _get_pictures() -> Path:
    if _OS == "Linux":
        xdg = os.environ.get("XDG_PICTURES_DIR", "")
        if xdg and Path(xdg).exists():
            return Path(xdg)
    return _get_user_folder("Pictures", "Pictures")


def _get_music() -> Path:
    if _OS == "Linux":
        xdg = os.environ.get("XDG_MUSIC_DIR", "")
        if xdg and Path(xdg).exists():
            return Path(xdg)
    return _get_user_folder("Music", "Music")


def _get_videos() -> Path:
    if _OS == "Linux":
        xdg = os.environ.get("XDG_VIDEOS_DIR", "")
        if xdg and Path(xdg).exists():
            return Path(xdg)
    return _get_user_folder("Videos", "Videos")


# Extend safe roots with common user folders (Desktop, Documents, Downloads, etc.)
try:
    for p in (
        _get_desktop(), _get_downloads(), _get_documents(),
        _get_pictures(), _get_music(), _get_videos(),
    ):
        try:
            if p and p.exists() and p.resolve() not in {r.resolve() for r in _SAFE_ROOTS}:
                _SAFE_ROOTS.append(p)
        except Exception:
            continue
except Exception:
    pass


def _resolve_path(raw: str) -> Path:
    raw = os.path.expandvars(str(raw).strip())
    raw = raw.strip('"').strip("'")
    if not raw:
        return Path.home()

    shortcuts: dict[str, Path] = {
        "desktop":   _get_desktop(),
        "downloads": _get_downloads(),
        "documents": _get_documents(),
        "pictures":  _get_pictures(),
        "music":     _get_music(),
        "videos":    _get_videos(),
        "home":      Path.home(),
        "escritorio": _get_desktop(),
        "descargas":  _get_downloads(),
        "documentos": _get_documents(),
        "imagenes":   _get_pictures(),
        "fotos":      _get_pictures(),
        "musica":     _get_music(),
        "videos":     _get_videos(),
    }
    lower = raw.lower()
    if lower in shortcuts:
        return shortcuts[lower]

    if _OS == "Windows":
        raw = raw.replace('/', '\\')
        if raw.startswith('\\\\'):
            raw = '\\\\' + raw[4:].replace('\\\\', '\\')
        else:
            raw = raw.replace('\\\\', '\\')

    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = Path.home() / path
    return Path(os.path.normpath(str(path)))


def _ensure_parent_dir(target: Path) -> Path:
    """Create a parent directory if needed and return the target path."""
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def _check_writable(target: Path) -> bool:
    """Return True if the given path is writable or its parent directory is writable."""
    try:
        if target.exists():
            if target.is_dir():
                test_dir = target
            else:
                return os.access(str(target), os.W_OK)
        else:
            test_dir = target.parent

        if not test_dir.exists() or not test_dir.is_dir():
            return False

        with tempfile.NamedTemporaryFile(prefix=".rex_write_test_", dir=str(test_dir), delete=False) as temp_file:
            temp_file.write(b"rex")
        Path(temp_file.name).unlink(missing_ok=True)
        return True
    except Exception:
        return False


def _set_writable_mode(target: Path) -> None:
    """Clear read-only flags so the current user can write to the path."""
    try:
        if os.name == 'nt':
            os.chmod(str(target), stat.S_IWRITE)
        else:
            os.chmod(str(target), stat.S_IRUSR | stat.S_IWUSR)
    except Exception:
        pass


def _format_size(b: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"


def _open_target(target: Path) -> str:
    if not _is_safe_path(target):
        return f"Access denied: {target}"
    if not target.exists():
        return f"Not found: {target}"
    try:
        resolved = Path(os.path.normpath(str(target)))
        if _OS == "Windows":
            try:
                os.startfile(str(resolved))
            except Exception:
                subprocess.Popen(["explorer", str(resolved)])
        elif _OS == "Darwin":
            subprocess.Popen(["open", str(resolved)])
        else:
            subprocess.Popen(["xdg-open", str(resolved)])
        return f"Opened: {resolved}"
    except Exception as e:
        try:
            if _OS == "Windows":
                safe_path = str(target).replace('/', '\\').strip('"').strip("'")
                subprocess.Popen(f'start "" "{safe_path}"', shell=True)
                return f"Opened: {safe_path}"
        except Exception:
            pass
        return f"Could not open: {e}"


def _safe_trash(target: Path) -> str:

    if not _SEND2TRASH:
        return (
            "send2trash is not installed. "
            "Run: pip install send2trash — "
            "Permanent deletion is disabled for safety."
        )
    send2trash.send2trash(str(target))
    return f"Moved to Trash: {target.name}"


def list_files(path: str = "desktop", show_hidden: bool = False, recursive: bool = False) -> str:
    try:
        target = _resolve_path(path)
        if not _is_safe_path(target):
            return f"Access denied: {target}"
        if not target.exists():
            return f"Path not found: {target}"
        if not target.is_dir():
            return f"Not a directory: {target}"

        items = []
        if recursive:
            for item in sorted(target.rglob("*")):
                if not show_hidden and any(part.startswith(".") for part in item.relative_to(target).parts):
                    continue
                indent = "  " * (len(item.relative_to(target).parts) - 1)
                if item.is_dir():
                    items.append(f"{indent}📁 {item.name}/")
                else:
                    size = _format_size(item.stat().st_size)
                    items.append(f"{indent}📄 {item.name} ({size})")
        else:
            for item in sorted(target.iterdir()):
                if not show_hidden and item.name.startswith("."):
                    continue
                if item.is_dir():
                    items.append(f"📁 {item.name}/")
                else:
                    size = _format_size(item.stat().st_size)
                    items.append(f"📄 {item.name} ({size})")

        if not items:
            return f"Directory is empty: {target.name}/"

        label = f"Contents of {target.name}/"
        if recursive:
            label = f"Contents of {target.name}/ (recursive)"
        return f"{label} ({len(items)} items):\n" + "\n".join(items)

    except PermissionError:
        return f"Permission denied: {path}"
    except Exception as e:
        return f"Error listing files: {e}"


def create_file(path: str, name: str = "", content: str = "") -> str:
    try:
        base   = _resolve_path(path)
        target = (base / name) if name else base
        if not _is_safe_path(target):
            return f"Access denied: {target}"
        target = _ensure_parent_dir(target)
        if not _check_writable(target):
            return f"Permission denied: cannot write to {target.parent}"
        target.write_text(content, encoding="utf-8")
        try:
            if os.name == 'nt':
                os.chmod(str(target), stat.S_IWRITE)
            else:
                os.chmod(str(target), stat.S_IRUSR | stat.S_IWUSR)
        except Exception:
            pass
        return f"File created: {target.name}"
    except PermissionError:
        return f"Permission denied: {target}"
    except Exception as e:
        return f"Could not create file: {e}"


def create_folder(path: str, name: str = "") -> str:
    try:
        base   = _resolve_path(path)
        target = (base / name) if name else base
        if not _is_safe_path(target):
            return f"Access denied: {target}"
        target = _ensure_parent_dir(target)
        if not _check_writable(target.parent):
            return f"Permission denied: cannot create folder in {target.parent}"
        target.mkdir(parents=True, exist_ok=True)
        _set_writable_mode(target)
        return f"Folder created: {target.name}"
    except PermissionError:
        return f"Permission denied: {target}"
    except Exception as e:
        return f"Could not create folder: {e}"


def delete_file(path: str, name: str = "") -> str:
    try:
        base   = _resolve_path(path)
        target = (base / name) if name else base
        if not _is_safe_path(target):
            return f"Access denied: {target}"
        if not target.exists():
            return f"Not found: {target.name}"

        # Güvenli dizin kontrolü — kritik kullanıcı klasörlerini koru
        protected = {
            _get_desktop(), _get_downloads(), _get_documents(),
            _get_pictures(), _get_music(), _get_videos(), Path.home()
        }
        if target.resolve() in {p.resolve() for p in protected}:
            return f"Protected directory, cannot delete: {target.name}"

        return _safe_trash(target)

    except PermissionError:
        return f"Permission denied: {path}"
    except Exception as e:
        return f"Could not delete: {e}"


def move_file(path: str, name: str = "", destination: str = "", overwrite: bool = False) -> str:
    try:
        base   = _resolve_path(path)
        src    = (base / name) if name else base
        dst    = _resolve_path(destination) if destination else None

        if not src.exists():
            return f"Source not found: {src.name}"
        if dst is None:
            return "No destination specified."
        if not _is_safe_path(src):
            return f"Access denied (source): {src}"
        if not _is_safe_path(dst):
            return f"Access denied (destination): {dst}"

        if dst.is_dir():
            dst = dst / src.name

        dst = _ensure_parent_dir(dst)
        if not _check_writable(dst.parent):
            return f"Permission denied: cannot write to {dst.parent}"

        if dst.exists():
            if not overwrite:
                return f"Destination already exists: {dst}"
            if dst.is_dir():
                shutil.rmtree(dst)
            else:
                _set_writable_mode(dst)
                dst.unlink()

        shutil.move(str(src), str(dst))
        return f"Moved: {src.name} → {dst.parent.name}/"

    except PermissionError:
        return f"Permission denied: {destination}"
    except Exception as e:
        return f"Could not move: {e}"


def copy_file(path: str, name: str = "", destination: str = "", overwrite: bool = False) -> str:
    try:
        base = _resolve_path(path)
        src  = (base / name) if name else base
        dst  = _resolve_path(destination) if destination else None

        if not src.exists():
            return f"Source not found: {src.name}"
        if dst is None:
            return "No destination specified."
        if not _is_safe_path(src):
            return f"Access denied (source): {src}"
        if not _is_safe_path(dst):
            return f"Access denied (destination): {dst}"

        if dst.is_dir():
            dst = dst / src.name

        dst = _ensure_parent_dir(dst)
        if not _check_writable(dst.parent):
            return f"Permission denied: cannot write to {dst.parent}"

        if src.is_dir():
            if dst.exists():
                if not overwrite:
                    return f"Destination already exists: {dst}"
                shutil.rmtree(dst)
            shutil.copytree(str(src), str(dst))
        else:
            if dst.exists():
                if not overwrite:
                    return f"Destination already exists: {dst}"
                _set_writable_mode(dst)
                dst.unlink()
            shutil.copy2(str(src), str(dst))

        return f"Copied: {src.name} → {dst.parent.name}/"

    except PermissionError:
        return f"Permission denied: {destination}"
    except Exception as e:
        return f"Could not copy: {e}"


def rename_file(path: str, name: str = "", new_name: str = "") -> str:
    try:
        base     = _resolve_path(path)
        target   = (base / name) if name else base
        if not _is_safe_path(target):
            return f"Access denied: {target}"
        if not target.exists():
            return f"Not found: {target.name}"
        if not new_name:
            return "No new name provided."

        new_path = target.parent / new_name
        if new_path.exists():
            return f"A file named '{new_name}' already exists here."

        target.rename(new_path)
        return f"Renamed: {target.name} → {new_name}"

    except Exception as e:
        return f"Could not rename: {e}"


def read_file(path: str, name: str = "", max_chars: int = 4000) -> str:
    try:
        base   = _resolve_path(path)
        target = (base / name) if name else base
        if not _is_safe_path(target):
            return f"Access denied: {target}"
        if not target.exists():
            return f"File not found: {target.name}"
        if not target.is_file():
            return f"Not a file: {target.name}"

        content = target.read_text(encoding="utf-8", errors="ignore")
        if len(content) > max_chars:
            content = content[:max_chars] + f"\n\n[Truncated — {len(content)} total chars]"
        return content

    except Exception as e:
        return f"Could not read file: {e}"


def write_file(path: str, name: str = "", content: str = "",
               append: bool = False) -> str:
    try:
        base   = _resolve_path(path)
        target = (base / name) if name else base
        if not _is_safe_path(target):
            return f"Access denied: {target}"
        target = _ensure_parent_dir(target)
        if not _check_writable(target):
            return f"Permission denied: cannot write to {target.parent}"
        mode = "a" if append else "w"
        with open(target, mode, encoding="utf-8") as f:
            f.write(content)
        try:
            if os.name == 'nt':
                os.chmod(str(target), stat.S_IWRITE)
            else:
                os.chmod(str(target), stat.S_IRUSR | stat.S_IWUSR)
        except Exception:
            pass
        action = "Appended to" if append else "Written to"
        return f"{action}: {target.name}"
    except PermissionError:
        return f"Permission denied: {target}"
    except Exception as e:
        return f"Could not write file: {e}"


def find_files(name: str = "", extension: str = "",
               path: str = "home", max_results: int = 20) -> str:
    try:
        search_path = _resolve_path(path)
        if not _is_safe_path(search_path):
            return f"Access denied: {search_path}"
        if not search_path.exists():
            return f"Search path not found: {path}"

        results    = []
        dir_count  = 0
        max_dirs   = 500  # performans + güvenlik limiti

        for item in search_path.rglob("*"):
            if item.is_dir():
                dir_count += 1
                if dir_count > max_dirs:
                    break
            if not item.exists():
                continue
            if extension and item.is_dir():
                continue
            if extension and item.suffix.lower() != extension.lower():
                continue
            if name and name.lower() not in item.name.lower():
                continue
            if item.is_dir():
                results.append(f"📁 {item.name}/ — {item.parent}")
            else:
                size = _format_size(item.stat().st_size)
                results.append(f"📄 {item.name} ({size}) — {item.parent}")
            if len(results) >= max_results:
                break

        if not results:
            query = name or extension or "items"
            return f"No {query} found in {search_path.name}/"

        return f"Found {len(results)} result(s):\n" + "\n".join(results)

    except Exception as e:
        return f"Search error: {e}"


def get_largest_files(path: str = "downloads", count: int = 10) -> str:
    count = min(count, 50)  # maksimum 50
    try:
        search_path = _resolve_path(path)
        if not _is_safe_path(search_path):
            return f"Access denied: {search_path}"
        if not search_path.exists():
            return f"Path not found: {path}"

        files = []
        for item in search_path.rglob("*"):
            if item.is_file():
                try:
                    files.append((item.stat().st_size, item))
                except Exception:
                    continue

        files.sort(reverse=True)
        top = files[:count]

        if not top:
            return "No files found."

        lines = [f"Top {len(top)} largest files in {search_path.name}/:"]
        for size, f in top:
            lines.append(f"  {_format_size(size):>10}  {f.name}  ({f.parent})")

        return "\n".join(lines)

    except Exception as e:
        return f"Error: {e}"


def get_disk_usage(path: str = "home") -> str:
    try:
        target = _resolve_path(path)
        usage  = shutil.disk_usage(target)
        pct    = usage.used / usage.total * 100
        return (
            f"Disk usage ({target}):\n"
            f"  Total : {_format_size(usage.total)}\n"
            f"  Used  : {_format_size(usage.used)} ({pct:.1f}%)\n"
            f"  Free  : {_format_size(usage.free)}"
        )
    except Exception as e:
        return f"Could not get disk usage: {e}"


def organize_desktop() -> str:
    type_map = {
        "Images":    {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico", ".heic"},
        "Documents": {".pdf", ".doc", ".docx", ".txt", ".xls", ".xlsx",
                      ".ppt", ".pptx", ".csv", ".odt", ".ods", ".odp"},
        "Videos":    {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"},
        "Music":     {".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"},
        "Archives":  {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"},
        "Code":      {".py", ".js", ".ts", ".html", ".css", ".json", ".xml",
                      ".cpp", ".java", ".cs", ".go", ".rs", ".sh"},
    }

    desktop = _get_desktop()
    moved, skipped = [], []

    try:
        for item in desktop.iterdir():
            # Klasörlere, gizli dosyalara ve organize klasörlerine dokunma
            if item.is_dir() or item.name.startswith("."):
                continue
            if item.name in {k for k in type_map}:
                continue

            ext        = item.suffix.lower()
            target_dir = desktop / "Others"
            for folder, exts in type_map.items():
                if ext in exts:
                    target_dir = desktop / folder
                    break

            target_dir.mkdir(exist_ok=True)
            new_path = target_dir / item.name

            if new_path.exists():
                skipped.append(item.name)
                continue

            shutil.move(str(item), str(new_path))
            moved.append(f"{item.name} → {target_dir.name}/")

        result = f"Desktop organized: {len(moved)} files moved."
        if moved:
            preview = moved[:8]
            result += "\n" + "\n".join(preview)
            if len(moved) > 8:
                result += f"\n... and {len(moved) - 8} more."
        if skipped:
            result += f"\n{len(skipped)} file(s) skipped (name conflict)."
        return result

    except Exception as e:
        return f"Could not organize desktop: {e}"


def get_file_info(path: str, name: str = "") -> str:
    try:
        base   = _resolve_path(path)
        target = (base / name) if name else base
        if not _is_safe_path(target):
            return f"Access denied: {target}"
        if not target.exists():
            return f"Not found: {target.name}"

        stat = target.stat()
        info = {
            "Name":      target.name,
            "Type":      "Folder" if target.is_dir() else "File",
            "Size":      _format_size(stat.st_size),
            "Location":  str(target.parent),
            "Created":   datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M"),
            "Modified":  datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
            "Extension": target.suffix or "—",
        }
        return "\n".join(f"  {k}: {v}" for k, v in info.items())

    except Exception as e:
        return f"Could not get file info: {e}"

def file_controller(
    parameters: dict = None,
    response=None,
    player=None,
    session_memory=None,
) -> str:
    params = parameters or {}
    action = params.get("action", "").lower().strip()
    path   = params.get("path", "desktop")
    name   = params.get("name", "")

    if player:
        player.write_log(f"[file] {action} {name or path}")

    try:
        if action == "list":
            return list_files(
                path,
                show_hidden=bool(params.get("show_hidden", False)),
                recursive=bool(params.get("recursive", False))
            )

        elif action == "create_file":
            return create_file(path, name=name, content=params.get("content", ""))

        elif action == "create_folder":
            return create_folder(path, name=name)

        elif action == "delete":
            return delete_file(path, name=name)

        elif action == "move":
            return move_file(
                path, name=name,
                destination=params.get("destination", ""),
                overwrite=bool(params.get("overwrite", False))
            )

        elif action == "copy":
            return copy_file(
                path, name=name,
                destination=params.get("destination", ""),
                overwrite=bool(params.get("overwrite", False))
            )

        elif action == "open":
            return _open_target(( _resolve_path(path) / name ) if name else _resolve_path(path))

        elif action == "rename":
            return rename_file(path, name=name, new_name=params.get("new_name", ""))

        elif action == "read":
            return read_file(path, name=name)

        elif action == "write":
            return write_file(
                path, name=name,
                content=params.get("content", ""),
                append=params.get("append", False)
            )

        elif action == "find":
            return find_files(
                name=name or params.get("name", ""),
                extension=params.get("extension", ""),
                path=path,
                max_results=min(int(params.get("max_results", 20)), 50),
            )

        elif action == "largest":
            return get_largest_files(
                path=path,
                count=int(params.get("count", 10)),
            )

        elif action == "disk_usage":
            return get_disk_usage(path)

        elif action == "organize_desktop":
            return organize_desktop()

        elif action == "info":
            return get_file_info(path, name=name)

        else:
            return f"Unknown action: '{action}'"

    except Exception as e:
        return f"File controller error ({action}): {e}"