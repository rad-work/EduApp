from urllib.parse import urlencode


def build_query_string(**params: str | int | list[str] | None) -> str:
    pairs: list[tuple[str, str]] = []
    for key, value in params.items():
        if value in (None, "", []):
            continue
        if isinstance(value, list):
            for item in value:
                if item not in (None, ""):
                    pairs.append((key, str(item)))
        else:
            pairs.append((key, str(value)))
    return urlencode(pairs)
