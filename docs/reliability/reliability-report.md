# Reliability Report

## 1. Огляд

Під час аналізу вихідного коду були виявлені 10 реальних ризиків ненадійності (fault → error → failure).  
**Основні типи:** відсутні таймаути, мовчазне ковтання помилок, слабка валідація, витік внутрішніх деталей, відсутні guard-clauses.  
Нижче наведено короткий опис кожної проблеми з класифікацією та рівнем критичності.

---

## 2. Таблиця знайдених проблем

| №   | Проблема                                                                         | Місце                                                            | Fault | Error                                                               | Failure                             | Severity |
|-----|----------------------------------------------------------------------------------|------------------------------------------------------------------|--------|---------------------------------------------------------------------|-------------------------------------|-----------|
| 1   | Відсутні health-check і таймаути БД                                              | src/api/db.py                                                    | create_engine(DATABASE_URL) без pool_pre_ping і таймаутів | Підключення зависають, пул блокується                               | Сервіс зависає, каскадні збої       | High |
| 2   | Ковтання помилок БД мовчки                                                       | src/api/services/user_service.py                                 | Помилка друкується через print і повертається None | Реальні помилки губляться                                           | Неможливо діагностувати збій        | High |
| 3   | Слабка валідація email у сервісі                                                 | src/api/services/user_service.py                                 | Відсутня перевірка email is None | Некоректні дані передаються далі                                    | IntegrityError або падіння          | Medium |
| 4   | Занадто широке except Exception                                                  | (загальні місця)                                                 | Уловлюються всі типи помилок | Приховуються логічні/системні баги                                  | Неможливо відлагодити               | High |
| 5   | Повернення 404 без логування                                                     | src/api/routes/users.py                                          | abort(404) без логу | Немає контексту чому не знайдено                                    | Ускладнений пошук дефектів          | Medium |
| 6   | Витік внутрішніх деталей у 500                                                   | (routes)                                                         | abort(500, message=str(e)) | Внутрішні помилки видно клієнту                                     | Витік конфіденційної інформації     | High |
| 7   | Відсутня перевірка JSON у вхідних запитах                                        | src/api/routes/auth_routes.py                                    | request.get_json() без silent=True | BadRequest при пошкодженому JSON                                    | 500 замість 400                     | Medium |
| 8   | Повернення None/False замість явної помилки                                      | src/api/services/room_service.py                                 | return False якщо не знайдено | Код інтерпретує як «успіх»                                          | Спотворення стану системи           | Medium |
| 9   | Виклики зовнішніх API без таймаутів                                              | src/api/services/payment_service.py                              | requests.post() без timeout | Потоки блокуються                                                   | Зависання системи, каскадні відмови | High |
| 10  | Небезпечний генератор booking-code                                               | src/api/services/booking_service.py                              | random.randint() + time.time() | Коди передбачувані                                                  | Підробка бронювання                 | High |
| 11* | Race condition при бронюванні                                                    | src/api/services/booking_service.py (check_room_availability)    | Відсутнє блокування FOR UPDATE на рівні рядка в базі даних | Обидві транзакції успішно роблять commit на той самий номер та дату | Подвійне бронювання                 | High |
| 12* | Порушення цілісності даних (email гостя), що призводить до блокування реєстрації | src/api/models/user_model.py, src/api/services/booking_service.py, src/api/routes/auth_routes.py | Унікальність email застосовується лише для користувачів із role IS NOT NULL, гість створюється з role=None | Система знаходить запис гостя і повертає помилку "User with this email already exists."                                                  | Гість не може зареєструватися, користувач не може створити акаунт із тим самим email                | High |
---

## 3. Перед/Після фрагменти коду, фікс проблем

### Проблема №1: Відсутні health-check і таймаути БД

**Before:**
```python
# db.py
engine = create_engine(DATABASE_URL)
```

**After:**
```python
# db.py
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    pool_recycle=3600,
        pool_size=5,
    max_overflow=10
    )
```

**Застосований патерн:** Connection Pool Management + Timeout Pattern

### Проблема №6: Витік внутрішніх деталей у 500-відповідях

**Before:**
```python
# bookings.py, users.py, rooms.py
except Exception as e:
    abort(500, message=str(e))
```

**After:**
```python
except Exception as e:
    abort(500, message="Internal server error")
```

**Застосований патерн:** Fail-Safe Error Handling

---

### Проблема №7: Відсутність перевірки JSON у вхідних запитах

**Before:**
```python
    data = request.get_json()
```

**After:**
```python
    data = request.get_json(silent=True)
    if data is None:
        abort(400, description='Invalid or missing JSON')
```

**Застосований патерн:** Input Validation + Fail-Fast

---

### Проблема №10: Небезпечний генератор booking-code

**Before:**
```python
def generate_booking_code():
    timestamp = int(time.time() * 1000) % 1000000
    random_part = random.randint(10000, 99999)
    return f"BK{timestamp}{random_part}"
```

**After:**
```python
import secrets

def generate_booking_code():
    timestamp = int(time.time() * 1000) % 1000000
    random_part = secrets.randbelow(90000) + 10000
    return f"BK{timestamp}{random_part}"
```

**Застосований патерн:** Secure Random Generation