"""Русские подписи для значений enum и служебных строк в UI."""

DIFFICULTY_LABELS: dict[str, str] = {
    "easy": "Лёгкая",
    "medium": "Средняя",
    "hard": "Сложная",
}

STATUS_LABELS: dict[str, str] = {
    "pending": "Ожидает",
    "queued": "В очереди",
    "running": "Выполняется",
    "completed": "Завершена",
    "failed": "Ошибка",
}

VERDICT_LABELS: dict[str, str] = {
    "accepted": "Принято",
    "wrong_answer": "Неверный ответ",
    "time_limit_exceeded": "Превышен лимит времени",
    "memory_limit_exceeded": "Превышен лимит памяти",
    "runtime_error": "Ошибка выполнения",
    "compilation_error": "Ошибка компиляции",
    "presentation_error": "Ошибка формата вывода",
    "system_error": "Системная ошибка",
}

MESSAGE_LABELS: dict[str, str] = {
    "No test cases configured for problem": "Для задачи не настроены тесты",
    "Compilation failed": "Ошибка компиляции",
    "Output mismatch": "Ответ не совпадает с эталоном",
    "All tests passed": "Все тесты пройдены",
    "Docker runner unavailable": "Среда проверки недоступна",
}

# Ключи в нижнем регистре (как в БД). Неизвестные теги показываем с пробелами вместо подчёркиваний.
TAG_LABELS: dict[str, str] = {
    "implementation": "Реализация",
    "math": "Математика",
    "greedy": "Жадные алгоритмы",
    "dp": "Динамическое программирование",
    "data_structures": "Структуры данных",
    "graphs": "Графы",
    "trees": "Деревья",
    "strings": "Строки",
    "geometry": "Геометрия",
    "binary_search": "Бинарный поиск",
    "two_pointers": "Два указателя",
    "sorting": "Сортировка",
    "combinatorics": "Комбинаторика",
    "number_theory": "Теория чисел",
    "dfs_and_bfs": "DFS и BFS",
    "shortest_paths": "Кратчайшие пути",
    "divide_and_conquer": "Разделяй и властвуй",
    "bitmasks": "Битовые маски",
    "constructive": "Конструктив",
    "simulation": "Симуляция",
    "games": "Теория игр",
    "flows": "Потоки в сетях",
    "dsu": "СНМ (объединение множеств)",
    "hashing": "Хеширование",
    "interactive": "Интерактив",
}


def _label(mapping: dict[str, str], value: object | None) -> str:
    if value is None:
        return "—"
    key = value.value if hasattr(value, "value") else str(value)
    return mapping.get(key, key.replace("_", " "))


def difficulty_label(value: object | None) -> str:
    return _label(DIFFICULTY_LABELS, value)


def status_label(value: object | None) -> str:
    return _label(STATUS_LABELS, value)


def verdict_label(value: object | None) -> str:
    return _label(VERDICT_LABELS, value)


def message_label(value: object | None) -> str:
    if value is None or value == "":
        return ""
    text = str(value)
    return MESSAGE_LABELS.get(text, text)


def tag_label(name: str | None) -> str:
    if name is None or name == "":
        return ""
    key = str(name).strip().lower()
    return TAG_LABELS.get(key, key.replace("_", " "))
