# Цифровий деканат - Практична робота 1

Готовий FastAPI API. Номер у списку **15**, варіант **3** - `academic_status`.

## Запуск у Windows

Розпакуйте архів. Установіть Python 3.12+ з pip, відкрийте папку проєкту.
Запустіть **setup.cmd**, після завершення - **start.cmd**.
Відкрийте http://127.0.0.1:8000/docs. Для тестів запустіть **test.cmd**.
Зупиняйте сервер через Ctrl+C. Для першого встановлення потрібен інтернет.

Або виконайте у PowerShell у папці з pyproject.toml:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Окремий термінал для тестів:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

У Linux/macOS: `python3 -m venv .venv`, потім `.venv/bin/python -m pip install -e ".[dev]"`
та `.venv/bin/python -m uvicorn app.main:app --reload`.

## Документація та результати

- [Повний гайд запуску](docs/launch-guide.md)
- [Звіт із практичної роботи](docs/report.md) - заповніть титульні дані та посилання після публікації
- [Контракт OpenAPI](docs/openapi.json); актуальна схема - `/openapi.json`
- [Результат pytest](evidence/pytest.txt): **57 passed**, одне попередження бібліотеки
- [Результат колекції](evidence/newman.txt): **20 запитів, 42 твердження, 0 провалів**
- [Машинний звіт Newman](evidence/newman-results.json), [підсумок](evidence/summary.json)
- `requirements-tested.txt` - точні версії перевіреного Windows-середовища

## Контракт API

| Метод | Шлях | Успіх | Помилки |
| --- | --- | --- | --- |
| GET | /health | 200 | - |
| POST | /api/v1/students | 201 | 409, 422 |
| GET | /api/v1/students | 200 | 422 |
| GET | /api/v1/students/{student_id} | 200 | 404, 422 |
| PATCH | /api/v1/students/{student_id} | 200 | 404, 409, 422 |

Приклад POST:

```json
{"full_name":"Олена Коваль","email":"olena.koval@example.com","group_code":"КН-31","academic_status":"active"}
```

`full_name`: 5-120 символів після обрізання пробілів; `email`: EmailStr, унікальність
без урахування регістру; `group_code`: `^[A-ZА-ЩЬЮЯЄІЇҐ0-9]+-[0-9]{2}$`.
Навчальні стани: `active` - навчається, `academic_leave` - академічна відпустка,
`graduated` - завершив навчання, `expelled` - відрахований. Вони чутливі до регістру.
Фільтр: `GET /api/v1/students?academic_status=active`.

PATCH змінює тільки передані поля. `{}`, `null` у переданому полі, `id` і невідомі
поля відхиляються. Унікальність email перевіряється і при PATCH із виключенням
поточного запису. Конфлікт не змінює жодного поля.

## Колекція Postman

Імпортуйте `postman/digital-dean-practice-01.postman_collection.json`.
Установіть `base_url` = `http://127.0.0.1:8000`, запустіть усі запити послідовно.
Колекція зберігає student_id і використовує нові навчальні email на кожен прохід.
Альтернатива за наявності Node.js/npm:

```text
npx --yes newman@6.2.3 run postman/digital-dean-practice-01.postman_collection.json
```

## Git

Основа: https://github.com/serhii-ch-eu/digital-dean-api-starter.
У корені комплекту є `practice-01.bundle` із повною локальною історією, гілкою
та тегом practice-01. Інструкція відновлення та публікації у власний форк - у гайді.
Віддалена публікація автоматично не виконувалася.

## Межі

Репозиторій зберігає дані в памʼяті одного процесу; перезапуск і --reload їх очищують.
Видалення, база даних, авторизація, TLS та аудит не реалізовані в цій роботі.
Використовуйте лише вигадані дані. Запускайте локально, без додаткових workers.
