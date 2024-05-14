from rest_framework import serializers

from lemarche.tenders.models import Tender


class SimpleTenderSerializer(serializers.ModelSerializer):
    slug = serializers.CharField(read_only=True)
    company_name = serializers.CharField(source="author.company.name", read_only=True)
    company_slug = serializers.CharField(source="author.company.slug", read_only=True)
    author_email = serializers.CharField(source="author.email", read_only=True)

    class Meta:
        model = Tender
        fields = [
            "created_at",
            "updated_at",
            "title",
            "slug",
            "kind",
            "presta_type",
            "amount",
            "amount_exact",
            "status",
            "source",
            "author_email",
            "company_name",
            "company_slug",
        ]
