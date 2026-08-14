from sqlalchemy import Column, Integer, String
from backend.database import Base

class Outlet(Base):
    __tablename__ = "outlets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    location = Column(String)
    type = Column(String)  # store / warehouse