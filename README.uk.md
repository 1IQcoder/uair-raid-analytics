# UAir-raid-analytics

### Зміст

- [AI-First Розробка](#ai-first-розробка)
- [Технологічний Стек](#технологічний-стек)
- [Як Працюють Дані](#як-працюють-дані)
- [Швидкий Запуск](#швидкий-запуск)
- [Робота З Районним Воркером](#робота-з-районним-воркером)
- [Корисні Команди](#корисні-команди)
- [Документація](#документація)

### Фінальний продукт доступний за посиланням: **https://uair-raid-analytics.potuzhnist.xyz/**

UAir-raid-analytics - це вебзастосунок для дослідження історичної статистики повітряних тривог в Україні. Проєкт показує дані на інтерактивній карті, дозволяє перемикатися між рівнем областей і районів, порівнювати регіони за кількістю тривог, сумарною тривалістю або комбінованим індексом. Основна ідея - зробити дані про повітряні тривоги зручними для візуального аналізу: користувач може швидко побачити, де тривоги оголошувались частіше, де вони тривали довше, як змінюється картина залежно від періоду, і які регіони мають найбільше навантаження за вибраною метрикою.

Проєкт запроваджує два рівні перегляду:

- **Області** - основний режим з довшою історією на базі відкритого датасету.
- **Райони** - більш детальна карта, яка використовує локально кешовані дані з alerts.in.ua за останній місяць.

## AI-First Розробка

Цей проєкт від самого початку був створений тільки за допомогою ШІ: **ChatGPT Plus + Codex**. Архітектура, бекенд, frontend, робота з картами, воркер синхронізації, документація і послідовні виправлення помилок були реалізовані через діалоги з AI.

У директорії `ai_conversations/` можна знайти повні діалоги з ШІ, за допомогою яких створювався застосунок. Це частина проєкту: вона показує не тільки фінальний код, а й процес прийняття рішень, пошуку помилок і поступового доведення продукту до робочого стану.

## Технологічний Стек

- **Python 3.12+**
- **FastAPI** - backend і API
- **SQLAlchemy** - робота з локальною базою даних
- **SQLite** - локальне сховище оброблених подій
- **Jinja2** - HTML-шаблони
- **Vanilla JavaScript** - frontend-логіка без frontend-фреймворку
- **D3 Geo** - рендер GeoJSON як inline SVG
- **HTML/CSS SVG map UI** - карта без Leaflet, OpenStreetMap і зовнішніх tile-провайдерів
- **httpx** - клієнт для alerts.in.ua API у фоновому воркері
- **pandas** - обробка CSV-датасету

## Як Працюють Дані

### Обласна статистика

Основне джерело історичних даних - **Vadimkin Ukrainian Air Raid Sirens Dataset**. Скрипт `scripts/update_dataset.py` завантажує CSV-дані з налаштованих URL, нормалізує події тривог і записує їх у локальну SQLite-базу.

Коли користувач відкриває карту або змінює фільтри, backend не використовує наперед прораховану таблицю для кожного режиму. Замість цього він читає локальні події з бази і рахує потрібні метрики на запит:

- кількість періодів тривоги;
- сумарну тривалість;
- середню тривалість;
- комбінований індекс інтенсивності.

Для обласного режиму діє правило: якщо тривога активна хоча б в одному районі області, область вважається під тривогою. Якщо одночасної тривоги немає ніде в межах області, такий період вважається завершеним.

### Районна статистика і alerts.in.ua worker

Районні дані беруться з офіційного API **alerts.in.ua**, але frontend ніколи не звертається до цього API напряму. Для цього створений окремий фоновий воркер:

```bash
python scripts/sync_alertsua_raions.py --loop
```

Воркер працює з локальним reference-файлом:

```text
data/reference/alertsua_raions.csv
```

У цьому файлі зберігаються відомі райони, їхні UID, області та ознака `enabled`. Важлива технічна деталь: history endpoint alerts.in.ua не працює напряму з UID районів. Тому воркер запитує історію по **UID області**, а з відповіді бере тільки записи, де `location_type == "raion"` і `alert_type == "air_raid"`.

Отримані районні події кешуються в локальній базі. API сайту для районів читає тільки локальну БД:

- `/api/raions/summary`
- `/api/raions/{location_uid}/daily`
- `/api/raions/sync-status`

Це зроблено з кількох причин:

- не розкривати `ALERTS_IN_UA_TOKEN` у браузері;
- не викликати зовнішній API під час користувацьких запитів;
- дотримуватись rate limit alerts.in.ua;
- показувати користувачу швидку відповідь з локального кешу.

За замовчуванням автозапуск воркера вимкнений. Синхронізацію потрібно запускати явно.

## Швидкий Запуск

### 1. Клонувати репозиторій

```bash
git clone <repository-url>
cd uair_raid_analytics
```

### 2. Створити virtualenv і встановити залежності

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

### 3. Налаштувати `.env`

Скопіюйте приклад:

```bash
cp .env.example .env
```

Для Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Базовий `.env`:

```env
UAIR_APP_NAME=UAir-raid-analytics
UAIR_DEBUG=false
UAIR_DATABASE_URL=sqlite:///./data/processed/uair_raid_analytics.sqlite3
UAIR_PRIMARY_DATASET_URL=https://raw.githubusercontent.com/Vadimkin/ukrainian-air-raid-sirens-dataset/main/datasets/official_data_uk.csv
UAIR_SECONDARY_DATASET_URL=https://raw.githubusercontent.com/Vadimkin/ukrainian-air-raid-sirens-dataset/main/datasets/volunteer_data_uk.csv

ALERTS_IN_UA_TOKEN=
ALERTS_IN_UA_HISTORY_MIN_INTERVAL_SECONDS=35
ALERTS_IN_UA_HISTORY_DAILY_LIMIT=500
ALERTS_IN_UA_WORKER_ENABLED=false
```

Для обласного режиму токен alerts.in.ua не потрібен. Для синхронізації районних даних потрібно отримати token alerts.in.ua і записати його в:

```env
ALERTS_IN_UA_TOKEN=your_token_here
```

Не зменшуйте `ALERTS_IN_UA_HISTORY_MIN_INTERVAL_SECONDS` нижче 30 секунд. Поточне значення 35 секунд обране через обмеження history endpoint alerts.in.ua: до 2 запитів на хвилину.

### 4. Завантажити і обробити основний датасет

```bash
python scripts/update_dataset.py
```

### 5. Запустити застосунок

```bash
uvicorn server.main:app --reload
```

Локально сайт буде доступний за адресою:

```text
http://127.0.0.1:8000
```

Сторінка з описом проєкту:

```text
http://127.0.0.1:8000/about
```

## Робота З Районним Воркером

Перевірити, які області будуть синхронізовані:

```bash
python scripts/sync_alertsua_raions.py --dry-run --limit 3
```

Синхронізувати одну область:

```bash
python scripts/sync_alertsua_raions.py --once
```

Запустити постійну синхронізацію:

```bash
python scripts/sync_alertsua_raions.py --loop
```

Воркер робить запити не по районах, а по унікальних UID областей з `data/reference/alertsua_raions.csv`, після чого витягує з відповіді районні записи. Один повний цикл займає приблизно 15-16 хвилин, бо між запитами є безпечна пауза.

## Корисні Команди

Перегенерувати нормалізовані GeoJSON-файли:

```bash
python scripts/normalize_geojson.py
```

Перевірити Python-файли на синтаксис:

```bash
python -m compileall -q server scripts
```

Перевірити CLI entrypoint для оновлення датасету:

```bash
uair-update-dataset
```

## Документація

Детальніший технічний контекст збережений у `docs/`, зокрема:

- архітектура;
- pipeline обробки даних;
- API endpoints;
- frontend-логіка;
- журнал проблем і рішень.
