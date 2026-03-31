from pydantic import BaseModel, constr, conint, Field

class DescribeMeForm(BaseModel):
    firstName: str = Field(
        min_length=3, title="First name", max_length=50
    )
    lastName: str = Field(
        min_length=3, title="Last name", max_length=50
    )
    age: int = Field(gt=18, lt=60, title="Age")
