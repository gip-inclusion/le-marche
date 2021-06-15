import factory


class SectorFactory(factory.django.DjangoModelFactory):
    id = "ABA1"
    parent = None
    lft = "AVA4"
    lvl = "0"
    rgt = "AVA4"
    root = None


class DirectoryFactory(factory.django.DjangoModelFactory):
    id = 12
    name = "SIAE"
    brand = "Super Siae"
    siret = "12345678900001"
    email = "jean@example.com"
    kind = "AI"
    website = "https://example.com"
    city = "Toulouse"
    post_code = "15019"
    department = "2A"
    region = "Grand Est"
