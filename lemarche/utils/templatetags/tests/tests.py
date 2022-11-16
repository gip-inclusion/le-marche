from django.test import TestCase

from lemarche.sectors.factories import SectorFactory
from lemarche.siaes.factories import SiaeFactory
from lemarche.utils.templatetags.siae_sectors_display import siae_sectors_display


class SiaeSectorDisplayTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae_with_one_sector = SiaeFactory()
        cls.siae_with_two_sectors = SiaeFactory()
        cls.siae_with_many_sectors = SiaeFactory()
        cls.siae_etti = SiaeFactory(kind="ETTI")
        sector_1 = SectorFactory(name="Entretien")
        sector_2 = SectorFactory(name="Agro")
        sector_3 = SectorFactory(name="Hygiène")
        sector_4 = SectorFactory(name="Bâtiment")
        sector_5 = SectorFactory(name="Informatique")
        cls.siae_with_one_sector.sectors.add(sector_1)
        cls.siae_with_two_sectors.sectors.add(sector_1, sector_2)
        cls.siae_with_many_sectors.sectors.add(sector_1, sector_2, sector_3, sector_4, sector_5)
        cls.siae_etti.sectors.add(sector_1, sector_2, sector_3, sector_4, sector_5)

    def test_should_return_list_of_siae_sector_strings(self):
        self.assertEqual(siae_sectors_display(self.siae_with_one_sector), "Entretien")
        self.assertEqual(siae_sectors_display(self.siae_with_two_sectors), "Agro, Entretien")  # default ordering: name
        self.assertEqual(
            siae_sectors_display(self.siae_with_many_sectors), "Agro, Bâtiment, Entretien, Hygiène, Informatique"
        )

    def test_should_filter_list_of_siae_sectors(self):
        self.assertEqual(
            siae_sectors_display(self.siae_with_many_sectors, display_max=3), "Agro, Bâtiment, Entretien, …"
        )

    def test_should_return_list_in_the_specified_format(self):
        self.assertEqual(siae_sectors_display(self.siae_with_two_sectors, output_format="list"), ["Agro", "Entretien"])
        self.assertEqual(
            siae_sectors_display(self.siae_with_two_sectors, output_format="li"), "<li>Agro</li><li>Entretien</li>"
        )

    def test_should_have_different_behavior_for_etti(self):
        self.assertEqual(siae_sectors_display(self.siae_etti), "Multisectoriel")

    def test_should_filter_list_on_current_search_query(self):
        self.assertEqual(siae_sectors_display(self.siae_with_one_sector, current_search_query="sectors=agro"), "")
        self.assertEqual(
            siae_sectors_display(self.siae_with_two_sectors, current_search_query="sectors=entretien"), "Entretien"
        )
        self.assertEqual(
            siae_sectors_display(self.siae_with_many_sectors, current_search_query="sectors=entretien&sectors=agro"),
            "Agro, Entretien",
        )
        # priority is on current_search (over ETTI)
        self.assertEqual(
            siae_sectors_display(self.siae_etti, current_search_query="sectors=entretien&sectors=agro"),
            "Agro, Entretien",
        )
