from src.api.db import db
from src.api.models.user_model import User, UserRole
import datetime
from sqlalchemy.exc import SQLAlchemyError, IntegrityError


def get_all_users():
    try:
        return db.query(User).all()
    except SQLAlchemyError as e:
        print(f"Database error fetching users: {e}")


def create_user(data, via_booking=False):
    try:
        email = data.get("email")
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        phone = data.get("phone")
        password = data.get("password") if not via_booking else None
        role_str = data.get("role")

        role = None
        if role_str:
            try:
                role = UserRole[role_str]
            except KeyError:
                raise ValueError(f"Invalid role: {role_str}")

        if not via_booking:
            existing_user = db.query(User).filter_by(email=email).first()
            if existing_user and existing_user.is_registered:
                raise ValueError("User with this email already exists")

        new_user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role=role,
            is_registered=not via_booking,
            created_at=datetime.datetime.utcnow()
        )

        if password:
            new_user.set_password(password)

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    except IntegrityError as e:
        db.rollback()
        raise ValueError("User with this email or phone already exists")
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Database error creating user: {e}")
    except Exception as e:
        db.rollback()
        raise e


def get_user_by_id(user_id):
    try:
        return db.query(User).get(user_id)
    except SQLAlchemyError as e:
        print(f"Database error fetching user {user_id}: {e}")
        return None


def update_user_partial(user_id, data):
    user = db.query(User).get(user_id)
    if not user:
        return None

    try:
        for key, value in data.items():
            if key == "password" and value:
                user.set_password(value)
            elif key == "role" and value:
                try:
                    setattr(user, key, UserRole[value])
                except KeyError:
                    raise ValueError(f"Invalid role: {value}")
            elif hasattr(user, key) and key not in ["user_id", "id"]:
                setattr(user, key, value)

        db.commit()
        return user
    except IntegrityError as e:
        db.rollback()
        raise ValueError("User with this email or phone already exists")
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Database error updating user: {e}")
    except Exception as e:
        db.rollback()
        raise e


def update_user_full(user_id, data):
    user = db.query(User).get(user_id)
    if not user:
        return None

    required_fields = ['email', 'first_name', 'last_name', 'phone', 'role']
    if not all(field in data for field in required_fields):
        raise ValueError("Missing required fields for full update")

    try:
        user.email = data.get('email')
        user.first_name = data.get('first_name')
        user.last_name = data.get('last_name')
        user.phone = data.get('phone')

        role_str = data.get('role')
        try:
            user.role = UserRole[role_str]
        except KeyError:
            raise ValueError(f"Invalid role: {role_str}")

        if data.get('password'):
            user.set_password(data.get('password'))

        db.commit()
        return user
    except IntegrityError as e:
        db.rollback()
        raise ValueError("User with this email or phone already exists")
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Database error updating user: {e}")
    except Exception as e:
        db.rollback()
        raise e


def delete_user(user_id):
    user = db.query(User).get(user_id)
    if not user:
        return False

    try:
        db.delete(user)
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Database error deleting user: {e}")
    except Exception as e:
        db.rollback()
        raise e