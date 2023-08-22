import logging

import requests
from django.conf import settings


logger = logging.getLogger(__name__)


def check_captcha_token(form_data):
    if not settings.MTCAPTCHA_PUBLIC_KEY:  # MTCAPTCHA is not activated
        return True
    try:
        token = form_data["mtcaptcha-verifiedtoken"]
    except KeyError:
        return False
    private_key = settings.MTCAPTCHA_PRIVATE_KEY
    if not private_key:
        logger.exception("MTCAPTCHA_PRIVATE_KEY has not been set.")
        return False
    mtcaptcha_url = f"https://service.mtcaptcha.com/mtcv1/api/checktoken?privatekey={private_key}&token={token}"
    try:
        response = requests.get(mtcaptcha_url)
        if response.status_code == 200:
            if response.json().get("success", False):
                return True
            else:
                # Log event only if the user is not responsible, see https://www.mtcaptcha.com/dev-guide
                if response.json()["fail_codes"] not in ["token-expired", "invalid-token"]:
                    logger.exception("Token failed : %s", response.json()["fail_codes"])
        else:
            logger.exception("Bad status code when calling Mtcaptcha API-> check-token: %s", response)
    except Exception as e:
        logger.exception("Exception when calling Mtcaptcha API-> check-token: %s", e)

    return False
