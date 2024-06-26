import logging
from datetime import timedelta

from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from sesame.utils import get_query_string as sesame_get_query_string

from lemarche.siaes.models import Siae
from lemarche.tenders import constants as tender_constants
from lemarche.tenders.models import PartnerShareTender, Tender, TenderSiae
from lemarche.users.models import User
from lemarche.utils import constants
from lemarche.utils.apis import api_brevo, api_mailjet, api_slack
from lemarche.utils.data import date_to_string
from lemarche.utils.emails import send_mail_async, whitelist_recipient_list
from lemarche.utils.urls import get_domain_url, get_object_admin_url, get_object_share_url


logger = logging.getLogger(__name__)


def send_validated_tender(tender: Tender):
    # find the matching Siaes? done in Tender post_save signal
    # notify author
    # TODO: we still notify author for each send ?
    send_confirmation_published_email_to_author(tender, nb_matched_siaes=tender.siaes.count())
    # send the tender to all matching Siaes & Partners
    send_tender_emails_to_siaes(tender)
    send_tender_emails_to_partners(tender)
    # set first_sent_at & last_sent_at, log
    tender.set_sent()


def send_validated_sent_batch_tender(tender: Tender):
    # the tender has already been sent a first time with send_validated_tender
    # this is the second/third/... iteration
    send_tender_emails_to_siaes(tender)
    # update last_sent_at, log
    tender.set_sent()


def restart_send_tender_task(tender: Tender):
    # send the tender to all matching Siaes & Partners
    send_tender_emails_to_siaes(tender)
    send_tender_emails_to_partners(tender)
    # log
    log_item = {
        "action": "restart_send",
        "date": timezone.now().isoformat(),
    }
    tender.logs.append(log_item)
    tender.save()


# @task()
def send_tender_emails_to_siaes(tender: Tender):
    """
    All corresponding Siae will be contacted
    - we send emails to both the Siae's 'contact_email' & the Siae's users 'email'
    - but we avoid sending duplicate emails

    previous email_subject: f"{tender.get_kind_display()} : {tender.title} ({tender.author.company_name})"
    """
    if tender.source == tender_constants.SOURCE_TALLY:
        tender_title_splitted = " ".join(tender.title.split()[:3])
        email_subject = f"{tender.get_kind_display()} : {tender_title_splitted}..."
    else:
        email_subject = "J'ai une opportunité commerciale pour vous sur le Marché de l'inclusion"

    # queryset
    all_siaes = tender.siaes.filter(tendersiae__email_send_date=None).order_by_super_siaes()
    logger.info(f"total siaes {all_siaes.count()}")
    siaes = all_siaes[: tender.limit_send_to_siae_batch]

    siae_users_count = 0
    siae_users_send_count = 0

    for siae in siaes:
        # send to siae 'contact_email'
        send_tender_email_to_siae(tender, siae, email_subject)
        # also send to the siae's user(s) 'email' (if its value is different)
        for user in siae.users.all():
            siae_users_count += 1
            if user.email != siae.contact_email:
                send_tender_email_to_siae(tender, siae, email_subject, recipient_to_override=user)
                siae_users_send_count += 1

    # log email batch
    siaes_log_item = {
        "action": "email_siaes_matched",
        "email_subject": email_subject,
        "email_count": siaes.count(),
        "email_timestamp": timezone.now().isoformat(),
    }
    tender.logs.append(siaes_log_item)
    logger.info(siaes_log_item)

    siae_users_log_item = {
        "action": "email_siae_users_matched",
        "email_subject": email_subject,
        "email_count": siae_users_send_count,
        "email_timestamp": timezone.now().isoformat(),
        "siae_users_count": siae_users_count,
    }
    tender.logs.append(siae_users_log_item)
    logger.info(siae_users_log_item)

    tender.save()


def send_tender_emails_to_partners(tender: Tender):
    """
    All corresponding partners (PartnerShareTender) will be contacted
    """
    partners = PartnerShareTender.objects.filter_by_tender(tender)
    partners_count = partners.count()

    if partners_count > 0:
        email_subject = f"{tender.get_kind_display()} : {tender.title} ({tender.author.company_name})"
        for partner in partners:
            send_tender_email_to_partner(email_subject, tender, partner)

            # log email batch
            log_item = {
                "action": "email_partners_matched",
                "email_subject": email_subject,
                "email_count": partners_count,
                "email_timestamp": timezone.now().isoformat(),
            }
            tender.logs.append(log_item)
            tender.save()


