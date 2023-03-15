from rest_framework import serializers

from lemarche.tenders.models import Tender


class TenderSerializer(serializers.ModelSerializer):
    sectors = serializers.SlugRelatedField(
        slug_field="slug", many=True, read_only=True, allow_null=True, required=False
    )
    location = serializers.SlugRelatedField(slug_field="slug", read_only=True, allow_null=True, required=False)

    class Meta:
        model = Tender
        fields = [
            # general
            "kind",
            "title",
            "sectors",
            "presta_type",
            "location",
            "is_country_area",
            # description
            "description",
            "start_working_date",
            "external_link",
            "constraints",
            "amount",
            "why_amount_is_blank",
            "accept_share_amount",
            "accept_cocontracting",
            # contact
            "contact_first_name",
            "contact_last_name",
            "contact_email",
            "contact_phone",
            "response_kind",
            "deadline_date",
        ]
