from pydantic import BaseModel, constr

class AddCountryModel(BaseModel):
    name: str = constr(min_length=3, max_length=50)
    flag: str = constr(min_length=3, max_length=128)
    cc2Code: str = constr(min_length=2, max_length=2)