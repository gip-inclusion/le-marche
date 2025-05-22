from rest_framework import serializers

from lemarche.perimeters.models import Perimeter
from lemarche.sectors.models import Sector


class InclusivePotentialQuerySerializer(serializers.Serializer):
    sector = serializers.SlugRelatedField(
        queryset=Sector.objects.all(),
        slug_field="slug",
        required=True,
        error_messages={
            "does_not_exist": "Le secteur avec ce slug n'existe pas.",
            "required": "Le paramètre 'sector' est requis.",
        },
    )
    perimeter = serializers.SlugRelatedField(
        queryset=Perimeter.objects.all(),
        slug_field="slug",
        required=False,
        error_messages={
            "does_not_exist": "Le périmètre avec ce slug n'existe pas.",
        },
    )
    budget = serializers.IntegerField(required=False)
