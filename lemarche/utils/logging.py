from django_datadog_logger.formatters import datadog


class CustomDataDogJSONFormatter(datadog.DataDogJSONFormatter):
    # We don't want those information in our logs
    LOG_KEYS_TO_REMOVE = ["usr.name", "usr.email", "usr.session_key"]

    def json_record(self, message, extra, record):
        log_entry_dict = super().json_record(message, extra, record)

        # Remove the keys we don't want in the logs
        for log_key in self.LOG_KEYS_TO_REMOVE:
            if log_key in log_entry_dict:
                del log_entry_dict[log_key]

        # Redact the token in the URL
        if "http.url" in log_entry_dict:
            token_index = log_entry_dict["http.url"].find("token")
            if token_index != -1:
                log_entry_dict["http.url"] = log_entry_dict["http.url"][:token_index] + "token=[REDACTED]"

        # Redact the token in the message
        if "message" in log_entry_dict:
            token_index = log_entry_dict["message"].find("token")
            if token_index != -1:
                log_entry_dict["message"] = log_entry_dict["message"][:token_index] + "token=[REDACTED]"

        return log_entry_dict
