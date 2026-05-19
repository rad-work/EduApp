from urllib.parse import urlencode


def build_query_string(**params: str | int | None) -> str:
    filtered = {key: value for key, value in params.items() if value not in (None, "", [])}
    return urlencode(filtered)
