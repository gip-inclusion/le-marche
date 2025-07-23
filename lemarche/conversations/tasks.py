from huey.contrib.djhuey import task

from lemarche.utils.apis import api_brevo


@task()
def send_transactional_email(args):
    """Send a transactional email using Brevo API."""

    brevo_email_client = api_brevo.BrevoTransactionalEmailApiClient()
    brevo_email_client.send_transactional_email_with_template(**args)