def send_tender_email_to_partner(email_subject: str, tender: Tender, partner: PartnerShareTender):
    recipient_list = whitelist_recipient_list(partner.contact_email_list)
    if recipient_list:
        variables = {
            "TENDER_TITLE": tender.title,
            "TENDER_AUTHOR_COMPANY": tender.author.company_name,
            "TENDER_SECTORS": tender.sectors_list_string(),
            "TENDER_PERIMETERS": tender.location_display,
            "TENDER_DEADLINE_DATE": date_to_string(tender.deadline_date),
            "TENDER_URL": get_object_share_url(tender),
        }

        api_mailjet.send_transactional_email_many_recipient_with_template(
            template_id=settings.MAILJET_TENDERS_PARTNER_PRESENTATION_TEMPLATE_ID,
            subject=email_subject,
            recipient_email_list=recipient_list,
            variables=variables,
            from_email=settings.TEAM_CONTACT_EMAIL,
            from_name="Pauline du Marché de l'inclusion",
        )

        # log email
        log_item = {
            "action": "email_tender",
            "email_to": recipient_list,
            "email_subject": email_subject,
            # "email_body": email_body,
            "email_timestamp": timezone.now().isoformat(),
            "metadata": {
                "tender_id": tender.id,
                "tender_title": tender.title,
                "tender_author_company_name": tender.author.company_name,
            },
        }
        partner.logs.append(log_item)
        partner.save()


# @task()
def send_tender_email_to_siae(tender: Tender, siae: Siae, email_subject: str, recipient_to_override: User = None):
    # override siae.contact_email if email_to_override is provided
    email_to = recipient_to_override.email if recipient_to_override else siae.contact_email
    recipient_list = whitelist_recipient_list([email_to])
    if recipient_list:
        recipient_email = recipient_list[0] if recipient_list else ""
        recipient_name = siae.contact_full_name

        tender_url = f"{get_object_share_url(tender)}?siae_id={siae.id}"
        tender_not_interested_url = f"{get_object_share_url(tender)}?siae_id={siae.id}&not_interested=True"
        if recipient_to_override:
            tender_url += f"&user_id={recipient_to_override.id}"
            tender_not_interested_url += f"&user_id={recipient_to_override.id}"

        variables = {
            "SIAE_CONTACT_FIRST_NAME": siae.contact_first_name,
            "SIAE_SECTORS": siae.sectors_list_string(),
            "SIAE_PERIMETER": siae.geo_range_pretty_display,
            "TENDER_TITLE": tender.title,
            "TENDER_AUTHOR_COMPANY": tender.author.company_name,
            "TENDER_KIND": tender.get_kind_display(),
            "TENDER_SECTORS": tender.sectors_list_string(),
            "TENDER_PERIMETERS": tender.location_display,
            "TENDER_AMOUNT": tender.amount_display,
            "TENDER_DEADLINE_DATE": date_to_string(tender.deadline_date),
            "TENDER_URL": tender_url,
            "TENDER_NOT_INTERESTED_URL": tender_not_interested_url,
        }

        api_mailjet.send_transactional_email_with_template(
            template_id=settings.MAILJET_TENDERS_SIAE_PRESENTATION_TEMPLATE_ID,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            variables=variables,
            subject=email_subject,
            from_email=settings.TEAM_CONTACT_EMAIL,
            from_name="Pauline du Marché de l'inclusion",
        )

        # update tendersiae
        tendersiae = TenderSiae.objects.get(tender=tender, siae=siae)
        tendersiae.email_send_date = timezone.now()
        log_item = {
            "action": "email_sent",
            "email_to": recipient_email,
            "email_subject": email_subject,
            "email_timestamp": timezone.now().isoformat(),
        }
        tendersiae.logs.append(log_item)
        tendersiae.save()


