import http.client
from fastapi import Depends
from app.common.responses import ReplyJSON
from .schemas import DescribeMeForm
from app.common.moment import moment
from app.common.i18n import get_locale_from_request, get_translator, t


class Welcome:
    @staticmethod
    def say_hello(locale: str = Depends(get_locale_from_request)):
        message = t("messages.welcome", locale)
        response_data = ReplyJSON(
            status=http.client.OK,
            code="WELCOME_SUCCESS",
            message=message
        )
        return response_data

    @staticmethod
    def describe_me(form: DescribeMeForm, locale: str = Depends(get_locale_from_request)):
        try:
            # form.model_validate()
            message = t("messages.describe_success", locale, firstName=form.firstName, lastName=form.lastName, age=form.age, hour=moment().format('HH:mm:ss'))
            response_data = ReplyJSON(
                status=http.client.OK,
                code="DESCRIBE_SUCCESS",
                message=message
            )
            return response_data
        except ValueError as e:
            response_data = ReplyJSON(
                status=http.client.OK,
                code="DESCRIBE_FAILED",
                error="Bad request",
                message=f"Failed to describe you: {e}",
            )
            return response_data
        except Exception as e:
            response_data = ReplyJSON(
                status=http.client.INTERNAL_SERVER_ERROR,
                code="DESCRIBE_FAILED",
                error="Internal server error",
                message=f"Failed to describe you: {e}",
            )
            return response_data
