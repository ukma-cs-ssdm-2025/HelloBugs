#!/usr/bin/env python3
"""
Скрипт для створення адміністратора
"""
from src.api.models.user_model import User, UserRole
from src.api.db import db

def create_admin():
    """Створює адміністратора в базі даних"""
    
    # Перевіряємо, чи існує адміністратор
    admin_email = 'admin@hotel.com'
    existing_admin = db.query(User).filter_by(email=admin_email).first()
    
    if existing_admin:
        print(f'❌ Адміністратор з email {admin_email} вже існує!')
        print(f'   ID: {existing_admin.user_id}')
        print(f'   Ім\'я: {existing_admin.first_name} {existing_admin.last_name}')
        print(f'   Роль: {existing_admin.role.value}')
        return
    
    # Створюємо нового адміністратора
    admin = User(
        email=admin_email,
        first_name='Адмін',
        last_name='Готелю',
        phone='+380999999999',  # Унікальний номер для адміна
        role=UserRole.ADMIN,
        is_registered=True
    )
    admin.set_password('admin123')  # Пароль за замовчуванням
    
    try:
        db.add(admin)
        db.commit()
        
        print('✅ Адміністратора успішно створено!')
        print(f'   Email: {admin_email}')
        print(f'   Пароль: admin123')
        print(f'   Ім\'я: {admin.first_name} {admin.last_name}')
        print(f'   Роль: {admin.role.value}')
        print('\n🔐 Тепер ви можете увійти в систему з цими даними!')
        
    except Exception as e:
        db.rollback()
        print(f'❌ Помилка при створенні адміністратора: {str(e)}')

if __name__ == '__main__':
    create_admin()
