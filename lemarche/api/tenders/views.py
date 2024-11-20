from django.conf import settings
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from lemarche.api.tenders.serializers import TenderSerializer
from lemarche.api.utils import BasicChoiceSerializer
from lemarche.tenders import constants as tender_constants
from lemarche.tenders.models import Tender
from lemarche.users import constants as user_constants
from lemarche.utils.emails import add_to_contact_list
from lemarche.www.tenders.utils import get_or_create_user_from_anonymous_content


PARTNER_APPROCH_UPDATE_FIELDS = ["title", "description", "deadline_date", "external_link"]


class TenderViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TenderSerializer

    @extend_schema(
        summary="Déposer un besoin d'achat",
        tags=[Tender._meta.verbose_name_plural],
        parameters=[
            OpenApiParameter(name="token", description="Token Utilisateur", required=True, type=str),
        ],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, args, kwargs)

    def perform_create(self, serializer: TenderSerializer):
        """
        - set Tender source
        - set Tender author (create user if it doesn't exist)
        - pop non-model fields
        - create Tender !
        """
        tender_source = (
            tender_constants.SOURCE_TALLY
            if serializer.validated_data.get("extra_data", {}).get("source") == tender_constants.SOURCE_TALLY
            else tender_constants.SOURCE_API
        )
        user_source = (
            user_constants.SOURCE_TALLY_FORM
            if (tender_source == tender_constants.SOURCE_TALLY)
            else user_constants.SOURCE_SIGNUP_FORM
        )
        # get Tender author
        user = get_or_create_user_from_anonymous_content(
            serializer.validated_data,
            source=user_source,
        )
        # Manage Partner APProch
        if tender_source == tender_constants.SOURCE_API:
            if user.id == settings.PARTNER_APPROCH_USER_ID:
                tender_partner_approch_id = serializer.validated_data.get("extra_data", {}).get("id", None)
                if tender_partner_approch_id:
                    # try to find an existing tender (same id + kind)
                    # if found, update some fields
                    # if not found, create it !
                    try:
                        tender = Tender.objects.get(
                            partner_approch_id=tender_partner_approch_id, kind=serializer.validated_data.get("kind")
                        )
                        for field in PARTNER_APPROCH_UPDATE_FIELDS:
                            setattr(tender, field, serializer.validated_data.get(field))
                        tender.save(update_fields=PARTNER_APPROCH_UPDATE_FIELDS)
                        return
                    except Tender.DoesNotExist:
                        serializer.validated_data["partner_approch_id"] = tender_partner_approch_id
        # pop non-model fields
        serializer.validated_data.pop("contact_kind", None)
        serializer.validated_data.pop("contact_buyer_kind_detail", None)
        # create Tender
        tender = serializer.save(
            author=user,
            status=tender_constants.STATUS_PUBLISHED,
            published_at=timezone.now(),
            source=tender_source,
            import_raw_object=self.request.data,
        )
        add_to_contact_list(user=user, type="signup", source=user_source, tender=tender)


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
