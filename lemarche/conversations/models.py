from uuid import uuid4

from django.conf import settings
from django.db import IntegrityError, models
from django.db.models import Func, IntegerField, Q
from django.utils import timezone
from django.utils.text import slugify
from django_extensions.db.fields import ShortUUIDField
from shortuuid import uuid


class ConversationQuerySet(models.QuerySet):
    def has_answer(self):
        return self.exclude(data=[])

    def with_answer_count(self):
        return self.annotate(answer_count=Func("data", function="jsonb_array_length", output_field=IntegerField()))

    def get_conv_from_uuid(self, conv_uuid: str, version=1):
        """get conv form
        Args:
            conv_uuid (str): _description_

        Returns:
            [VERSION, UUID, KIND_SENDER]
        """
        if version == 0:
            return self.get(uuid=conv_uuid)
        else:
            return self.get(Q(sender_encoded__endswith=conv_uuid) | Q(siae_encoded__endswith=conv_uuid))


class Conversation(models.Model):
    KIND_SEARCH = "SEARCH"
    KIND_TENDER = "TENDER"
    KIND_CHOICES = (
        (KIND_SEARCH, "Recherche"),
        (KIND_TENDER, "Dépôt de besoin"),
    )

    USER_KIND_SENDER_TO_BUYER = "b"
    USER_KIND_SENDER_TO_SIAE = "s"

    uuid = ShortUUIDField(
        verbose_name="Identifiant UUID",
        default=uuid,
        editable=False,
        unique=True,
        db_index=True,
        auto_created=True,
    )

    sender_encoded = models.CharField(
        verbose_name="Identifiant initiateur", unique=True, db_index=True, max_length=255
    )
    siae_encoded = models.CharField(verbose_name="Identifiant structure", unique=True, db_index=True, max_length=255)
    version = models.PositiveIntegerField(verbose_name="Version", default=1)

    kind = models.CharField(
        verbose_name="Type de conversation", default=KIND_SEARCH, choices=KIND_CHOICES, max_length=10, db_index=True
    )
    sender_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Utilisateur à l'initiative",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    sender_email = models.EmailField(verbose_name="Email de l'initiateur de la conversation", null=True)
    sender_first_name = models.CharField(verbose_name="Prénom", max_length=150)
    sender_last_name = models.CharField(verbose_name="Nom", max_length=150)

    title = models.CharField(verbose_name="Objet de la première demande", max_length=200)
    initial_body_message = models.TextField(verbose_name="Message initial", blank=True)
    siae = models.ForeignKey(
        "siaes.Siae", verbose_name="Structure", on_delete=models.CASCADE, null=True, related_name="conversations"
    )

    data = models.JSONField(default=list)

    created_at = models.DateTimeField(verbose_name="Date de création", default=timezone.now)
    updated_at = models.DateTimeField(verbose_name="Date de modification", auto_now=True)
    validated_at = models.DateTimeField(verbose_name="Date de validation", blank=True, null=True)

    objects = models.Manager.from_queryset(ConversationQuerySet)()

    class Meta:
        verbose_name = "Conversation"

    def __str__(self):
        return self.title

    def set_sender_encoded(self):
        """
        The UUID of sender.
        """
        if not self.sender_encoded:
            slug_sender_full_name = slugify(self.sender_full_name).replace("-", "_")
            self.sender_encoded = f"{slug_sender_full_name}_{str(uuid4())[:4]}"

    def set_siae_encoded(self):
        """
        The UUID of siae.
        """
        if not self.siae_encoded:
            if self.siae.contact_full_name:
                siae_slug_full_name = slugify(self.siae.contact_full_name).replace("-", "_")
            else:
                siae_slug_full_name = self.siae.slug.replace("-", "_")
            self.siae_encoded = f"{siae_slug_full_name}_{str(uuid4())[:4]}"

    def save(self, *args, **kwargs):
        """
        - generate the uuid field
        """
        try:
            self.set_sender_encoded()
            self.set_siae_encoded()
            super().save(*args, **kwargs)
        except IntegrityError as e:
            # check that it's a new UUID conflict
            # Full message expected: duplicate key value violates unique constraint "conversations_conversation_sender_encoded_0f0b821f_uniq" DETAIL:  Key (sender_encoded)=(...) already exists.  # noqa
            if "conversations_conversation_sender_encoded" in str(e):
                self.set_sender_encoded()
                super().save(*args, **kwargs)
            if "conversations_conversation_siae_encoded" in str(e):
                self.set_siae_encoded()
                super().save(*args, **kwargs)
            else:
                raise e

    def get_user_kind(self, conv_uuid):
        # method only available in version >= 1
        if self.sender_encoded.endswith(conv_uuid):
            return self.USER_KIND_SENDER_TO_BUYER
        elif self.siae_encoded.endswith(conv_uuid):
            return self.USER_KIND_SENDER_TO_SIAE

    @property
    def sender_email_buyer(self):
        return self.sender_email

    @property
    def sender_full_name(self):
        return f"{self.sender_first_name} {self.sender_last_name}"

    @property
    def sender_email_buyer_encoded(self):
        if self.version == 0:
            # for legacy
            return f"{self.uuid}_{self.USER_KIND_SENDER_TO_BUYER}@{settings.INBOUND_PARSING_DOMAIN_EMAIL}"
        if self.version == 1:
            return f"{self.sender_encoded}@{settings.INBOUND_PARSING_DOMAIN_EMAIL}"

    @property
    def sender_email_siae_encoded(self):
        if self.version == 0:
            # for legacy
            return f"{self.uuid}_{self.USER_KIND_SENDER_TO_SIAE}@{settings.INBOUND_PARSING_DOMAIN_EMAIL}"
        if self.version == 1:
            return f"{self.siae_encoded}@{settings.INBOUND_PARSING_DOMAIN_EMAIL}"

    @property
    def sender_email_siae(self):
        return self.siae.contact_email

    @property
    def nb_messages(self):
        """Number of messages is the len of data item + the initial message

        Returns:
            int: Number of all messages
        """
        return len(self.data) + 1

    @property
    def is_validated(self) -> bool:
        return self.validated_at is not None

    def set_validated(self):
        self.validated_at = timezone.now()
        self.save()
