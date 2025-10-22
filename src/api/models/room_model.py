from sqlalchemy import (Column, Integer, String, Enum, Float,
                        Text, Boolean, DECIMAL, JSON, ForeignKey,
                        PrimaryKeyConstraint)
from src.api.db import Base
from sqlalchemy.orm import relationship
import enum

class RoomType(enum.Enum):
    ECONOMY = "ECONOMY"
    STANDARD = "STANDARD"
    DELUXE = "DELUXE"

class RoomStatus(enum.Enum):
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    MAINTENANCE = "MAINTENANCE"

class Room(Base):
    __tablename__ = "rooms"

    room_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    room_number = Column(String, nullable=False, unique=True)
    room_type = Column(Enum(RoomType), nullable=False)
    max_guest = Column(Integer, nullable=False)
    base_price = Column(DECIMAL(10, 2), nullable=False)
    status = Column(Enum(RoomStatus), nullable=False, default=RoomStatus.AVAILABLE)
    description = Column(Text, nullable=True)
    floor = Column(Integer, nullable=False)
    size_sqm = Column(Float, nullable=True)
    main_photo_url = Column(String, nullable=True)
    photo_urls = Column(JSON, nullable=True)

    # bookings = relationship("Booking", back_populates="room")
    # amenities = relationship("RoomAmenity", back_populates="room")


class Amenity(Base):
    __tablename__ = "amenities"

    amenity_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    amenity_name = Column(String, nullable=False)
    icon_url = Column(String, nullable=True)

    # rooms = relationship("RoomAmenity", back_populates="amenity")


class RoomAmenity(Base):
    __tablename__ = "room_amenities"

    room_id = Column(Integer, ForeignKey("rooms.room_id"), nullable=False)
    amenity_id = Column(Integer, ForeignKey("amenities.amenity_id"), nullable=False)
    quantity = Column(Integer, default=1)
    is_available = Column(Boolean, default=True)

    __table_args__ = (
        PrimaryKeyConstraint("room_id", "amenity_id", name="pk_room_amenity"),
    )

    # room = relationship("Room", back_populates="amenities")
    # amenity = relationship("Amenity", back_populates="rooms")