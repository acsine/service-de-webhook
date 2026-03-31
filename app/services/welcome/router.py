from fastapi import APIRouter
from .handlers import Welcome

from .schemas import DescribeMeForm

router = APIRouter(prefix="/welcome")

router.get("/")(Welcome.say_hello)
router.post("/describe-me")(Welcome.describe_me)
