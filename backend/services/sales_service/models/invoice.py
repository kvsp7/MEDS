from sqlalchemy import Column, Integer, String, DateTime
from backend.database import Base
import datetime

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String, unique=True, nullable=False)
    sale_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)