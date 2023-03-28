# common blocks
from wagtail import blocks


class StatsWebsite(blocks.StructBlock):
    """A stats of marche website section"""

    # def get_context(self, request, *args, **kwargs):

    class Meta:
        template = "cms/streams/stats_website.html"
        icon = "pen"
        label = "Statistique du marche"


class TendersTestimonialsSection(blocks.StructBlock):

    title = blocks.CharBlock(default="Ils ont publié un besoin sur le marché", required=True, max_length=120)

    class Meta:
        template = "cms/streams/section_they_publish_tenders.html"
        icon = "pen"
        label = "Ils ont publié un besoin sur le marché"


class TendersStudiesCasesSection(blocks.StructBlock):

    title = blocks.CharBlock(default="100% des besoins ont reçu des réponses en 24h", required=True, max_length=120)
    subtitle = blocks.CharBlock(default="Gagnez du temps en utilisant le marché.", required=True, max_length=120)

    class Meta:
        template = "cms/streams/section_studies_cases_tenders.html"
        icon = "pen"
        label = "Etude de cas"


class OurSiaesSection(blocks.StructBlock):
    """An external or internal URL."""

    title = (
        blocks.CharBlock(
            default="Les prestataires inclusifs, des partenaires d'excellence", required=True, max_length=60
        ),
    )
    subtitle = blocks.RichTextBlock(
        default="""
            Faire appel à nos 8500 prestataires inclusifs, c'est la garantie d'être accompagné
            par des professionnels reconnus et certifiés dans leur domaine.
        """,
        required=True,
        features=["bold", "italic"],
    )
    # constats = blocks.StreamBlock(
    #     [
    #         (
    #             "constat",
    #             ConstatBlock(),
    #         )
    #     ],
    #     min_num=1,
    #     max_num=3,
    # )

    class Meta:
        template = "cms/streams/section_our_siaes.html"
        icon = "pen"
        label = "Section nos structures"


class OurRessourcesSection(blocks.StructBlock):

    title = blocks.CharBlock(default="Nos ressources", required=True, max_length=120)

    class Meta:
        template = "cms/streams/section_our_ressources.html"
        icon = "pen"
        label = "Nos ressources"


class WhatFindHereSection(blocks.StructBlock):

    title = blocks.CharBlock(default="Sur le marché", required=True, max_length=120)

    class Meta:
        template = "cms/streams/section_what_find_here.html"
        icon = "pen"
        label = "Avantages marché"


class OurPartnersSection(blocks.StructBlock):

    title = blocks.CharBlock(default="Les partenaires du marché", required=True, max_length=120)

    class Meta:
        template = "cms/streams/section_our_partners.html"
        icon = "pen"
        label = "Nos partenaires"
