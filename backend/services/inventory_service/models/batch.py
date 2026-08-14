from sqlalchemy import Column, Integer, String, Date, ForeignKey
from backend.database import Base

class Batch(Base):
    __tablename__ = "batches"

    id = Column(Integer, primary_key=True, index=True)
    medicine_id = Column(Integer, ForeignKey("medicines.id"))
    batch_number = Column(String, nullable=False)
    expiry_date = Column(Date, nullable=False)
    quantity = Column(Integer, nullable=False)
    outlet_id = Column(Integer, ForeignKey("outlets.id"))