from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Index
from src.api.db import Base
from sqlalchemy.orm import relationship
import enum
import datetime

class UserRole(enum.Enum):
    CUSTOMER = "CUSTOMER"
    STAFF = "STAFF"
    ADMIN = "ADMIN"

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=True)
    password = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_registered = Column(Boolean, default=False)

    __table_args__ = (
        Index(
            "ix_users_email_unique_account",
            "email",
            unique=True,
            postgresql_where=(role.isnot(None))
        ),
        Index(
            "ix_users_phone_unique_account",
            "phone",
            unique=True,
            postgresql_where=(role.isnot(None))
        ),
    )

    bookings = relationship("Booking", back_populates="user")