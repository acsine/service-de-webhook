from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .handlers import Countries

from .schemas import AddCountryModel


router = APIRouter(prefix="/country")

router.get("/all")(Countries.get_countries)
router.post("/add")(Countries.add_country)