def send_tender_contacted_reminder_email_to_siaes(
    tender: Tender, days_since_email_send_date=2, send_on_weekends=False
):
    if days_since_email_send_date == 2:
        email_subject = f"Un {tender.get_kind_display().lower()} pour vous sur le Marché de l'inclusion"
        template_id = settings.MAILJET_TENDERS_SIAE_CONTACTED_REMINDER_2D_TEMPLATE_ID
    elif days_since_email_send_date == 3:
        email_subject = f"Avez vous consulté le {tender.get_kind_display().lower()} ?"
        template_id = settings.MAILJET_TENDERS_SIAE_CONTACTED_REMINDER_3D_TEMPLATE_ID
    elif days_since_email_send_date == 4:
        email_subject = f"L'opportunité : {tender.get_kind_display().lower()} a besoin de votre réponse !"
        template_id = settings.MAILJET_TENDERS_SIAE_CONTACTED_REMINDER_4D_TEMPLATE_ID
    else:
        error_message = f"send_tender_contacted_reminder_email_to_siaes: days_since_email_send_date has a non-managed value ({days_since_email_send_date})"  # noqa
        raise Exception(error_message)

    current_weekday = timezone.now().weekday()

    # queryset
    lt_days_ago = timezone.now() - timedelta(days=days_since_email_send_date)
    gte_days_ago = timezone.now() - timedelta(days=days_since_email_send_date + 1)
    if current_weekday == 0 and not send_on_weekends:
        # Monday: special case (need to account for Saturday & Sunday)
        gte_days_ago = timezone.now() - timedelta(days=days_since_email_send_date + 1 + 2)
    tendersiae_contacted_reminder_list = TenderSiae.objects.filter(tender_id=tender.id).email_click_reminder(
        gte_days_ago=gte_days_ago, lt_days_ago=lt_days_ago
    )

    for tendersiae in tendersiae_contacted_reminder_list:
        # send to siae 'contact_email'
        send_tender_contacted_reminder_email_to_siae(
            tendersiae, email_subject, template_id, days_since_email_send_date
        )

    # log email batch
    log_item = {
        "action": f"email_siaes_contacted_reminder_{days_since_email_send_date}d",
        "email_subject": email_subject,
        "email_count": tendersiae_contacted_reminder_list.count(),
        "email_timestamp": timezone.now().isoformat(),
    }
    tender.logs.append(log_item)
    tender.save()


def send_tender_contacted_reminder_email_to_siae(
    tendersiae: TenderSiae, email_subject, template_id, days_since_email_send_date
):
    recipient_list = whitelist_recipient_list([tendersiae.siae.contact_email])
    if recipient_list:
        recipient_email = recipient_list[0] if recipient_list else ""
        recipient_name = tendersiae.tender.author.full_name

        variables = {
            "SIAE_CONTACT_FIRST_NAME": tendersiae.siae.contact_first_name,
            "SIAE_SECTORS": tendersiae.siae.sectors_list_string(),
            "SIAE_PERIMETER": tendersiae.siae.geo_range_pretty_display,
            "TENDER_TITLE": tendersiae.tender.title,
            "TENDER_AUTHOR_COMPANY": tendersiae.tender.author.company_name,
            "TENDER_KIND": tendersiae.tender.get_kind_display(),
            "TENDER_SECTORS": tendersiae.tender.sectors_list_string(),
            "TENDER_PERIMETERS": tendersiae.tender.location_display,
            "TENDER_AMOUNT": tendersiae.tender.amount_display,
            "TENDER_DEADLINE_DATE": date_to_string(tendersiae.tender.deadline_date),
            "TENDER_URL": f"{get_object_share_url(tendersiae.tender)}?siae_id={tendersiae.siae.id}&mtm_campaign=relance-esi-contactees",  # noqa
        }

        api_mailjet.send_transactional_email_with_template(
            template_id=template_id,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            variables=variables,
            subject=email_subject,
        )

        # log email
        log_item = {
            "action": f"email_siae_contacted_reminder_{days_since_email_send_date}d",
            "email_to": recipient_email,
            "email_subject": email_subject,
            # "email_body": email_body,
            "email_timestamp": timezone.now().isoformat(),
        }
        tendersiae.logs.append(log_item)
        tendersiae.save()


