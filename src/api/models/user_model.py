from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Index, event
from src.api.db import Base, db
from sqlalchemy.orm import relationship
import enum
import datetime
# import bcrypt
import os
from werkzeug.security import generate_password_hash, check_password_hash


class UserRole(enum.Enum):
    GUEST = "GUEST"           # Гість
    STAFF = "STAFF"           # Працівник
    ADMIN = "ADMIN"          # Адміністратор

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

    # bookings = relationship("Booking", back_populates="user")
    # reviews = relationship("Review", back_populates="user")
    
    def set_password(self, password):
        """Create hashed password."""
        self.password = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password, password)
    
    def generate_auth_token(self):
        """Generate JWT token for the user."""
        from ..auth import create_token
        return create_token(self.user_id, self.role == UserRole.ADMIN)
    
    @staticmethod
    def verify_auth_token(token):
        """Verify the authentication token."""
        from ..auth import SECRET_KEY
        from jwt import decode, InvalidTokenError
        try:
            data = decode(token, SECRET_KEY, algorithms=['HS256'])
            return db.query(User).get(data['user_id'])
        except InvalidTokenError:
            return None
    
    @property
    def is_admin(self):
        """Check if user has admin role."""
        return self.role == UserRole.ADMIN
    
    @property
    def is_staff(self):
        """Check if user has staff role."""
        return self.role in [UserRole.STAFF, UserRole.ADMIN]


# @event.listens_for(User.__table__, 'after_create')
# def create_admin_user(*args, **kwargs):
#     """Create admin user if not exists."""
#     admin_email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
#     admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
#     
#     admin = db.query(User).filter_by(email=admin_email).first()
#     if not admin:
#         admin = User(
#             email=admin_email,
#             first_name='Admin',
#             last_name='User',
#             phone='+1234567890',
#             role=UserRole.ADMIN,
#             is_registered=True
#         )
#         admin.set_password(admin_password)
#         db.add(admin)
#         db.commit()
#         print('Admin user created successfully')