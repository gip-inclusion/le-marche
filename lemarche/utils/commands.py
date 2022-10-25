from django.core.management.base import BaseCommand


class BaseCommand(BaseCommand):
    def stdout_success(self, message):
        return self.stdout.write(self.style.SUCCESS(message))

    def stdout_error(self, message):
        return self.stdout.write(self.style.ERROR(message))

    def stdout_info(self, message):
        return self.stdout.write(self.style.HTTP_INFO(message))

    def stdout_messages_info(self, messages):
        self.stdout_info("-" * 80)
        messages = messages if (type(messages) == list) else [messages]
        for message in messages:
            self.stdout_info(message)
        self.stdout_info("-" * 80)

    def stdout_messages_success(self, messages):
        self.stdout_success("-" * 80)
        messages = messages if (type(messages) == list) else [messages]
        for message in messages:
            self.stdout_success(message)
        self.stdout_success("-" * 80)
