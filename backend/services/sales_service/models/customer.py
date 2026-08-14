from sqlalchemy import Column, Integer, String
from backend.database import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # walk-in
    contact = Column(String)