from django.db import migrations


SIRETS = [
    "41841943800050",
    "34373752400128",
    "34373752400094",
    "42156728000027",
    "41902631500020",
    "85006394200013",
    "49864436800017",
    "41990306700025",
    "50045854200031",
    "42143076000049",
    "49971814600032",
    "39384485700036",
    "40168908800029",
    "89326867200027",
    "89795939100011",
    "44066204700015",
    "89217217200017",
    "43281485300005",
    "37816144200108",
    "37816144200090",
    "45231025300029",
    "44066204700057",
    "42463098600497",
    "88464124200026",
    "77811508900055",
    "88096979500082",
    "34819435800035",
    "40101593800350",
    "40101593800459",
    "40219166200640",
    "87922327900032",
    "75094891100029",
    "89357967200021",
    "44066204700024",
    "42921893600038",
    "82371229400136",
    "82298489400029",
    "53468714000028",
    "82461183400022",
    "48044602000038",
    "38178866000086",
    "44066204700023",
    "44066204700018",
    "52968348400016",
    "44066204700022",
    "41982940300023",
]


def add_reseau_iae(apps, schema_editor):
    Network = apps.get_model("networks", "Network")
    Siae = apps.get_model("siaes", "Siae")

    network, _ = Network.objects.get_or_create(
        slug="act-essonne",
        defaults={
            "name": "Act'Essonne",
            "brand": "",
            "website": "",
        },
    )

    for siret in SIRETS:
        for siae in Siae.objects.filter(siret=siret):
            siae.networks.add(network)


def remove_reseau_iae(apps, schema_editor):
    Network = apps.get_model("networks", "Network")
    network = Network.objects.filter(slug="act-essonne").first()
    if network:
        network.siaes.clear()
        network.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("networks", "0001_initial"),
        ("siaes", "0002_alter_historicalsiae_name_alter_siae_name"),
    ]

    operations = [
        migrations.RunPython(add_reseau_iae, remove_reseau_iae),
    ]
