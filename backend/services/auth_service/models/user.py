from sqlalchemy import Column, Integer, String
from backend.database import Base
from sqlalchemy import ForeignKey


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    password = Column(String)
    role = Column(String)
    outlet_id = Column(Integer, ForeignKey("outlets.id"))