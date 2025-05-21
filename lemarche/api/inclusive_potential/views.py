from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from lemarche.api.inclusive_potential.serializers import InclusivePotentialQuerySerializer
from lemarche.siaes.constants import KIND_HANDICAP_LIST, KIND_INSERTION_LIST
from lemarche.siaes.models import Siae


class InclusivePotentialView(APIView):

    @extend_schema(
        parameters=[InclusivePotentialQuerySerializer],
        responses={200: None},
    )
    def get(self, request):
        serializer = InclusivePotentialQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        sector = serializer.validated_data.get("sector")
        perimeter = serializer.validated_data.get("perimeter")

        siaes = Siae.objects.filter_with_potential_through_activities(sector, perimeter)

        insertion_siaes = 0
        handicap_siaes = 0
        siaes_with_super_badge = 0
        for siae in siaes:
            if siae.kind in KIND_INSERTION_LIST:
                insertion_siaes += 1
            elif siae.kind in KIND_HANDICAP_LIST:
                handicap_siaes += 1

            if siae.super_badge:
                siaes_with_super_badge += 1

        return Response(
            {
                "sector_name": sector.name,
                "perimeter_name": perimeter.name if perimeter else None,
                "perimeter_kind": perimeter.kind if perimeter else None,
                "potential_siaes": siaes.count(),
                "insertion_siaes": insertion_siaes,
                "handicap_siaes": handicap_siaes,
                "siaes_with_super_badge": siaes_with_super_badge,
            }
        )
