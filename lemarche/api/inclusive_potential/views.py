from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from lemarche.api.inclusive_potential.serializers import InclusivePotentialQuerySerializer
from lemarche.api.inclusive_potential.utils import get_score_inclusif
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

        inclusive_potential = get_score_inclusif(siaes.count())

        return Response(
            {
                "sector_name": sector.name,
                "perimeter_name": perimeter.name if perimeter else None,
                "perimeter_kind": perimeter.kind if perimeter else None,
                "potential_siaes": siaes.count(),
                "score_inclusif": inclusive_potential.score_inclusif,
                "inclusif_interpretation": inclusive_potential.inclusif_interpretation,
            }
        )
