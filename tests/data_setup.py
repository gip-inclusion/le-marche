from itou_c4_api.cocorico import models as app_models

import itou_c4_api.cocorico.factories as f
import factory


def basic_setup(self):
    self.sector = f.SectorFactory()
    self.directory = f.DirectoryFactory()
