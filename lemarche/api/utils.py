import random
import string

from rest_framework import serializers


def custom_preprocessing_hook(endpoints):
    """
    Only show /api/* in the generated documentation
    Helps to filter out /cms/* stuff
    https://github.com/tfranzel/drf-spectacular/issues/655
    """
    filtered = []
    for path, path_regex, method, callback in endpoints:
        if path.startswith("/api/"):
            filtered.append((path, path_regex, method, callback))
    return filtered


def generate_random_string(n=64):
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


class BasicChoiceSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()


class BasicChoiceWithParentSerializer(BasicChoiceSerializer):
    parent = serializers.CharField()
