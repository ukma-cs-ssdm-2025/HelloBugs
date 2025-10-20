# Debugging Log
(журнал налагодження для двох кейсів (в частині авторизації):)
---

## Кейс 1: `get_current_user()` падає, якщо роль — рядок
### Симптом
під час перегляду ендпоїнта `GET /api/v1/auth/me` виявлено потенційний збій: виклик `g.current_user.role.value` може спричинити `AttributeError`, якщо `role` вже є рядком, а не переліком `UserRole`
- Файл: `src/api/routes/auth_routes.py`
- Функція: `get_current_user()`
- Рядки (до виправлення):
```python
return jsonify({
    'id': g.current_user.user_id,
    'email': g.current_user.email,
    'first_name': g.current_user.first_name,
    'last_name': g.current_user.last_name,
    'role': g.current_user.role.value,
    'is_admin': g.current_user.role == UserRole.ADMIN
})
```
### Коренева причина
роль користувача в системі може бути enum `UserRole` (тип який має `.value`) або звичайний рядок (наприклад, якщо запис у БД/серіалізація зберегла значення ролі як текст). Якщо роль збережена як текст, `.value` не існує - і програма падає з промилкою. Тобто код без перевірки викликав `.value`, що ламалося б для рядків. Декоратори в `src/api/auth.py` вже враховують обидва варіанти, а `get_current_user()` — ні
### Виправлення
виправлено перевірку типу ролі перед використанням `.value` щоб уникнути помилки.
Бо роль потрібно було привести до одного формату перед формуванням відповіді,за таким самим принципом, який вже використовується в декораторах 
- Файл: `src/api/routes/auth_routes.py`
- Функція: `get_current_user()`
- Зміни:
```python
role_value = g.current_user.role.value if hasattr(g.current_user.role, 'value') else g.current_user.role
is_admin = (role_value == 'ADMIN')
return jsonify({
    'id': g.current_user.user_id,
    'email': g.current_user.email,
    'first_name': g.current_user.first_name,
    'last_name': g.current_user.last_name,
    'role': role_value,
    'is_admin': is_admin
})
```
Це унеможливлює падіння, якщо роль задана рядком, та узгоджує логіку з декораторами в `src/api/auth.py`
### Перевірка (кроки і команди)
- Перевірка сценарію з enum-роллю:
  ```bash
  pytest tests/test_auth_routes.py::test_me_authorized -q
  ```
- Перевірка сценарію з роллю-рядком (доданий тест):
  ```bash
  pytest tests/test_auth_routes.py::test_me_authorized_role_as_string -q
  ```
- Очікування: тести проходять
### Чому це корисно
- Уникаємо падінь, якщо роль у базі і в сесії збережена текстом
- поведінка ендпоїнта стала стабільною та передбачуваною
- узгоджено логіку з декораторами у auth.py
### Уроки
- **Уніфікація даних:** якщо поле може бути в різних типах (Enum або текст), його треба перевіряти перед викристанням та нормалізувати або явно уніфікувати на межі модуля.
- **Повторне використання патернів:** копіюємо перевірки з уже стабільних місць (декораторів).
- **Тести негативних сценаріїв:** додаємо кейс із рядком, щоб захиститися від регресій
---

## Кейс 2: `register()` повертає 415 без JSON
### Симптом
Запит `POST /api/v1/auth/register` без JSON тіла повертав технічну помилку `415 Unsupported Media Type` ще до того як запустився наш код (не вистачає `Content-Type: application/json`). Тест очікував дружній 400 про відсутні поля (Ми хотіли, щоб у такій ситуації API повертав 400 Bad Request з поясненням “бракує даних”.)
- Файл: `src/api/routes/auth_routes.py`
- Функція: `register()`
### Коренева причина
`request.get_json()` без `Content-Type: application/json` тригерив стандартний 415 від Flask. Ми не могли повернути свій 400. Через це наша перевірка полів не виконувалась взагалі
### Виправлення
- Замінили `request.get_json()` на `request.get_json(silent=True)` — тепер не кидає 415, а повертає `None`.
- додали перевірку: `if not data or not all(field in data for field in ["email", "password"]):return jsonify({"error": "Missing fields"}), 400`
- додано тест: `tests/test_auth_routes.py::test_register_no_payload`
### Перевірка (кроки і команди)
- перевірити обидва сценарії реєстрації:
- сценарій з неповними даними:
  ```bash
  pytest tests/test_auth_routes.py::test_register_missing_fields -q
  ```
- сценарій без JSON:
    ```bash
  pytest tests/test_auth_routes.py::test_register_no_payload -q
  ```
- очікування: обидва тести повернуть — 400. Пас тесту означає, що ендпоїнт повернув очікуваний код (400) і перевірка assert resp.status_code == 400 пройшла
### Чому це корисно
- api дає зрозумілу й дружню відповідь для користувачів 
- уникнули технічної помилки 415
- полегшує клієнтам/тестам розуміння, що саме не так (бракує полів)
- тести стали стабільнішими, бо поведінка передбачувана