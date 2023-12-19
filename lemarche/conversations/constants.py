ATTRIBUTES_TO_SAVE_FOR_INBOUND = ["From", "To", "CC", "ReplyTo", "SentAtDate", "Attachments"]

SOURCE_MAILJET = "MAILJET"
SOURCE_BREVO = "BREVO"

SOURCE_CHOICES = (
    (SOURCE_MAILJET, "Mailjet"),
    (SOURCE_BREVO, "Brevo"),
)
