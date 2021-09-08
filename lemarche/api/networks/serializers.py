from rest_framework import serializers

from lemarche.networks.models import Network


class NetworkSerializer(serializers.ModelSerializer):

    class Meta:
        model = Network
        fields = [
            "name",
            "slug",
            "brand",
            "website",
        ]
