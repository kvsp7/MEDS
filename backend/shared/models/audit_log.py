from sqlalchemy import Column, Integer, String, DateTime
from backend.database import Base
import datetime

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer)

    action = Column(String)        # CREATE, UPDATE, DELETE, LOGIN, SALE
    entity = Column(String)        # Medicine, User, Batch, Sale
    entity_id = Column(Integer)    # ID of that entity

    description = Column(String)   # detailed message

    timestamp = Column(DateTime, default=datetime.datetime.utcnow)