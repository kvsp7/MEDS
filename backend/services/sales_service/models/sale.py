from sqlalchemy import Column, Integer, Float, DateTime
from backend.database import Base
import datetime

class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    medicine_id = Column(Integer)
    quantity = Column(Integer)
    total_price = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    outlet_id = Column(Integer)
    customer_id = Column(Integer, nullable=True)