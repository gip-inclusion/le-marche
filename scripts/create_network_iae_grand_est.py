"""
Crée le réseau "IAE Grand Est" et rattache les structures à partir du fichier
scripts/data/iae_grand_est_sirets.csv (colonne SIRET).

Usage :
    docker compose run --rm django python scripts/create_network_iae_grand_est.py
    docker compose run --rm django python scripts/create_network_iae_grand_est.py --dry-run
"""

# ruff: noqa: E402, I001

import csv
import os
import sys


sys.path.insert(0, "/app")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django

django.setup()

from lemarche.networks.models import Network
from lemarche.siaes.models import Siae


NETWORK_NAME = "IAE Grand Est"
CSV_FILE = os.path.join(os.path.dirname(__file__), "data", "iae_grand_est_sirets.csv")
SIRET_COLUMN = "SIRET"

dry_run = "--dry-run" in sys.argv

print("-" * 60)
print(f"{'[DRY RUN] ' if dry_run else ''}Réseau cible : {NETWORK_NAME}")

network, created = Network.objects.get_or_create(name=NETWORK_NAME)
if created:
    print(f"Réseau créé   → ID : {network.id}, slug : {network.slug}")
else:
    print(f"Réseau existant → ID : {network.id}, slug : {network.slug}")

print(f"Structures déjà rattachées : {network.siaes.count()}")
print("-" * 60)

with open(CSV_FILE, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    sirets = [row[SIRET_COLUMN].strip() for row in reader if row[SIRET_COLUMN].strip()]

print(f"{len(sirets)} SIRET(s) à traiter...")
print("-" * 60)

siae_missing = 0
siae_already_linked = 0
siae_newly_linked = 0

for siret in sirets:
    siae_qs = Siae.objects.filter(siret=siret)
    if not siae_qs.exists():
        print(f"  ✗ SIRET introuvable : {siret}")
        siae_missing += 1
    else:
        for siae in siae_qs:
            if network in siae.networks.all():
                siae_already_linked += 1
            else:
                siae_newly_linked += 1
                if not dry_run:
                    siae.networks.add(network)

print("-" * 60)
print("Récapitulatif :")
print(f"  SIRET traités              : {len(sirets)}")
print(f"  Structures rattachées      : {siae_newly_linked}")
print(f"  Déjà rattachées (ignorées) : {siae_already_linked}")
print(f"  SIRET introuvables         : {siae_missing}")
if dry_run:
    print("\n[DRY RUN] Aucune modification effectuée en base.")
