from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import importlib.util
import re
from typing import Iterable


@dataclass(frozen=True)
class MissingDependency:
    package: str
    import_name: str


_IMPORT_NAME_OVERRIDES = {
    "google-genai": "google.genai",
    "google-generativeai": "google.generativeai",
    "beautifulsoup4": "bs4",
    "duckduckgo-search": "duckduckgo_search",
    "opencv-python": "cv2",
    "pillow": "PIL",
    "send2trash": "send2trash",
    "youtube-transcript-api": "youtube_transcript_api",
    "python-pptx": "pptx",
    "python-docx": "docx",
    "pyqt6": "PyQt6",
}


def _normalize_package_name(line: str) -> str:
    s = line.replace("\ufeff", "").strip()
    if not s or s.startswith("#"):
        return ""

    # Remove inline comments.
    s = s.split("#", 1)[0].strip()
    if not s:
        return ""

    # Remove version specifiers and environment markers.
    # Examples: package==1.0.0, package>=1.0; python_version>='3.10'
    s = re.split(r"[<>=!~;]", s, maxsplit=1)[0].strip()
    return s.lower()


def _package_to_import_name(package: str) -> str:
    if package in _IMPORT_NAME_OVERRIDES:
        return _IMPORT_NAME_OVERRIDES[package]
    return package.replace("-", "_")


def _is_import_available(import_name: str) -> bool:
    try:
        return importlib.util.find_spec(import_name) is not None
    except Exception:
        return False


def parse_requirements(requirements_path: Path) -> list[str]:
    if not requirements_path.exists():
        return []

    packages: list[str] = []
    for raw in requirements_path.read_text(encoding="utf-8-sig").splitlines():
        pkg = _normalize_package_name(raw)
        if pkg:
            packages.append(pkg)
    return packages


def check_project_dependencies(requirements_path: Path) -> list[MissingDependency]:
    missing: list[MissingDependency] = []
    for package in parse_requirements(requirements_path):
        import_name = _package_to_import_name(package)
        if not _is_import_available(import_name):
            missing.append(MissingDependency(package=package, import_name=import_name))
    return missing


def build_install_command(packages: Iterable[str], python_executable: str = "python") -> str:
    cleaned = [p for p in packages if p]
    if not cleaned:
        return ""
    quoted_python = f'"{python_executable}"'
    return f"{quoted_python} -m pip install " + " ".join(cleaned)