def send_tender_interested_reminder_email_to_siaes(
    tender: Tender, days_since_detail_contact_click_date=2, send_on_weekends=False
):
    email_subject = f"{tender.title}"

    current_weekday = timezone.now().weekday()

    # queryset
    lt_days_ago = timezone.now() - timedelta(days=days_since_detail_contact_click_date)
    gte_days_ago = timezone.now() - timedelta(days=days_since_detail_contact_click_date + 1)
    if current_weekday == 0 and not send_on_weekends:
        # Monday: special case (need to account for Saturday & Sunday)
        gte_days_ago = timezone.now() - timedelta(days=days_since_detail_contact_click_date + 1 + 2)
    tendersiae_interested_reminder_list = TenderSiae.objects.filter(
        tender_id=tender.id
    ).detail_contact_click_post_reminder(gte_days_ago=gte_days_ago, lt_days_ago=lt_days_ago)

    for tendersiae in tendersiae_interested_reminder_list:
        # send to siae 'contact_email'
        send_tender_interested_reminder_email_to_siae(tendersiae, email_subject, days_since_detail_contact_click_date)

    # log email batch
    log_item = {
        "action": f"email_siaes_interested_reminder_{days_since_detail_contact_click_date}d",
        "email_subject": email_subject,
        "email_count": tendersiae_interested_reminder_list.count(),
        "email_timestamp": timezone.now().isoformat(),
    }
    tender.logs.append(log_item)
    tender.save()


def send_tender_interested_reminder_email_to_siae(
    tendersiae: TenderSiae, email_subject, days_since_detail_contact_click_date
):
    recipient_list = whitelist_recipient_list([tendersiae.siae.contact_email])
    if recipient_list:
        recipient_email = recipient_list[0] if recipient_list else ""
        recipient_name = tendersiae.tender.author.full_name

        variables = {
            "SIAE_CONTACT_FIRST_NAME": tendersiae.siae.contact_first_name,
            "SIAE_SECTORS": tendersiae.siae.sectors_list_string(),
            "SIAE_PERIMETER": tendersiae.siae.geo_range_pretty_display,
            "TENDER_TITLE": tendersiae.tender.title,
            "TENDER_AUTHOR_COMPANY": tendersiae.tender.author.company_name,
            "TENDER_KIND": tendersiae.tender.get_kind_display(),
            "TENDER_SECTORS": tendersiae.tender.sectors_list_string(),
            "TENDER_PERIMETERS": tendersiae.tender.location_display,
            "TENDER_AMOUNT": tendersiae.tender.amount_display,
            "TENDER_DEADLINE_DATE": date_to_string(tendersiae.tender.deadline_date),
            "TENDER_URL": f"{get_object_share_url(tendersiae.tender)}?siae_id={tendersiae.siae.id}&mtm_campaign=relance-esi-interessees",  # noqa
        }

        api_mailjet.send_transactional_email_with_template(
            template_id=settings.MAILJET_TENDERS_SIAE_INTERESTED_REMINDER_2D_TEMPLATE_ID,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            variables=variables,
            subject=email_subject,
        )

        # log email
        log_item = {
            "action": f"email_siae_interested_reminder_{days_since_detail_contact_click_date}d",
            "email_to": recipient_email,
            "email_subject": email_subject,
            # "email_body": email_body,
            "email_timestamp": timezone.now().isoformat(),
        }
        tendersiae.logs.append(log_item)
        tendersiae.save()


def send_confirmation_published_email_to_author(tender: Tender, nb_matched_siaes: int):
    """Send email to the author when the tender is published to the siaes

    Args:
        tender (Tender): Tender published
        nb_matched (int): number of siaes match
    """
    email_subject = f"Votre {tender.get_kind_display().lower()} a été publié !"
    recipient_list = whitelist_recipient_list([tender.author.email])
    if recipient_list and not tender.contact_notifications_disabled:
        recipient_email = recipient_list[0] if recipient_list else ""
        recipient_name = tender.author.full_name

        variables = {
            "TENDER_AUTHOR_FIRST_NAME": tender.author.first_name,
            "TENDER_TITLE": tender.title,
            "TENDER_KIND": tender.get_kind_display(),
            "TENDER_SECTORS": tender.sectors_list_string(),
            "TENDER_PERIMETERS": tender.location_display,
            "TENDER_AMOUNT": tender.amount_display,
            "TENDER_DEADLINE_DATE": date_to_string(tender.deadline_date),
            "TENDER_NB_MATCH": nb_matched_siaes,
            "TENDER_URL": get_object_share_url(tender),
        }

        api_mailjet.send_transactional_email_with_template(
            template_id=settings.MAILJET_TENDERS_AUTHOR_CONFIRMATION_VALIDATED_TEMPLATE_ID,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            variables=variables,
            subject=email_subject,
        )

        # log email
        log_item = {
            "action": "email_publish_confirmation",
            "email_to": recipient_email,
            "email_subject": email_subject,
            # "email_body": email_body,
            "email_timestamp": timezone.now().isoformat(),
        }
        tender.logs.append(log_item)
        tender.save()


