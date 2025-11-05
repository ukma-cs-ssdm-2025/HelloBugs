# SonarCloud Refactoring Report  

## Аналіз SonarCloud
### Обрані метрики для покращення

### Обрані метрики для покращення

| Метрика | До рефакторингу | Після рефакторингу | Зміна |
|----------|------------------|--------------------|--------|
| Maintainability | A (369 issues) | A (212 issues)  | зменшилась к-сть Code Smells |
| Reliability | E (53 issues) | A (1 issues) | +кілька рівнів|
| Security | E (6 issues) | A (0 issues) | +кілька рівнів|
| Hotspots Reviewed | E (0.0%) | D (37.5%) | +1 рівень|


## Короткий опис використаних патернів рефакторингу
1. Remove Hardcoded Data / Introduce Constant  Прибрано захардкодені дані (паролі в тестах), замінено на динамічні змінні через secrets.token_urlsafe(). Це зменшило ризики безпеки й підвищило повторне використання коду.

2. Introduce Timezone Awareness / Replace Deprecated Function  Замінено datetime.utcnow() на datetime.now(timezone.utc) у кількох файлах.  Код став стабільним для різних часових поясів.

3. Improve Accessibility / Simplify Validation  В HTML-шаблоні admin_stats.html додано for="stats-apply" для кнопки та змінено валідацію дат. Це зробило інтерфейс доступним , покращило UX.

4. Simplify Loop / Rename Variable Прибрано небезпечне переприсвоєння змінної c у циклі. Цикл став безпечнішим і легшим для розуміння.

5. Replace Equality with Tolerant Comparison  У тестах порівняння == замінено на math.isclose(). Це прибрало можливі похибки при роботі з float-значеннями.

6. Extract Helper Functions / Early Return У booking_service.py винесено перевірки й підфункції в окремі хелпери. Знижено когнітивну складність і покращено структуру бізнес-логіки.

7. Use Static Methods and Properties over Globals  
   Замість глобальних змінних і функцій зроблено статичні методи та властивості у відповідних класах. Це підвищило інкапсуляцію та безпеку коду.

8. Avoid Non-Native Interactive Elements  
В HTML/JS-коді замінено нестандартні інтерактивні елементи на нативні (наприклад, кнопки). Це покращило доступність та сумісність з різними браузерами і пристроями.

9. Fix Variable Modification in Loop (end in isRangeFree)  
У bookings_create.js змінну end у циклі isRangeFree більше не модифікують всередині циклу. Це зробило цикл передбачуваним і уникнуло потенційних багів при перевірці дат.


## Скріншоти з SonarCloud

### До рефакторингу:
![SonarCloud Before](docs/refactoring/before_screenshot.png)
### Після рефакторингу:
![SonarCloud After](docs/refactoring/after_screenshot.png)

## Результат регресійного тестування
- Всі тести пройшли успішно  
- Жодних регресій не виявлено
