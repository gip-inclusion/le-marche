# common blocks
from django.utils.translation import gettext as _
from wagtail.core import blocks


class ButtonBlock(blocks.StructBlock):
    """An external or internal URL."""

    title = blocks.CharBlock(required=True, max_length=60)
    button_page = blocks.PageChooserBlock(required=False, help_text=_("If selected, this url will be used first"))
    button_url = blocks.URLBlock(
        required=False, help_text=_("If added, this url will be used secondarily to the button page")
    )

    # def get_context(self, request, *args, **kwargs):
    #     context = super().get_context(request, *args, **kwargs)
    #     context['latest_posts'] = BlogDetailPage.objects.live().public()[:3]
    #     return context

    class Meta:  # noqa
        template = "streams/button_block.html"
        icon = "placeholder"
        label = _("Single Button")
        # value_class = LinkStructValue


class StatsWebsite(blocks.StructBlock):
    """A stats of marche website section"""

    # def get_context(self, request, *args, **kwargs):
    #     context = super().get_context(request, *args, **kwargs)
    #     context['latest_posts'] = BlogDetailPage.objects.live().public()[:3]
    #     return context

    class Meta:  # noqa
        template = "cms/streams/stats_website.html"
        icon = "pen"
        label = _("Statistique du marche")


class SectionTheyPublishTenders(blocks.StructBlock):

    title = blocks.CharBlock(default="Ils ont publié un besoin sur le marché", required=True, max_length=120)

    class Meta:  # noqa
        template = "cms/streams/section_they_publish_tenders.html"
        icon = "pen"
        label = _("Ils ont publié un besoin sur le marché")


class SectionStudiesCasesTenders(blocks.StructBlock):

    title = blocks.CharBlock(default="100% des besoins ont reçu des réponses en 24h", required=True, max_length=120)
    subtitle = blocks.CharBlock(default="Gagnez du temps en utilisant le marché.", required=True, max_length=120)

    class Meta:  # noqa
        template = "cms/streams/section_studies_cases_tenders.html"
        icon = "pen"
        label = _("Etude de cas")


class SectionOurSiaes(blocks.StructBlock):
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

    class Meta:  # noqa
        template = "cms/streams/section_our_siaes.html"
        icon = "pen"
        label = _("Section nos structures")


class SectionOurRessources(blocks.StructBlock):

    title = blocks.CharBlock(default="Nos ressources", required=True, max_length=120)

    class Meta:  # noqa
        template = "cms/streams/section_our_ressources.html"
        icon = "pen"
        label = _("Nos ressources")


class SectionWhatFindHere(blocks.StructBlock):

    title = blocks.CharBlock(default="Sur le marché", required=True, max_length=120)

    class Meta:  # noqa
        template = "cms/streams/section_what_find_here.html"
        icon = "pen"
        label = _("Avantages marché")


class SectionOurPartners(blocks.StructBlock):

    title = blocks.CharBlock(default="Les partenaires du marché", required=True, max_length=120)

    class Meta:  # noqa
        template = "cms/streams/section_our_partners.html"
        icon = "pen"
        label = _("Nos partenaires")
