import factory

import lemarche.cocorico.factories as f
from lemarche.cocorico import models as app_models


def basic_setup(self):
    # self.sector = f.SectorFactory()
    self.directory = f.DirectoryFactory()
