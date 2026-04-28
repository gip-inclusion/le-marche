from datetime import date
from io import StringIO
from unittest.mock import patch

from django.test import TestCase

from lemarche.siaes.management.commands.sync_siaes_decp_details import _select_unique_markets
from lemarche.siaes.models import SiaePublicMarket
from tests.siaes.factories import SiaeFactory


class ApiDecpFetchContractsCountTest(TestCase):
    """Tests du wrapper api_decp.fetch_contracts_count."""

    @patch("lemarche.utils.apis.api_decp.requests.get")
    def test_retourne_le_total_par_siret(self, mocked_get):
        mocked_get.return_value.json.return_value = {"meta": {"total": 5}}
        mocked_get.return_value.raise_for_status.return_value = None

        from lemarche.utils.apis.api_decp import fetch_contracts_count

        result = fetch_contracts_count("12345678901234", "2023-01-01")
        self.assertEqual(result, 5)
        # Un seul appel : SIRET exact a trouvé des résultats, pas de fallback SIREN
        self.assertEqual(mocked_get.call_count, 1)

    @patch("lemarche.utils.apis.api_decp.requests.get")
    def test_fallback_siren_si_siret_vide(self, mocked_get):
        # Premier appel (SIRET) → 0, deuxième appel (SIREN) → 3
        mocked_get.return_value.raise_for_status.return_value = None
        mocked_get.return_value.json.side_effect = [
            {"meta": {"total": 0}},
            {"meta": {"total": 3}},
        ]

        from lemarche.utils.apis.api_decp import fetch_contracts_count

        result = fetch_contracts_count("12345678901234", "2023-01-01")
        self.assertEqual(result, 3)
        self.assertEqual(mocked_get.call_count, 2)

    @patch("lemarche.utils.apis.api_decp.requests.get")
    def test_retourne_zero_si_siret_et_siren_vides(self, mocked_get):
        mocked_get.return_value.raise_for_status.return_value = None
        mocked_get.return_value.json.return_value = {"meta": {"total": 0}}

        from lemarche.utils.apis.api_decp import fetch_contracts_count

        result = fetch_contracts_count("12345678901234", "2023-01-01")
        self.assertEqual(result, 0)

    @patch("lemarche.utils.apis.api_decp.requests.get")
    def test_retourne_zero_si_meta_absent(self, mocked_get):
        mocked_get.return_value.raise_for_status.return_value = None
        mocked_get.return_value.json.return_value = {}

        from lemarche.utils.apis.api_decp import fetch_contracts_count

        result = fetch_contracts_count("12345678901234", "2023-01-01")
        self.assertEqual(result, 0)


class ApiDecpFetchRecentContractsTest(TestCase):
    """Tests du wrapper api_decp.fetch_recent_contracts."""

    @patch("lemarche.utils.apis.api_decp.requests.get")
    def test_retourne_la_liste_data_par_siret(self, mocked_get):
        mocked_get.return_value.json.return_value = {"data": [{"uid": "abc"}, {"uid": "def"}]}
        mocked_get.return_value.raise_for_status.return_value = None

        from lemarche.utils.apis.api_decp import fetch_recent_contracts

        result = fetch_recent_contracts("12345678901234", "2023-01-01")
        self.assertEqual(len(result), 2)
        # SIRET a trouvé des résultats, pas de fallback
        self.assertEqual(mocked_get.call_count, 1)

    @patch("lemarche.utils.apis.api_decp.requests.get")
    def test_fallback_siren_si_siret_vide(self, mocked_get):
        mocked_get.return_value.raise_for_status.return_value = None
        mocked_get.return_value.json.side_effect = [
            {"data": []},
            {"data": [{"uid": "xyz"}]},
        ]

        from lemarche.utils.apis.api_decp import fetch_recent_contracts

        result = fetch_recent_contracts("12345678901234", "2023-01-01")
        self.assertEqual(len(result), 1)
        self.assertEqual(mocked_get.call_count, 2)

    @patch("lemarche.utils.apis.api_decp.requests.get")
    def test_retourne_liste_vide_si_siret_et_siren_vides(self, mocked_get):
        mocked_get.return_value.raise_for_status.return_value = None
        mocked_get.return_value.json.return_value = {"data": []}

        from lemarche.utils.apis.api_decp import fetch_recent_contracts

        result = fetch_recent_contracts("12345678901234", "2023-01-01")
        self.assertEqual(result, [])


class SelectUniqueMarketsTest(TestCase):
    """Tests de la logique de déduplication et filtrage dans sync_siaes_decp_details."""

    def _make_row(self, uid, acheteur_nom="Mairie", objet="Travaux"):
        return {"uid": uid, "acheteur_nom": acheteur_nom, "objet": objet, "montant": 1000}

    def test_retourne_max_3_marchés(self):
        rows = [self._make_row(f"uid-{i}") for i in range(6)]
        result = _select_unique_markets(rows)
        self.assertEqual(len(result), 3)

    def test_deduplique_par_uid(self):
        rows = [self._make_row("uid-1"), self._make_row("uid-1"), self._make_row("uid-2")]
        result = _select_unique_markets(rows)
        self.assertEqual(len(result), 2)

    def test_ignore_ligne_sans_acheteur(self):
        rows = [self._make_row("uid-1", acheteur_nom=""), self._make_row("uid-2")]
        result = _select_unique_markets(rows)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["uid"], "uid-2")

    def test_ignore_ligne_sans_objet(self):
        rows = [self._make_row("uid-1", objet=""), self._make_row("uid-2")]
        result = _select_unique_markets(rows)
        self.assertEqual(len(result), 1)

    def test_retourne_liste_vide_si_vide(self):
        self.assertEqual(_select_unique_markets([]), [])

    def test_retourne_liste_vide_si_toutes_invalides(self):
        rows = [self._make_row("uid-1", acheteur_nom="", objet="")]
        self.assertEqual(_select_unique_markets(rows), [])


