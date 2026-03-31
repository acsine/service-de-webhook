import httpx
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.responses import ReplyJSON
from app.common.models import Country
from app.common.i18n import get_locale_from_request, get_translator, t
from app.config.database import Database
from .schemas import AddCountryModel
import http.client


class Countries:

    @staticmethod
    async def get_countries(locale: str = Depends(get_locale_from_request)):
        url = "https://restcountries.com/v3.1/all"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)

        if response.status_code != http.client.OK:
            message = t("messages.countries_failed", locale)
            response_data = ReplyJSON(
                status=response.status_code,
                code="COUNTRIES_FAILED",
                message=message
            )
            return response_data

        message = t("messages.countries_success", locale)
        response_data = ReplyJSON(
            status=http.client.OK,
            code="COUNTRIES_SUCCESS",
            message=message,
            data=response.json()
        )
        return response_data

    @staticmethod
    async def add_country(country: AddCountryModel, db: AsyncSession = Depends(Database.get_instance) , locale: str = Depends(get_locale_from_request)):
        country = Country(name=country.name, cc2_code=country.cc2Code, flag=country.flag)
        db.add(country)
        await db.commit()
        message = t("messages.country_added_success", locale)
        response_data = ReplyJSON(
            status=http.client.CREATED,
            code="COUNTRY_ADDED_SUCCESS",
            message=message,
        )
        return response_data
