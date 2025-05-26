from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from lemarche.api.inclusive_potential.constants import RECOMMENDATIONS
from lemarche.api.inclusive_potential.serializers import InclusivePotentialQuerySerializer
from lemarche.siaes.constants import KIND_HANDICAP_LIST, KIND_INSERTION_LIST
from lemarche.siaes.models import Siae


class InclusivePotentialView(APIView):

    @extend_schema(
        parameters=[InclusivePotentialQuerySerializer],
        responses={200: None},
    )
    def get(self, request):  # noqa: C901
        serializer = InclusivePotentialQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        sector = serializer.validated_data.get("sector")
        perimeter = serializer.validated_data.get("perimeter")
        budget = serializer.validated_data.get("budget")

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

        siaes_count = siaes.count()
        analysis_data = {}
        if budget:
            # Get all valid CA values from siaes and calculate the average manually to avoid to many fat queries
            ca_values = [siae.ca or siae.api_entreprise_ca for siae in siaes if siae.ca or siae.api_entreprise_ca]
            if ca_values:
                analysis_data["ca_average"] = round(sum(ca_values) / len(ca_values))
                analysis_data["eco_dependency"] = round(budget / analysis_data["ca_average"] * 100)

            if siaes_count > 30:
                if "eco_dependency" in analysis_data and analysis_data["eco_dependency"] < 30:
                    recommendation = RECOMMENDATIONS["reservation"]
                else:
                    recommendation = RECOMMENDATIONS["lot"]
            elif siaes_count > 10:
                recommendation = RECOMMENDATIONS["lot"]
            elif siaes_count > 1:
                recommendation = RECOMMENDATIONS["clause"]
            else:
                recommendation = RECOMMENDATIONS["aucun"]

            recommendation["explanation"] = (
                recommendation["explanation"].format(
                    siaes_count=siaes_count,
                    eco_dependency=analysis_data["eco_dependency"],
                    ca_average=analysis_data["ca_average"],
                )
                if "eco_dependency" in analysis_data and "ca_average" in analysis_data
                else None
            )
            analysis_data["recommendation"] = recommendation

        data = {
            "sector_name": sector.name,
            "perimeter_name": perimeter.name if perimeter else None,
            "perimeter_kind": perimeter.kind if perimeter else None,
            "potential_siaes": siaes_count,
            "insertion_siaes": insertion_siaes,
            "handicap_siaes": handicap_siaes,
            "siaes_with_super_badge": siaes_with_super_badge,
        }
        if budget:
            data.update(analysis_data)

        return Response(data)