class SyncSiaesDecpCommandTest(TestCase):
    """Tests de la commande sync_siaes_decp."""

    @classmethod
    def setUpTestData(cls):
        cls.siae = SiaeFactory(siret="12345678901234", siret_is_valid=True, is_active=True, is_delisted=False)

    @patch("lemarche.utils.apis.api_slack.send_message_to_channel")
    @patch("lemarche.utils.apis.api_decp.fetch_contracts_count")
    def test_wet_run_met_a_jour_has_won_contract(self, mocked_fetch, mocked_slack):
        mocked_fetch.return_value = 3

        from django.core.management import call_command

        call_command("sync_siaes_decp", siret=self.siae.siret, wet_run=True, stdout=StringIO())

        self.siae.refresh_from_db()
        self.assertTrue(self.siae.has_won_contract_last_3_years)
        self.assertEqual(self.siae.decp_contracts_count_last_3_years, 3)
        self.assertIsNotNone(self.siae.decp_last_sync_date)

    @patch("lemarche.utils.apis.api_decp.fetch_contracts_count")
    def test_wet_run_false_si_aucun_contrat(self, mocked_fetch):
        mocked_fetch.return_value = 0

        from django.core.management import call_command

        call_command("sync_siaes_decp", siret=self.siae.siret, wet_run=True, stdout=StringIO())

        self.siae.refresh_from_db()
        self.assertFalse(self.siae.has_won_contract_last_3_years)
        self.assertEqual(self.siae.decp_contracts_count_last_3_years, 0)

    @patch("lemarche.utils.apis.api_decp.fetch_contracts_count")
    def test_dry_run_ne_modifie_pas_la_base(self, mocked_fetch):
        mocked_fetch.return_value = 5
        original_count = self.siae.decp_contracts_count_last_3_years

        from django.core.management import call_command

        call_command("sync_siaes_decp", siret=self.siae.siret, stdout=StringIO())

        self.siae.refresh_from_db()
        self.assertEqual(self.siae.decp_contracts_count_last_3_years, original_count)


class SyncSiaesDecpDetailsCommandTest(TestCase):
    """Tests de la commande sync_siaes_decp_details."""

    @classmethod
    def setUpTestData(cls):
        cls.siae = SiaeFactory(
            siret="12345678901234",
            siret_is_valid=True,
            is_active=True,
            is_delisted=False,
            has_won_contract_last_3_years=True,
        )

    @patch("lemarche.utils.apis.api_slack.send_message_to_channel")
    @patch("lemarche.utils.apis.api_decp.fetch_recent_contracts")
    def test_wet_run_stocke_les_marchés(self, mocked_fetch, mocked_slack):
        mocked_fetch.return_value = [
            {
                "uid": "uid-001",
                "acheteur_nom": "Mairie de Paris",
                "objet": "Prestations de nettoyage",
                "montant": "85000.00",
                "dateNotification": "2024-11-15",
                "datePublicationDonnees": "2024-11-20",
                "codeCPV": "90919000-2",
                "procedure": "Appel d'offres ouvert",
                "lieuExecution_nom": "(75) Paris",
            }
        ]

        from django.core.management import call_command

        call_command("sync_siaes_decp_details", siret=self.siae.siret, wet_run=True, stdout=StringIO())

        markets = SiaePublicMarket.objects.filter(siae=self.siae)
        self.assertEqual(markets.count(), 1)
        market = markets.first()
        self.assertEqual(market.buyer_name, "Mairie de Paris")
        self.assertEqual(market.market_object, "Prestations de nettoyage")
        self.assertEqual(market.award_date, date(2024, 11, 15))
        self.assertEqual(market.cpv_code, "90919000-2")
        self.assertEqual(market.procedure_type, "Appel d'offres ouvert")
        self.assertEqual(market.lieu_execution, "(75) Paris")

    @patch("lemarche.utils.apis.api_decp.fetch_recent_contracts")
    def test_dry_run_ne_stocke_rien(self, mocked_fetch):
        mocked_fetch.return_value = [{"uid": "uid-001", "acheteur_nom": "Mairie", "objet": "Travaux", "montant": None}]

        from django.core.management import call_command

        call_command("sync_siaes_decp_details", siret=self.siae.siret, stdout=StringIO())

        self.assertEqual(SiaePublicMarket.objects.filter(siae=self.siae).count(), 0)

    @patch("lemarche.utils.apis.api_slack.send_message_to_channel")
    @patch("lemarche.utils.apis.api_decp.fetch_recent_contracts")
    def test_wet_run_remplace_les_marchés_existants(self, mocked_fetch, mocked_slack):
        SiaePublicMarket.objects.create(
            siae=self.siae,
            market_uid="ancien-uid",
            buyer_name="Ancien acheteur",
            market_object="Ancien marché",
        )
        mocked_fetch.return_value = [
            {"uid": "nouveau-uid", "acheteur_nom": "Nouvel acheteur", "objet": "Nouveau marché", "montant": None}
        ]

        from django.core.management import call_command

        call_command("sync_siaes_decp_details", siret=self.siae.siret, wet_run=True, stdout=StringIO())

        markets = SiaePublicMarket.objects.filter(siae=self.siae)
        self.assertEqual(markets.count(), 1)
        self.assertEqual(markets.first().market_uid, "nouveau-uid")
