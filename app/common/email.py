import httpx
import logging
from typing import Optional, Dict, Any
from app.config.settings import settings

logger = logging.getLogger(__name__)

async def send_notification_email(
    to_email: str,
    subject: str,
    message: str,
    email_title: Optional[str] = None,
    button_text: Optional[str] = None,
    button_url: Optional[str] = "https://google.com",
    template_data: Optional[Dict[str, Any]] = None,
    use_template: bool = True
) -> bool:
    """
    Sends an email using the external notification service.
    """
    payload = {
        "to_email": to_email,
        "subject": subject,
        "message": message,
        "from_email": settings.DEFAULT_FROM_EMAIL,
        "from_name": settings.DEFAULT_FROM_NAME,
        "email_title": email_title or subject,
        "button_text": button_text or "Click Here",
        "button_url": button_url,
        "use_template": str(use_template).lower(),
        "template_id": "",
        "template_data": str(template_data or {}),
        "priority": "",
        "additional_info": "",
        "cc": "",
        "bcc": "",
        "reply_to": ""
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                settings.NOTIFICATION_SERVICE_URL,
                data=payload,
                headers={"accept": "application/json"}
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == 202:
                logger.info(f"Email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"Failed to send email: {data}")
                return False
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred while sending email: {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"An error occurred while sending email: {e}")
            return False
