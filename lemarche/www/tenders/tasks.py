from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from lemarche.siaes.models import Siae
from lemarche.tenders.models import PartnerShareTender, Tender, TenderSiae
from lemarche.utils.apis import api_mailjet, api_slack
from lemarche.utils.emails import EMAIL_SUBJECT_PREFIX, send_mail_async, whitelist_recipient_list
from lemarche.utils.urls import get_admin_url_object, get_share_url_object


# @task()
def send_tender_emails_to_siaes(tender: Tender):
    """
    All corresponding Siae will be contacted
    """
    email_subject = (
        f"{EMAIL_SUBJECT_PREFIX}{tender.get_kind_display()} : {tender.title} ({tender.author.company_name})"
    )
    siaes = tender.siaes.all()
    for siae in siaes:
        send_tender_email_to_siae(email_subject, tender, siae)

    tender.tendersiae_set.update(email_send_date=timezone.now(), updated_at=timezone.now())

    # log email batch
    log_item = {
        "action": "email_siaes_matched",
        "email_subject": email_subject,
        "email_count": siaes.count(),
        "email_timestamp": timezone.now().isoformat(),
    }
    tender.logs.append(log_item)
    tender.save()


def send_tender_emails_to_partners(tender: Tender):
    """
    All corresponding partners (PartnerShareTender) will be contacted
    """
    partners = PartnerShareTender.objects.filter_by_tender(tender)
    email_subject = (
        f"{EMAIL_SUBJECT_PREFIX}{tender.get_kind_display()} : {tender.title} ({tender.author.company_name})"
    )
    for partner in partners:
        send_tender_email_to_partner(email_subject, tender, partner)

    # log email batch
    log_item = {
        "action": "email_partners_matched",
        "email_subject": email_subject,
        "email_count": partners.count(),
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
            "TENDER_PERIMETERS": tender.location.name_display,
            "TENDER_URL": get_share_url_object(tender),
        }

        api_mailjet.send_transactional_email_many_recipient_with_template(
            template_id=settings.MAILJET_TENDERS_PRESENTATION_TEMPLATE_PARTNERS_ID,
            subject=email_subject,
            recipient_email_list=recipient_list,
            variables=variables,
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


def send_tenders_author_feedback_30_days(tender: Tender):
    email_subject = EMAIL_SUBJECT_PREFIX + "Concernant votre dépôt de besoin sur le marché de l'inclusion"
    recipient_list = whitelist_recipient_list([tender.author.email])
    if recipient_list:
        recipient_email = recipient_list[0] if recipient_list else ""
        recipient_name = tender.author.full_name

        variables = {
            "TENDER_AUTHOR_FIRST_NAME": tender.author.first_name,
            "TENDER_TITLE": tender.title,
            "TENDER_VALIDATE_AT": tender.validated_at.strftime("%d %B %Y"),
            "TENDER_KIND": tender.get_kind_display(),
        }

        api_mailjet.send_transactional_email_with_template(
            template_id=settings.MAILJET_TENDERS_AUTHOR_FEEDBACK_30D_TEMPLATE_ID,
            subject=email_subject,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            variables=variables,
        )

        # log email
        log_item = {
            "action": "email_feedback_30d_sent",
            "email_to": recipient_email,
            "email_subject": email_subject,
            # "email_body": email_body,
            "email_timestamp": timezone.now().isoformat(),
        }
        tender.logs.append(log_item)
        tender.save()


# @task()
def send_tender_email_to_siae(email_subject: str, tender: Tender, siae: Siae):
    recipient_list = whitelist_recipient_list([siae.contact_email])
    if recipient_list:
        recipient_email = recipient_list[0] if recipient_list else ""
        recipient_name = siae.contact_full_name

        variables = {
            "SIAE_CONTACT_FIRST_NAME": siae.contact_first_name,
            "SIAE_SECTORS": siae.sectors_list_string(),
            "SIAE_PERIMETER": siae.geo_range_pretty_display,
            "TENDER_TITLE": tender.title,
            "TENDER_AUTHOR_COMPANY": tender.author.company_name,
            "TENDER_KIND": tender.get_kind_display(),
            "TENDER_SECTORS": tender.sectors_list_string(),
            "TENDER_PERIMETERS": tender.location.name_display,
            "TENDER_URL": get_share_url_object(tender),
        }

        api_mailjet.send_transactional_email_with_template(
            template_id=settings.MAILJET_TENDERS_PRESENTATION_TEMPLATE_ID,
            subject=email_subject,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            variables=variables,
        )


def send_confirmation_published_email_to_author(tender: Tender, nb_matched_siaes: int):
    """Send email to the author when the tender is published to the siaes

    Args:
        tender (Tender): Tender published
        nb_matched (int): number of siaes match
    """
    email_subject = f"{EMAIL_SUBJECT_PREFIX}Votre {tender.get_kind_display().lower()} a été publié !"
    recipient_list = whitelist_recipient_list([tender.author.email])
    if recipient_list:
        recipient_email = recipient_list[0] if recipient_list else ""
        recipient_name = tender.author.full_name

        variables = {
            "TENDER_AUTHOR_FIRST_NAME": tender.author.first_name,
            "TENDER_TITLE": tender.title,
            "TENDER_KIND": tender.get_kind_display(),
            "TENDER_NB_MATCH": nb_matched_siaes,
            "TENDER_URL": get_share_url_object(tender),
        }

        api_mailjet.send_transactional_email_with_template(
            template_id=settings.MAILJET_TENDERS_AUTHOR_CONFIRMATION_PUBLISHED_TEMPLATE_ID,
            subject=email_subject,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            variables=variables,
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
            email_subject = EMAIL_SUBJECT_PREFIX + "Une première structure intéressée !"
            template_id = settings.MAILJET_TENDERS_SIAE_INTERESTED_1_TEMPLATE_ID
        elif tender_siae_detail_contact_click_count == 2:
            should_send_email = True
            email_subject = EMAIL_SUBJECT_PREFIX + "Une deuxième structure intéressée !"
            template_id = settings.MAILJET_TENDERS_SIAE_INTERESTED_2_TEMPLATE_ID
        elif tender_siae_detail_contact_click_count == 5:
            should_send_email = True
            email_subject = EMAIL_SUBJECT_PREFIX + "Une cinquième structure intéressée !"
            template_id = settings.MAILJET_TENDERS_SIAE_INTERESTED_5_TEMPLATE_ID
        elif tender_siae_detail_contact_click_count % 5 == 0:
            should_send_email = True
            email_subject = EMAIL_SUBJECT_PREFIX + "5 nouvelles structures intéressées !"
            template_id = settings.MAILJET_TENDERS_SIAE_INTERESTED_5_MORE_TEMPLATE_ID
        else:
            pass

        if should_send_email:
            recipient_list = whitelist_recipient_list([tender.author.email])  # tender.contact_email ?
            if recipient_list:
                recipient_email = recipient_list[0] if recipient_list else ""
                recipient_name = tender.author.full_name

                variables = {
                    "TENDER_AUTHOR_FIRST_NAME": tender.author.first_name,
                    "TENDER_TITLE": tender.title,
                    "TENDER_SIAE_INTERESTED_LIST_URL": f"{get_share_url_object(tender)}/structures-interessees",  # noqa
                }

                api_mailjet.send_transactional_email_with_template(
                    template_id=template_id,
                    subject=email_subject,
                    recipient_email=recipient_email,
                    recipient_name=recipient_name,
                    variables=variables,
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
    tender_admin_url = get_admin_url_object(tender)
    email_body = render_to_string(
        "tenders/create_notification_email_admin_body.txt",
        {
            "tender_id": tender.id,
            "tender_title": tender.title,
            "tender_kind": tender.get_kind_display(),
            "tender_author_full_name": tender.contact_full_name,
            "tender_author_company": tender.author.company_name,
            "tender_admin_url": tender_admin_url,
        },
    )
    send_mail_async(
        email_subject=email_subject,
        email_body=email_body,
        recipient_list=[settings.NOTIFY_EMAIL],
    )

    api_slack.send_message_to_channel(text=email_body, service_id=settings.SLACK_WEBHOOK_C4_SUPPORT_CHANNEL)
