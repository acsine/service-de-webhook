from pydantic import BaseModel
from typing import Optional


class ReplyJSON(BaseModel):
    status: int
    code: str
    error: Optional[bool] = False
    message: str
    data: Optional[dict] = None

    def toJson(self):
        return self.model_dump()
