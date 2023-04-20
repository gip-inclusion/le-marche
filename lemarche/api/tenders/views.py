from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, viewsets

from lemarche.api.tenders.serializers import TenderSerializer
from lemarche.api.utils import BasicChoiceSerializer, check_user_token
from lemarche.tenders import constants as tender_constants
from lemarche.tenders.models import Tender


class TenderViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = TenderSerializer

    @extend_schema(
        summary="Déposer un besoin d'achat",
        tags=[Tender._meta.verbose_name_plural],
        parameters=[
            OpenApiParameter(name="token", description="Token Utilisateur", required=True, type=str),
        ],
    )
    def create(self, request, *args, **kwargs):
        token = request.GET.get("token", None)
        self.user = check_user_token(token)
        return super().create(request, args, kwargs)

    def perform_create(self, serializer):
        serializer.save(
            author=self.user,
            status=Tender.STATUS_PUBLISHED,
            source=Tender.SOURCE_API,
            import_raw_object=self.request.POST,
        )


class TenderKindViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = BasicChoiceSerializer
    queryset = Tender.objects.none()

    def get_queryset(self):
        tender_kinds = [{"id": id, "name": name} for (id, name) in tender_constants.KIND_CHOICES]
        return tender_kinds

    @extend_schema(summary="Lister tous les types de besoins d'achat", tags=[Tender._meta.verbose_name_plural])
    def list(self, request, *args, **kwargs):
        return super().list(request, args, kwargs)


class TenderAmountViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = BasicChoiceSerializer
    queryset = Tender.objects.none()

    def get_queryset(self):
        tender_amounts = [{"id": id, "name": name} for (id, name) in tender_constants.AMOUNT_RANGE_CHOICES]
        return tender_amounts

    @extend_schema(summary="Lister tous les montants de besoins d'achat", tags=[Tender._meta.verbose_name_plural])
    def list(self, request, *args, **kwargs):
        return super().list(request, args, kwargs)
