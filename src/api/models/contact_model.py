from sqlalchemy import Column, Integer, String, Text
from src.api.db import Base


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    hotel_name = Column(String(255), nullable=False, default="Готель Хрещатик")
    address = Column(String(500), nullable=False, default="м. Київ, вул. Хрещатик, 1")
    phone = Column(String(50), nullable=False, default="+380956666666")
    email = Column(String(255), nullable=False, default="info@hotel.com")
    schedule = Column(String(255), nullable=False, default="Цілодобово")
    description = Column(Text, nullable=True)
