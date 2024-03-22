import os

from django.core.files.storage import default_storage

from lemarche.utils.commands import BaseCommand


class Command(BaseCommand):
    """
    Script to copy images in Django storage system, to use them in fixtures for example

    Usage:
    python manage.py populate_demo_images --images_demo=lemarche/fixtures/django/images/ --folder=original_images
    """

    help = "Ajoute des images de démonstrations au système de stockage de Django"

    def add_arguments(self, parser):
        parser.add_argument(
            "--images_demo", dest="images_demo", type=str, help="Chemin du dossier contenant les images de démo"
        )
        parser.add_argument(
            "--folder", dest="folder", type=str, help="Chemin du dossier de destination", default="original_images"
        )

    def handle(self, *args, **options):
        images_folder = options["images_demo"]
        dest_folder = options["folder"]

        for image_name in os.listdir(images_folder):
            image_path = f"{dest_folder}/{image_name}"
            if not default_storage.exists(image_path):
                with open(os.path.join(images_folder, image_name), "rb") as image_file:
                    default_storage.save(image_path, image_file)
