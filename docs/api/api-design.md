# API Design Documentation

## Огляд архітектури
- **Базовий URL**: `http://localhost:3000/api/v1`
- **Стиль API**: RESTful
- **Автентифікація**: JWT Bearer tokens
- **Формат відповіді**: JSON
- **Стратегія версіонування**: Версіонування через шлях URL (/v1, /v2)

---

## Модель ресурсів

### Ресурс Users
- **Endpoint**: `/users`
- **Опис**: Керує обліковими записами користувачів (клієнтів, персоналу та адміністраторів).

- **Атрибути**:
  - `accountId` (integer): Унікальний ідентифікатор
  - `password` (string): Зашифрований пароль
  - `firstName` (string): Ім’я користувача
  - `lastName` (string): Прізвище користувача
  - `phone` (string): Контактний номер телефону
  - `role` (enum): CUSTOMER | STAFF | ADMIN
  - `createdAt` (datetime): Дата та час створення облікового запису

- **Зв’язки**:
  - Має багато `Bookings`
  - Має багато `Ratings`

---

### Ресурс Rooms
- **Endpoint**: `/rooms`
- **Опис**: Керує інформацією про кімнати, їхні типи та статус доступності.

- **Атрибути**:
  - `roomId` (integer): Унікальний ідентифікатор
  - `roomNumber` (string): Номер кімнати
  - `roomType` (enum): ECONOMY | STANDARD | DELUXE
  - `maxGuest` (integer): Максимальна кількість гостей
  - `basePrice` (decimal): Базова ціна за ніч
  - `status` (enum): AVAILABLE | OCCUPIED | MAINTENANCE
  - `description` (text): Детальний опис кімнати
  - `floor` (integer): Поверх
  - `sizeSqm` (decimal): Розмір кімнати у квадратних метрах
  - `mainPhotoUrl` (string): Посилання на головне фото
  - `photoUrls` (array[string]): Список додаткових фото

- **Зв’язки**:
  - Має багато `Bookings`
  - Має багато `Ratings`
  - Має багато `RoomAmenities`

---

### Ресурс Bookings
- **Endpoint**: `/bookings`
- **Опис**: Керує бронюваннями та життєвим циклом резервацій.

- **Атрибути**:
  - `bookingCode` (string): Унікальний код бронювання
  - `checkInDate` (date): Дата заїзду
  - `checkOutDate` (date): Дата виїзду
  - `specialRequests` (text): Додаткові побажання гостя (необов’язково)
  - `status` (enum): ACTIVE | COMPLETED | CANCELLED
  - `createdAt` (datetime): Дата створення бронювання
  - `updatedAt` (datetime): Останнє оновлення запису

- **Зв’язки**:
  - Належить до `Account` 
  - Належить до `Room`
  - Має одну необов’язкову `Rating`
  - Має багато `Notifications`
