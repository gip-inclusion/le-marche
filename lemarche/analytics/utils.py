import importlib
import inspect

from django.apps import apps

from .data_collectors import DataCollector


def get_all_data_collectors():
    data_collector_classes = []

    # get all installed apps
    for app_config in apps.get_app_configs():
        try:
            # Import all data collectors
            collectors_module = importlib.import_module(f"{app_config.name}.data_collectors")
        except ModuleNotFoundError:
            continue

        # Inspect each member to find sub-classes of DataCollector
        for name, obj in inspect.getmembers(collectors_module, inspect.isclass):
            if issubclass(obj, DataCollector) and obj is not DataCollector:
                data_collector_classes.append(obj)

    return data_collector_classes
