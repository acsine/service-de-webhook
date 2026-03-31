from sqlalchemy import Column, Integer, String
from app.config.database import Base  # adjust import if needed

class Country(Base):
    __tablename__ = "country"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    cc2_code = Column(String(2), nullable=False)
    flag = Column(String(128), nullable=True)

    def __repr__(self):
        return f"<Country(name='{self.name}')>"