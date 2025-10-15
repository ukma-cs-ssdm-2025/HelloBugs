from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, ForeignKey
from src.api.db import Base
from sqlalchemy.orm import relationship
import enum
import datetime

class BookingStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class Booking(Base):
    __tablename__ = "bookings"

    booking_code = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.room_id"), nullable=False)
    check_in_date = Column(DateTime, nullable=False)
    check_out_date = Column(DateTime, nullable=False)
    special_requests = Column(Text, nullable=True)
    status = Column(Enum(BookingStatus), nullable=False, default=BookingStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # user = relationship("User", back_populates="bookings")
    # room = relationship("Room", back_populates="bookings")
