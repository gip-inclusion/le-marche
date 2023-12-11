from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, viewsets

from lemarche.api.tenders.serializers import TenderSerializer
from lemarche.api.utils import BasicChoiceSerializer, check_user_token
from lemarche.tenders import constants as tender_constants
from lemarche.tenders.models import Tender
from lemarche.users import constants as user_constants
from lemarche.www.tenders.utils import get_or_create_user_from_anonymous_content


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
        check_user_token(token)
        return super().create(request, args, kwargs)

    def perform_create(self, serializer: TenderSerializer):
        """
        - set Tender source
        - set Tender author (create user if it doesn't exist)
        - pop non-model fields
        - create Tender !
        """
        source = (
            tender_constants.SOURCE_TALLY
            if serializer.validated_data.get("extra_data", {}).get("source") == tender_constants.SOURCE_TALLY
            else tender_constants.SOURCE_API
        )
        # get Tender author
        user = get_or_create_user_from_anonymous_content(
            serializer.validated_data,
            source=user_constants.SOURCE_TALLY_FORM
            if source == tender_constants.SOURCE_TALLY
            else user_constants.SOURCE_SIGNUP_FORM,
        )
        # pop non-model fields
        serializer.validated_data.pop("contact_kind", None)
        serializer.validated_data.pop("contact_buyer_kind_detail", None)
        # create Tender
        serializer.save(
            author=user,
            status=tender_constants.STATUS_PUBLISHED,
            published_at=timezone.now(),
            source=source,
            import_raw_object=self.request.data,
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