def send_siae_interested_email_to_author(tender: Tender):
    """
    The author is notified (by intervals) when new Siaes show interest (detail_contact_click_date set)

    Intervals:
    - first Siae
    - second Siae
    - 5th Siae
    - every 5 additional Siae (10th, 15th, ... up until 50)

    If tender_siae_detail_contact_click_count reaches 50, then the author will have received 12 emails
    """
    tender_siae_detail_contact_click_count = TenderSiae.objects.filter(
        tender=tender, detail_contact_click_date__isnull=False
    ).count()

    if (tender_siae_detail_contact_click_count > 0) and (tender_siae_detail_contact_click_count <= 50):
        should_send_email = False

        if tender_siae_detail_contact_click_count == 1:
            should_send_email = True
            email_subject = "Un premier prestataire intéressé !"
            template_id = settings.MAILJET_TENDERS_AUTHOR_SIAE_INTERESTED_1_TEMPLATE_ID
        elif tender_siae_detail_contact_click_count == 2:
            should_send_email = True
            email_subject = "Un deuxième prestataire intéressé !"
            template_id = settings.MAILJET_TENDERS_AUTHOR_SIAE_INTERESTED_2_TEMPLATE_ID
        elif tender_siae_detail_contact_click_count == 5:
            should_send_email = True
            email_subject = "Un cinquième prestataire intéressé !"
            template_id = settings.MAILJET_TENDERS_AUTHOR_SIAE_INTERESTED_5_TEMPLATE_ID
        elif tender_siae_detail_contact_click_count % 5 == 0:
            should_send_email = True
            email_subject = "5 nouveaux prestataires intéressés !"
            template_id = settings.MAILJET_TENDERS_AUTHOR_SIAE_INTERESTED_5_MORE_TEMPLATE_ID
        else:
            pass

        if should_send_email:
            recipient_list = whitelist_recipient_list([tender.author.email])  # tender.contact_email ?
            if recipient_list and not tender.contact_notifications_disabled:
                recipient_email = recipient_list[0] if recipient_list else ""
                recipient_name = tender.author.full_name

                variables = {
                    "TENDER_AUTHOR_FIRST_NAME": tender.author.first_name,
                    "TENDER_TITLE": tender.title,
                    "TENDER_SIAE_INTERESTED_LIST_URL": f"{get_object_share_url(tender)}/prestataires",  # noqa
                }

                api_mailjet.send_transactional_email_with_template(
                    template_id=template_id,
                    recipient_email=recipient_email,
                    recipient_name=recipient_name,
                    variables=variables,
                    subject=email_subject,
                )

                # log email
                log_item = {
                    "action": "email_siae_interested",
                    "email_to": recipient_email,
                    "email_subject": email_subject,
                    # "email_body": email_body,
                    "email_timestamp": timezone.now().isoformat(),
                }
                tender.logs.append(log_item)
                tender.save()


