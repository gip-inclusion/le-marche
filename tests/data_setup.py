from lemarche.cocorico import models as app_models

import lemarche.cocorico.factories as f
import factory


def basic_setup(self):
    self.sector = f.SectorFactory()
    self.directory = f.DirectoryFactory()
