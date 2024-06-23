from abc import ABC, abstractmethod


class DataCollector(ABC):
    @abstractmethod
    def collect_and_save_data(self, before=None, save=True):
        pass