def notify_admin_tender_created(tender: Tender):
    email_subject = f"Marché de l'inclusion : dépôt de besoin, ajout d'un nouveau {tender.get_kind_display()}"
    tender_admin_url = get_object_admin_url(tender)
    data_to_send = {
        "tender_id": tender.id,
        "tender_title": tender.title,
        "tender_kind": tender.get_kind_display(),
        "tender_location": tender.location_display,
        "tender_deadline_date": tender.deadline_date,
        "tender_author_full_name": tender.contact_full_name,
        "tender_author_email": tender.author.email,
        "tender_author_company": tender.author.company_name,
        "tender_scale_marche_useless": tender.get_scale_marche_useless_display(),
        "tender_status": tender.get_status_display(),
        "tender_source": tender.get_source_display(),
        "tender_admin_url": tender_admin_url,
    }
    email_body = render_to_string("tenders/create_notification_email_admin_body.txt", data_to_send)
    send_mail_async(
        email_subject=email_subject,
        email_body=email_body,
        recipient_list=[settings.NOTIFY_EMAIL],
    )
    api_slack.send_message_to_channel(text=email_body, service_id=settings.SLACK_WEBHOOK_C4_TENDER_CHANNEL)


def send_tenders_author_feedback_or_survey(tender: Tender, kind="feedback_30d"):
    email_subject = f"Suite à votre {tender.get_kind_display().lower()}"
    recipient_list = whitelist_recipient_list([tender.author.email])
    if recipient_list and not tender.contact_notifications_disabled:
        recipient_email = recipient_list[0] if recipient_list else ""
        recipient_name = tender.author.full_name

        variables = {
            "TENDER_AUTHOR_FIRST_NAME": tender.author.first_name,
            "TENDER_TITLE": tender.title,
            "TENDER_VALIDATE_AT": tender.first_sent_at.strftime("%d %B %Y"),  # TODO: TENDER_SENT_AT?
            "TENDER_KIND": tender.get_kind_display(),
        }

        if kind in ["transactioned_question_7d", "transactioned_question_7d_reminder"]:
            template_id = settings.MAILJET_TENDERS_AUTHOR_TRANSACTIONED_QUESTION_7D_TEMPLATE_ID
            user_sesame_query_string = sesame_get_query_string(tender.author)  # TODO: sesame scope parameter
            answer_url_with_sesame_token = (
                f"https://{get_domain_url()}"
                + reverse("tenders:detail-survey-transactioned", args=[tender.slug])
                + user_sesame_query_string
            )
            variables["ANSWER_YES_URL"] = f"{answer_url_with_sesame_token}&answer={constants.YES}"
            variables["ANSWER_NO_URL"] = f"{answer_url_with_sesame_token}&answer={constants.NO}"
            variables["ANSWER_DONT_KNOW_URL"] = f"{answer_url_with_sesame_token}&answer={constants.DONT_KNOW}"
            # add timestamp
            tender.survey_transactioned_send_date = timezone.now()
        else:
            template_id = settings.MAILJET_TENDERS_AUTHOR_FEEDBACK_30D_TEMPLATE_ID

        api_mailjet.send_transactional_email_with_template(
            template_id=template_id,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            variables=variables,
            subject=email_subject,
        )

        # log email
        log_item = {
            "action": f"email_{kind}_sent",
            "email_to": recipient_email,
            "email_subject": email_subject,
            # "email_body": email_body,
            "email_timestamp": timezone.now().isoformat(),
        }
        tender.logs.append(log_item)
        tender.save()


def send_tenders_siaes_survey(tender: Tender, kind="transactioned_question_7d"):
    tendersiae_qs = TenderSiae.objects.filter(tender=tender)

    if kind == "transactioned_question_7d":
        # siae must be interested
        tendersiae_qs = tendersiae_qs.filter(detail_contact_click_date__isnull=False)
        # siae must not have received the survey yet
        tendersiae_qs = tendersiae_qs.filter(survey_transactioned_answer=None, survey_transactioned_send_date=None)

        for tendersiae in tendersiae_qs:
            send_tenders_siae_survey(tendersiae, kind=kind)

        # log email batch
        log_item = {
            "action": f"email_siaes_{kind}_sent",
            "siae_count": tendersiae_qs.count(),
            "email_timestamp": timezone.now().isoformat(),
        }
        tender.logs.append(log_item)
        tender.save()


