from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from lemarche.api.inclusive_potential.serializers import InclusivePotentialQuerySerializer
from lemarche.api.inclusive_potential.utils import get_inclusive_potential_data


class InclusivePotentialView(APIView):
    @extend_schema(exclude=True)
    def get(self, request):
        serializer = InclusivePotentialQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        sector = serializer.validated_data.get("sector")
        perimeter = serializer.validated_data.get("perimeter")
        budget = serializer.validated_data.get("budget")
        potential_data, analysis_data = get_inclusive_potential_data(sector, perimeter, budget)

        data = {
            "sector_name": sector.name,
            "perimeter_name": perimeter.name if perimeter else None,
            "perimeter_kind": perimeter.kind if perimeter else None,
            "potential_siaes": potential_data.potential_siaes,
            "insertion_siaes": potential_data.insertion_siaes,
            "handicap_siaes": potential_data.handicap_siaes,
            "local_siaes": potential_data.local_siaes,
            "siaes_with_super_badge": potential_data.siaes_with_super_badge,
            "employees_insertion_average": potential_data.employees_insertion_average,
            "employees_permanent_average": potential_data.employees_permanent_average,
        }
        if budget:
            data.update(analysis_data)

        return Response(data)
