from django.core.management.base import BaseCommand


class BaseCommand(BaseCommand):
    def stdout_success(self, message):
        return self.stdout.write(self.style.SUCCESS(message))

    def stdout_error(self, message):
        return self.stdout.write(self.style.ERROR(message))

    def stdout_info(self, message):
        return self.stdout.write(self.style.HTTP_INFO(message))

    def stdout_warning(self, message):
        return self.stdout.write(self.style.WARNING(message))

    def stdout_messages_info(self, messages):
        self.stdout_info("-" * 80)
        messages = messages if (type(messages) is list) else [messages]
        for message in messages:
            self.stdout_info(message)

    def stdout_messages_success(self, messages):
        self.stdout_success("-" * 80)
        messages = messages if (type(messages) is list) else [messages]
        for message in messages:
            self.stdout_success(message)

    def stdout_messages_error(self, messages):
        self.stdout_error("-" * 80)
        messages = messages if (type(messages) is list) else [messages]
        for message in messages:
            self.stdout_error(message)