def send_tenders_siae_survey(tendersiae: TenderSiae, kind="transactioned_question_7d"):
    email_subject = f"Suite à notre demande de {tendersiae.tender.title}"
    template_id = settings.MAILJET_TENDERS_SIAE_TRANSACTIONED_QUESTION_7D_TEMPLATE_ID

    for user in tendersiae.siae.users.all():
        recipient_list = whitelist_recipient_list([user.email])
        if recipient_list:
            recipient_email = recipient_list[0] if recipient_list else ""
            recipient_name = user.full_name

            variables = {
                "TENDER_AUTHOR_FULL_NAME": tendersiae.tender.contact_full_name,
                "tender_author_company": tendersiae.tender.author.company_name,
                "TENDER_TITLE": tendersiae.tender.title,
                "TENDER_VALIDATE_AT": tendersiae.tender.first_sent_at.strftime("%d %B %Y"),  # TODO: TENDER_SENT_AT?
                "TENDER_KIND": tendersiae.tender.get_kind_display(),
            }

            user_sesame_query_string = sesame_get_query_string(user)  # TODO: sesame scope parameter
            answer_url_with_sesame_token = (
                f"https://{get_domain_url()}"
                + reverse(
                    "tenders:detail-siae-survey-transactioned", args=[tendersiae.tender.slug, tendersiae.siae.slug]
                )
                + user_sesame_query_string
            )
            variables["ANSWER_YES_URL"] = answer_url_with_sesame_token + "&answer=True"
            variables["ANSWER_NO_URL"] = answer_url_with_sesame_token + "&answer=False"

            api_mailjet.send_transactional_email_with_template(
                template_id=template_id,
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                variables=variables,
                subject=email_subject,
            )

            # update tendersiae
            tendersiae.survey_transactioned_send_date = timezone.now()
            # log email
            log_item = {
                "action": f"email_{kind}_sent",
                "email_to": recipient_email,
                "email_subject": email_subject,
                # "email_body": email_body,
                "email_timestamp": timezone.now().isoformat(),
            }
            tendersiae.logs.append(log_item)
            tendersiae.save()


def notify_admin_siae_wants_cocontracting(tender: Tender, siae: Siae):
    email_subject = f"Marché de l'inclusion : la structure {siae.name} souhaite répondre en co-traitance"
    tender_admin_url = get_object_admin_url(tender)
    email_body = render_to_string(
        "tenders/cocontracting_notification_email_admin_body.txt",
        {
            "tender_title": tender.title,
            "tender_kind": tender.get_kind_display(),
            "tender_admin_url": tender_admin_url,
            "siae_name": siae.name,
            "siae_contact_email": siae.contact_email,
            "siae_siret": siae.siret,
        },
    )
    send_mail_async(
        email_subject=email_subject,
        email_body=email_body,
        recipient_list=[settings.NOTIFY_EMAIL],
    )

    if settings.BITOUBI_ENV == "prod":
        api_slack.send_message_to_channel(text=email_body, service_id=settings.SLACK_WEBHOOK_C4_TENDER_CHANNEL)


def send_super_siaes_email_to_author(tender: Tender, top_siaes: list[Siae]):
    recipient_list = whitelist_recipient_list([tender.author.email])
    if recipient_list:
        recipient_email = recipient_list[0] if recipient_list else ""
        recipient_name = tender.author.full_name

        # Use transaction parameters of Brevo with loop for siaes, documentation :
        # https://help.brevo.com/hc/en-us/articles/4402386448530-Customize-your-emails-using-transactional-parameters
        variables = {
            "author_name": recipient_name,
            "tender_title": tender.title,
            "tender_kind": tender.get_kind_display().lower(),
            "siaes_count": len(top_siaes),
            "siaes": [],
            "tender_siae_interested_list_url": f"{get_object_share_url(tender)}/prestataires",
        }
        for siae in top_siaes:
            variables["siaes"].append(
                {
                    "name": siae.name_display,
                    "kind": siae.get_kind_display(),
                    "contact_name": siae.contact_full_name,
                    "contact_phone": siae.contact_phone_display,
                    "contact_email": siae.contact_email,
                }
            )

        api_brevo.send_transactional_email_with_template(
            template_id=settings.BREVO_TENDERS_AUTHOR_SUPER_SIAES_TEMPLATE_ID,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            variables=variables,
        )

        # log email
        log_item = {
            "action": "email_super_siaes",
            "email_to": recipient_email,
            "email_timestamp": timezone.now().isoformat(),
            "email_variables": variables,
        }
        tender.logs.append(log_item)
        tender.save()
