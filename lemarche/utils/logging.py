from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.urls import resolve
from django_datadog_logger.formatters import datadog


REDACTED = "[REDACTED]"


def is_sensitive_query_param(name: str) -> bool:
    """Query string parameters whose value is a secret (e.g. django-sesame token, API key)"""
    name = name.lower()
    return name in ("key", "api_key") or any(word in name for word in ("token", "password", "secret"))


# URL path parameters whose value is a secret (Django & allauth password reset, allauth email confirmation)
SENSITIVE_URL_KWARGS = ("token", "key")


def get_path_secrets(path: str) -> list[str]:
    try:
        resolver_match = resolve(path)
    except Exception:  # we cannot crash the log formatter under any circumstances
        return []
    return [
        value
        for name, value in resolver_match.kwargs.items()
        if name in SENSITIVE_URL_KWARGS and isinstance(value, str) and value
    ]


def redact_path(path: str) -> str:
    for secret in get_path_secrets(path):
        path = path.replace(secret, REDACTED)
    return path


def redact_url(url: str) -> str:
    """Redact secrets in the path and in the query string of an URL (absolute or not)"""
    try:
        split_url = urlsplit(url)
        query = urlencode(
            [
                (name, REDACTED if is_sensitive_query_param(name) else value)
                for name, value in parse_qsl(split_url.query, keep_blank_values=True)
            ],
            safe="[]",
        )
        return urlunsplit(split_url._replace(path=redact_path(split_url.path), query=query))
    except Exception:  # we cannot crash the log formatter under any circumstances
        return REDACTED


class CustomDataDogJSONFormatter(datadog.DataDogJSONFormatter):
    # We don't want those information in our logs
    LOG_KEYS_TO_REMOVE = ["usr.name", "usr.email", "usr.session_key"]

    def json_record(self, message, extra, record):
        log_entry_dict = super().json_record(message, extra, record)

        # Remove the keys we don't want in the logs
        for log_key in self.LOG_KEYS_TO_REMOVE:
            if log_key in log_entry_dict:
                del log_entry_dict[log_key]

        # Redact the secrets (tokens, keys…) in the URLs: path segments & query string
        secrets = []
        if log_entry_dict.get("http.url_details.path"):
            secrets += get_path_secrets(log_entry_dict["http.url_details.path"])
            log_entry_dict["http.url_details.path"] = redact_path(log_entry_dict["http.url_details.path"])
        if log_entry_dict.get("http.url_details.queryString"):
            query_string = log_entry_dict["http.url_details.queryString"]
            secrets += [str(value) for name, value in query_string.items() if is_sensitive_query_param(name)]
            log_entry_dict["http.url_details.queryString"] = {
                name: REDACTED if is_sensitive_query_param(name) else value for name, value in query_string.items()
            }
        for log_key in ["http.url", "http.referer"]:
            if log_entry_dict.get(log_key):
                log_entry_dict[log_key] = redact_url(log_entry_dict[log_key])

        # Redact the secrets in the message
        if log_entry_dict.get("message"):
            for secret in secrets:
                if secret:
                    log_entry_dict["message"] = log_entry_dict["message"].replace(secret, REDACTED)
            token_index = log_entry_dict["message"].find("token")
            if token_index != -1:
                log_entry_dict["message"] = log_entry_dict["message"][:token_index] + "token=[REDACTED]"

        return log_entry_dict
