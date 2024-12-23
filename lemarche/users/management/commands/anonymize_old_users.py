from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Update and anonymize inactive users past a defined inactivity period"""
