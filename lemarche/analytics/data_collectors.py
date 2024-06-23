from abc import ABC, abstractmethod


class DataCollector(ABC):
    @abstractmethod
    def collect_data(self):
        pass
