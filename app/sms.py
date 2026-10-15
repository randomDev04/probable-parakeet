import logging

from app.config import settings

logger = logging.getLogger("uvivorm.error")

def send_otp_sms(phone: str, code: str) -> None:
    if settings.envirement == "development":
        # Read it with: docker compose logs -f api
        logger.warning("DEV MODE - OTP for %s is %s", phone, code)
        return

    # Production: call SMS provider (MSG91)
    raise NotImplementedError("Configure an SMS provider in app/sms.py")