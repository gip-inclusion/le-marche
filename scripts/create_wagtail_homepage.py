# script to use inside shell of django
from wagtail.models import Page

from lemarche.cms.models import HomePage


def create_homepage():
    root = Page.get_first_root_node()
    homepage = HomePage(title="Page d'accueil", slug="accueil")
    root.add_child(instance=homepage)


def delete_homepage():
    # we can only have one homepage
    hp = HomePage.objects.first()
    hp.delete()
