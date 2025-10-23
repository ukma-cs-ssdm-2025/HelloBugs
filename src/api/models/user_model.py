from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Index, event
from src.api.db import Base, db
from sqlalchemy.orm import relationship
import enum
import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class UserRole(enum.Enum):
    GUEST = "GUEST"
    STAFF = "STAFF"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
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
    # reviews = relationship("Review", back_populates="user")

    def set_password(self, password):
        """Create hashed password."""
        self.password = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password, password)

    def generate_auth_token(self):
        """Generate JWT token for the user."""
        from src.api.auth import create_token  # Виправлений імпорт
        role_value = self.role.value if self.role else 'GUEST'
        return create_token(self.user_id, role=role_value, is_admin=self.role == UserRole.ADMIN)

    @staticmethod
    def verify_auth_token(token):
        """Verify the authentication token."""
        from src.api.auth import SECRET_KEY
        from jwt import decode, InvalidTokenError
        try:
            data = decode(token, SECRET_KEY, algorithms=['HS256'])
            return db.session.query(User).get(data['user_id'])
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

    @property
    def is_guest(self):
        """Check if user has guest role."""
        return self.role == UserRole.GUEST

    def get_role_name(self):
        """Get user role name in Ukrainian."""
        role_names = {
            UserRole.GUEST: 'Гість',
            UserRole.STAFF: 'Співробітник',
            UserRole.ADMIN: 'Адміністратор'
        }
        return role_names.get(self.role, 'Невідомо')

    def to_dict(self):
        """Convert user to dictionary for schema compatibility."""
        return {
            'id': self.user_id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'role': self.role.value if self.role else None,
            'created_at': self.created_at,
            'is_registered': self.is_registered
        }