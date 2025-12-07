# HelloBugs
[![CI Test](https://github.com/ukma-cs-ssdm-2025/HelloBugs/actions/workflows/ci_test.yml/badge.svg?branch=main)](https://github.com/ukma-cs-ssdm-2025/HelloBugs/actions/workflows/ci_test.yml)
[![CI/CD Staging](https://github.com/ukma-cs-ssdm-2025/HelloBugs/actions/workflows/flask-api-docker.yml/badge.svg)](https://github.com/ukma-cs-ssdm-2025/HelloBugs/actions/workflows/flask-api-docker.yml)
[![Production Deploy](https://github.com/ukma-cs-ssdm-2025/HelloBugs/actions/workflows/production.yml/badge.svg)](https://github.com/ukma-cs-ssdm-2025/HelloBugs/actions/workflows/production.yml)
[![coverage](https://codecov.io/github/ukma-cs-ssdm-2025/hellobugs/graph/badge.svg?token=JLC4ED2WR6)](https://codecov.io/github/ukma-cs-ssdm-2025/hellobugs)


## Інформація про команду
**Склад:**
- Дем'янiк Катерина КН-3
- Правило Анастасія КН-3
- Сич Анастасія КН-3
- Титаренко Владислава КН-3 

## Тема проєкту
### Система бронювання номерів

## Опис ідеї
Система дозволяє гостям онлайн бронювати номери у готелі, а персоналу — керувати бронюваннями.  
Клієнти можуть переглядати доступні номери, обирати дати та отримувати підтвердження бронювання електронною поштою.  


## Артефакти вимог

**Документи з усіма вимогами:**
- [Користувацькі історії](./docs/requirements/user-stories.md)  
- [Нефункціональні вимоги](./docs/requirements/requirements.md)  
- [Матриця простежуваності вимог (RTM)](./docs/requirements/rtm.md)

**Архітектурна документація:**
- [Високорівневий дизайн](./docs/architecture/high-level-design.md)
- [Матриця простежуваності вимог до архітектури](./docs/architecture/traceability-matrix.md)

**Прийняті архітектурні рішення (ADR):**
- [ADR-001](./docs/architecture/decisions/ADR-001.md)
- [ADR-002](./docs/architecture/decisions/ADR-002.md)

**UML-діаграми:**
- [Компонентна діаграма](./docs/architecture/uml/componentsDiagram/components.puml) | [PNG](./docs/architecture/uml/componentsDiagram/components.png)
- [Діаграма класів](./docs/architecture/uml/classDiagram/classDigram.puml)| [PNG](./docs/architecture/uml/classDiagram/class-diagram.png)
- [Діаграма послідовності](./docs/architecture/uml/sequenceDiagram/sequenceDiagram.puml) | [PNG](./docs/architecture/uml/sequenceDiagram/seqDiagram.png)
- [Діаграма розгортання](./docs/architecture/uml/deploymentDiagram/deployment.puml) | [PNG](./docs/architecture/uml/deploymentDiagram/deployment.png)

**Документація API**
- [API Design Documentation](docs/api/api-design.md)  
- [Quality Attributes](docs/api/quality-attributes.md)  
- GitHub Pages: [https://ukma-cs-ssdm-2025.github.io/HelloBugs/](https://ukma-cs-ssdm-2025.github.io/HelloBugs/)

## Стандарти якості та тестування
- [Стратегія тестування](./docs/testing/testing-strategy.md)
- [Debugging Log](./docs/testing/debugging-log.md)
- [Static Analysis Report](./docs/code-quality/static-analysis.md)
- [Звіт code review іншої команди](./docs/code-quality/review-report.md)
- [Прогрес реалізації](./docs/code-quality/progress.md)

## Командні правила
- [Team Charter](./TeamCharter.md)

## Відео Loom 
- [Список відео (Loom/файли)](./Labs/)

## Як запустити проєкт

### Передумови
- Акаунт на [Docker Hub](https://www.docker.com/products/docker-hub/)
- Встановлений [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### 0. Клонувати репозиторій
```bash
git clone https://github.com/ukma-cs-ssdm-2025/HelloBugs.git
cd HelloBugs
```
### 1. Запустити додаток
```bash
docker-compose up --build
```
🌘 Доступний за адресою: http://localhost:3000

### 2. Запустити тести 
```bash
docker-compose -f docker-compose.test.yml run --rm app
```

### Також автоматично розгорнутий за посиланнями: 

🌓 **Staging версія:** https://hellobugs-hotel-staging.up.railway.app/

🌕️ **Production версія:** https://hellobugs-hotel-production.up.railway.app/