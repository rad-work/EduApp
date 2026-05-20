"""Поддерживаемые языки посылок и нормализация значения."""

from typing import Final

ALLOWED_SUBMISSION_LANGUAGES: Final[frozenset[str]] = frozenset({"python", "c", "cpp", "java"})

# Имя исходного файла в рабочей директории контейнера (/work)
SOURCE_FILENAMES: Final[dict[str, str]] = {
    "python": "main.py",
    "c": "main.c",
    "cpp": "main.cpp",
    "java": "Main.java",
}

# Подписи для выпадающего списка: версии должны соответствовать образу runner (runner/Dockerfile).
# При обновлении базового образа или пакетов Debian при необходимости обновите строки ниже.
SUBMISSION_LANGUAGE_CHOICES: Final[list[tuple[str, str]]] = [
    ("python", "Python 3.12.13"),
    ("c", "GCC 14.2.0 · C17"),
    ("cpp", "G++ 14.2.0 · C++20"),
    ("java", "OpenJDK 21 · javac 21.0.11"),
]


def normalize_submission_language(raw: str) -> str | None:
    """Приводит ввод пользователя/API к ключу языка или None, если язык не поддерживается."""
    s = raw.strip().lower().replace(" ", "")
    if s in ("c++", "cplusplus", "cpp", "cxx"):
        s = "cpp"
    if s in ALLOWED_SUBMISSION_LANGUAGES:
        return s
    return None


def container_source_path(language: str) -> str:
    """Путь до исходника внутри монтированного /work (language уже нормализован)."""
    return f"/work/{SOURCE_FILENAMES[language]}"
