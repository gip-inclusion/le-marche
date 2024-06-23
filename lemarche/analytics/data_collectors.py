from abc import ABC, abstractmethod


class DataCollector(ABC):
    KIND_GLOBAL = "G"
    KIND_PER_MODEL = "PM"

    @abstractmethod
    def collect_and_save_data(self, before=None, save=True):
        pass
