from src.api.models.user_model import User, UserRole
import datetime
from sqlalchemy.exc import SQLAlchemyError, IntegrityError


def get_all_users(session):
    try:
        return session.query(User).all()
    except SQLAlchemyError as e:
        print(f"Database error fetching users: {e}")
        raise


def create_user(session, data, via_booking=False):
    try:
        email = data.get("email")
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        phone = data.get("phone")
        password = data.get("password") if not via_booking else None
        role_str = data.get("role")

        role = None
        if role_str:
            if isinstance(role_str, dict):
                role_str = role_str.get("value")
            try:
                role = UserRole[role_str]
            except KeyError:
                raise ValueError(f"Invalid role: {role_str}")

        if not via_booking:
            existing_user = session.query(User).filter_by(email=email).first()
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

        session.add(new_user)
        session.commit()
        return new_user

    except IntegrityError as e:
        session.rollback()
        raise ValueError("User with this email or phone already exists")
    except SQLAlchemyError as e:
        session.rollback()
        raise Exception(f"Database error creating user: {e}")
    except Exception as e:
        session.rollback()
        raise e


def get_user_by_id(session, user_id):
    try:
        return session.query(User).get(user_id)
    except SQLAlchemyError as e:
        print(f"Database error fetching user {user_id}: {e}")
        return None


def get_user_by_email(session, email):
    try:
        return session.query(User).filter_by(email=email).first()
    except SQLAlchemyError as e:
        print(f"Database error fetching user by email {email}: {e}")
        return None


def update_user_partial(session, user_id, data):
    user = session.query(User).get(user_id)
    if not user:
        return None

    try:
        for key, value in data.items():
            if key in ["user_id", "id", "created_at", "is_registered"]:
                continue
            
            if key == "password":
                if value and value.strip():
                    user.set_password(value)
            elif key == "role":
                if value:
                    role_value = value
                    if isinstance(value, dict):
                        role_value = value.get("value", value.get("role"))
                    try:
                        user.role = UserRole[role_value]
                    except (KeyError, TypeError) as e:
                        print(f"Invalid role value: {role_value}, error: {e}")
                        raise ValueError(f"Invalid role: {role_value}")
            elif hasattr(user, key):
                setattr(user, key, value)

        session.commit()
        session.refresh(user) 
        return user
        
    except IntegrityError as e:
        session.rollback()
        print(f"IntegrityError updating user {user_id}: {e}")
        raise ValueError("User with this email or phone already exists")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"SQLAlchemyError updating user {user_id}: {e}")
        raise Exception(f"Database error updating user: {e}")
    except Exception as e:
        session.rollback()
        print(f"Unexpected error updating user {user_id}: {e}")
        import traceback
        traceback.print_exc()
        raise e


def update_user_full(session, user_id, data):
    user = session.query(User).get(user_id)
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
        if isinstance(role_str, dict):
            role_str = role_str.get("value", role_str.get("role"))
        try:
            user.role = UserRole[role_str]
        except KeyError:
            raise ValueError(f"Invalid role: {role_str}")

        if data.get('password'):
            password = data.get('password')
            if password and password.strip():
                user.set_password(password)

        session.commit()
        session.refresh(user)
        return user
        
    except IntegrityError as e:
        session.rollback()
        print(f"IntegrityError in full update user {user_id}: {e}")
        raise ValueError("User with this email or phone already exists")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"SQLAlchemyError in full update user {user_id}: {e}")
        raise Exception(f"Database error updating user: {e}")
    except Exception as e:
        session.rollback()
        print(f"Unexpected error in full update user {user_id}: {e}")
        import traceback
        traceback.print_exc()
        raise e


def delete_user(session, user_id):
    user = session.query(User).get(user_id)
    if not user:
        return False

    try:
        session.delete(user)
        session.commit()
        return True
    except SQLAlchemyError as e:
        session.rollback()
        print(f"SQLAlchemyError deleting user {user_id}: {e}")
        raise Exception(f"Database error deleting user: {e}")
    except Exception as e:
        session.rollback()
        print(f"Unexpected error deleting user {user_id}: {e}")
        raise e