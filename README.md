
 [![Stand With Ukraine](https://raw.githubusercontent.com/vshymanskyy/StandWithUkraine/main/badges/StandWithUkraine.svg)](https://stand-with-ukraine.pp.ua)

#### Ukraine is still suffering from Russian aggression, [please consider supporting Red Cross Ukraine with a donation](https://redcross.org.ua/en/).

[![Stand With Ukraine](https://raw.githubusercontent.com/vshymanskyy/StandWithUkraine/main/banner2-direct.svg)](https://stand-with-ukraine.pp.ua)

---

# Datakom Integration for Home Assistant

Custom integration for monitoring Datakom generator controllers via REST API. Supports multi-language interface (English, Russian, Ukrainian), ENUM sensors with localized states, and calculated sensors for fuel efficiency and battery health monitoring.

## Features

- **Multi-language support**: English, Ukrainian, Russian translations
- **ENUM sensors**: Genset Mode, Genset State, Engine State, Breaker State, Mains State, Battery State, Start Source, Running Type
- **Calculated sensors**: Average fuel rate, fuel time remaining, specific fuel consumption, battery health
- **Binary sensors**: API connection status, LED indicators, alarm monitoring
- **Control buttons**: Restart functionality
- **Automatic parameter detection**: Auto-assigns device classes and units of measurement

## Installation

1. Copy the `custom_components/datakom` folder to your Home Assistant `custom_components` directory
2. Copy the `www/datakom` folder to your Home Assistant `config/www/` directory
3. Restart Home Assistant
4. Add the Lovelace resources:
   - Go to **Settings → Dashboards → Resources → Add Resource**
   - Add card: URL: `/local/datakom/datakom-controller-card.js`, Type: **JavaScript Module**
   - Add editor: URL: `/local/datakom/datakom-controller-card-editor.js`, Type: **JavaScript Module**
   - Click **Create** for each
5. Refresh your browser (Ctrl+F5)
6. Go to **Settings → Devices & Services → Add Integration**
7. Search for "Datakom API"
8. Follow the configuration steps

## Configuration

### Step 1: API Settings
- **API URL**: Base URL of your Datakom REST API (e.g., `https://example.com/datakom/api`)
- **Update Interval**: How often to fetch data (1-60 minutes)
- **Language**: Select interface language (Українська/English/Русский) - auto-detected from Home Assistant language

### Step 2: Parameter Selection
- Choose which parameters to monitor (multiple selection supported)
- Parameter names are automatically translated based on selected language
- The integration will create sensors for all selected parameters
- All parameters are selected by default

## Sensors

### Standard Sensors
Parameters from the API are automatically converted to sensors:
- `sensor.genset_l1`, `sensor.genset_l2`, `sensor.genset_l3` - Generator voltages
- `sensor.genset_i1`, `sensor.genset_i2`, `sensor.genset_i3` - Generator currents
- `sensor.genset_freq` - Generator frequency
- `sensor.genset_tot_active_pwr` - Total active power
- `sensor.engine_rpm` - Engine RPM
- `sensor.engine_coolant_temp` - Coolant temperature
- `sensor.engine_oil_pressure` - Oil pressure
- `sensor.engine_fuel_level` - Fuel level
- `sensor.engine_run_hours` - Engine run hours
- And many more...

### ENUM Sensors (with localized states)
- **`sensor.genset_mode`** - Control mode (Stop, Auto, Manual, Test, Auto-Start, Remote, Schedule, Maintenance, Emergency)
- **`sensor.genset_state`** - Operational state (26 states: At Rest, Cranking, Running, Cooling Down, etc.)
- **`sensor.engine_state`** - Engine status (Off, Cranking, Running, Warming Up, Cooling, etc.)
- **`sensor.breaker_state`** - Circuit breaker position
- **`sensor.mains_state`** - Grid status
- **`sensor.battery_state`** - Battery charge state
- **`sensor.start_source`** - Start trigger source
- **`sensor.running_type`** - Operational mode type

### Calculated Sensors
- **`sensor.avg_fuel_rate`** - Average fuel consumption (L/h)
  - Formula: `Total Fuel Consumption / Run Hours`
- **`sensor.fuel_time_remaining`** - Estimated runtime remaining (hours)
  - Formula: `Fuel Status / Fuel Rate`
- **`sensor.specific_fuel_consumption`** - Fuel efficiency (L/kWh)
  - Formula: `Total Fuel Consumption / Total kWh`
- **`sensor.battery_health`** - Battery condition (%)
  - Based on minimum battery voltage (12.6V = 100%, 10.5V = 0%)

### Binary Sensors
- **`binary_sensor.api_connection`** - API connection status
- **`binary_sensor.mains`** - Mains power LED status (calculated: on when generator is not running)
- **`binary_sensor.genset`** - Generator LED status (calculated: on when generator is running)
- **`binary_sensor.auto`** - Auto mode LED (calculated: on when mode is AUTO or AUTO_START)
- **`binary_sensor.manual`** - Manual mode LED (calculated: on when mode is MANUAL)
- **`binary_sensor.alarm`** - Alarm LED (calculated: on when any alarm is active)
- **`binary_sensor.alarm_shutdown`** - Shutdown alarms
- **`binary_sensor.alarm_warning`** - Warning alarms
- **`binary_sensor.alarm_loaddump`** - LoadDump alarms

**Note**: LED indicators are now calculated from generator state and mode parameters, not from direct API endpoints.

### Buttons
- **`button.restart`** - Restart device controller

## Custom Lovelace Card

The integration includes a custom Datakom Controller Card that mimics the original D500 panel interface.

### Installation
1. Copy `www/datakom` folder to `config/www/datakom/`
2. Add resources: **Settings → Dashboards → Resources**
   - Card URL: `/local/datakom/datakom-controller-card.js`, Type: **JavaScript Module**
   - Editor URL: `/local/datakom/datakom-controller-card-editor.js`, Type: **JavaScript Module**
3. Refresh browser (Ctrl+F5)

### Usage
```yaml
type: custom:datakom-controller-card
model: D 500
display_title: GEN PHASE VOLTAGES
status_indicators:
  - label: AUTO READY
    color: green
    entity: binary_sensor.auto
  - label: ALARM
    color: red
    entity: binary_sensor.alarm_shutdown
display_values:
  - label: L1
    entity: sensor.genset_l1
  - label: L2
    entity: sensor.genset_l2
  - label: L3
    entity: sensor.genset_l3
side_indicators:
  - label: MAINS
    color: green
    entity: binary_sensor.mains
  - label: GENSET
    color: green
    entity: binary_sensor.genset
control_buttons:
  - action: test
    label: TEST
    class: btn-test
    icon: ⚙
    indicator_entity: binary_sensor.test
    indicator_color: yellow
  - action: auto
    label: AUTO
    class: btn-auto
    icon: 🔧
    indicator_entity: binary_sensor.auto
    indicator_color: green
  - action: manual
    label: MAN
    class: btn-manual
    icon: ✋
    indicator_entity: binary_sensor.manual
    indicator_color: yellow
  - action: stop
    label: STOP
    class: btn-stop
    icon: O
    indicator_entity: binary_sensor.stop
    indicator_color: red
  - action: run
    label: RUN
    class: btn-run
    icon: I
    indicator_entity: binary_sensor.run
    indicator_color: green
```

See [www/datakom/README.md](www/datakom/README.md) for detailed card configuration.

## Example Dashboard

```yaml
type: entities
title: Generator Status
entities:
  - entity: sensor.genset_state
    name: Generator State
  - entity: sensor.genset_mode
    name: Control Mode
  - entity: sensor.engine_rpm
    name: Engine RPM
  - entity: sensor.genset_tot_active_pwr
    name: Active Power
  - entity: sensor.avg_fuel_rate
    name: Avg Fuel Rate
  - entity: sensor.fuel_time_remaining
    name: Fuel Time Left
  - entity: sensor.battery_health
    name: Battery Health
```

## Project Structure

```
HA_datakom/
├── custom_components/
│   └── datakom/
│       ├── __init__.py           # Integration initialization
│       ├── sensor.py             # Sensor platform
│       ├── binary_sensor.py      # Binary sensor platform
│       ├── button.py             # Button platform
│       ├── config_flow.py        # UI configuration
│       ├── manifest.json         # Integration metadata
│       ├── services.yaml         # Service definitions
│       └── translations/
│           ├── en.json           # English translations
│           ├── ru.json           # Russian translations
│           └── uk.json           # Ukrainian translations
├── www/
│   └── datakom/
│       ├── datakom-controller-card.js        # Custom Lovelace card
│       ├── datakom-controller-card-editor.js # Visual editor
│       ├── README.md             # Card documentation
│       └── img/                  # Button images
├── dashboard/
│   └── dashboard_demo.yaml       # Example dashboard
├── configuration.yaml
└── README.md
```

## Troubleshooting

### Check Logs
Go to **Settings → System → Logs** and search for `datakom` entries.

### Common Issues
- **Sensors not updating**: Check API URL and network connectivity
- **Missing translations**: Ensure language is set in Home Assistant profile
- **ENUM sensors showing numbers**: Verify translation files are loaded correctly

## API Endpoints Used

### Main Endpoints
- `/health` - API health check and connection status
- `/dump_devm_param_names?language={lang}` - Get parameter list with translations
  - Language options: `uk` (Ukrainian), `en` (English), `ru` (Russian)
- `/dump_devm?id={param_id}` - Get specific parameter value
- `/dump_devm` - Get all parameters (used for calculated sensors and LED states)
- `/dump_devm_alarm` - Get active alarm signals

### Response Structure

**Parameter data** (`/dump_devm`):
```json
{
  "success": true,
  "result": [
    {
      "id": 237,
      "label": "Engine RPM",
      "title": "Обороти двигуна",  // Translation based on language parameter
      "value": 1497,
      "unit": "RPM"
    }
  ],
  "cached": true,
  "timestamp": "2026-01-22T10:30:00.000Z"
}
```

**Alarm data** (`/dump_devm_alarm`):
```json
{
  "success": true,
  "alarm": {
    "ShutDown": [],
    "LoadDump": [],
    "Warning": [
      {
        "slot": 0,
        "name": "Fuel Filling!",
        "index": 252
      }
    ]
  },
  "cached": true
}
```

### Key Parameter IDs
- `103` - Genset Mode (0=Stop, 1=Auto, 2=Manual, 4=Auto-Start, etc.)
- `105` - Genset State (0=At Rest, 1-25=Various running states)
- `237` - Engine RPM
- `239` - Engine Battery Voltage 1
- `587` - Engine Fuel Percent

## License
This integration is provided as-is for monitoring Datakom generator controllers.

---

# Інтеграція Datakom для Home Assistant

Інтеграція для моніторингу контролерів генераторів Datakom через REST API. Підтримує багатомовний інтерфейс (англійська, російська, українська), ENUM сенсори з локалізованими станами та розрахункові сенсори для контролю ефективності палива та стану батареї.

## Можливості

- **Багатомовна підтримка**: переклади українською, англійською, російською
- **ENUM сенсори**: Режим генератора, Стан генератора, Стан двигуна, Стан вимикача, Стан мережі, Стан батареї, Джерело запуску, Тип роботи
- **Розрахункові сенсори**: Середня витрата палива, залишок часу роботи, питома витрата палива, стан батареї
- **Бінарні сенсори**: Стан API підключення, індикатори LED, моніторинг аварій
- **Кнопки керування**: Функція перезапуску
- **Автоматичне визначення параметрів**: Автоматичне призначення класів пристроїв та одиниць вимірювання

## Встановлення

1. Скопіюйте папку `custom_components/datakom` до директорії `custom_components` вашого Home Assistant
2. Скопіюйте папку `www/datakom` до `config/www/` вашого Home Assistant
3. Перезапустіть Home Assistant
4. Додайте Lovelace ресурси:
   - Перейдіть до **Налаштування → Панелі → Ресурси → Додати ресурс**
   - Додайте картку: URL: `/local/datakom/datakom-controller-card.js`, Тип: **JavaScript Module**
   - Додайте редактор: URL: `/local/datakom/datakom-controller-card-editor.js`, Тип: **JavaScript Module**
   - Натисніть **Створити** для кожного
5. Оновіть браузер (Ctrl+F5)
6. Перейдіть до **Налаштування → Пристрої та служби → Додати інтеграцію**
7. Знайдіть "Datakom API"
8. Слідуйте крокам налаштування

## Налаштування

### Крок 1: Налаштування API
- **URL API**: Базова URL вашого Datakom REST API (наприклад, `https://example.com/datakom/api`)
- **Інтервал оновлення**: Як часто оновлювати дані (1-60 хвилин)
- **Мова**: Виберіть мову інтерфейсу (Українська/English/Русский) - автоматично визначається з мови Home Assistant

### Крок 2: Вибір параметрів
- Виберіть параметри для моніторингу (підтримується множинний вибір)
- Назви параметрів автоматично перекладаються відповідно до обраної мови
- Інтеграція створить сенсори для всіх обраних параметрів
- За замовчуванням вибрані всі параметри

## Сенсори

### Стандартні сенсори
Параметри з API автоматично конвертуються в сенсори:
- `sensor.genset_l1`, `sensor.genset_l2`, `sensor.genset_l3` - Напруга генератора
- `sensor.genset_i1`, `sensor.genset_i2`, `sensor.genset_i3` - Струм генератора
- `sensor.genset_freq` - Частота генератора
- `sensor.genset_tot_active_pwr` - Загальна активна потужність
- `sensor.engine_rpm` - Оберти двигуна
- `sensor.engine_coolant_temp` - Температура охолоджувальної рідини
- `sensor.engine_oil_pressure` - Тиск масла
- `sensor.engine_fuel_level` - Рівень палива
- `sensor.engine_run_hours` - Мотогодини
- Та багато інших...

### ENUM сенсори (з локалізованими станами)
- **`sensor.genset_mode`** - Режим управління (Зупинка, Авто, Ручний, Тест, Авто-запуск, Дистанційний, Розклад, Обслуговування, Аварійний)
- **`sensor.genset_state`** - Операційний стан (26 станів: У стані спокою, Прокрутка, Робота, Охолодження тощо)
- **`sensor.engine_state`** - Стан двигуна (Вимкнено, Прокрутка, Робота, Прогрів, Охолодження тощо)
- **`sensor.breaker_state`** - Положення автоматичного вимикача
- **`sensor.mains_state`** - Стан мережі
- **`sensor.battery_state`** - Стан заряду батареї
- **`sensor.start_source`** - Джерело запуску
- **`sensor.running_type`** - Тип операційного режиму

### Розрахункові сенсори
- **`sensor.avg_fuel_rate`** - Середня витрата палива (л/год)
  - Формула: `Загальна витрата палива / Мотогодини`
- **`sensor.fuel_time_remaining`** - Залишок часу роботи (години)
  - Формула: `Залишок палива / Поточна витрата`
- **`sensor.specific_fuel_consumption`** - Питома витрата палива (л/кВт·год)
  - Формула: `Загальна витрата палива / Загальна виробка кВт·год`
- **`sensor.battery_health`** - Стан батареї (%)
  - На основі мінімальної напруги батареї (12.6V = 100%, 10.5V = 0%)

### Бінарні сенсори
- **`binary_sensor.api_connection`** - Стан підключення до API
- **`binary_sensor.mains`** - Стан LED мережі (розраховується: увімкнено коли генератор не працює)
- **`binary_sensor.genset`** - Стан LED генератора (розраховується: увімкнено коли генератор працює)
- **`binary_sensor.auto`** - LED автоматичного режиму (розраховується: увімкнено в режимі AUTO або AUTO_START)
- **`binary_sensor.manual`** - LED ручного режиму (розраховується: увімкнено в режимі MANUAL)
- **`binary_sensor.alarm`** - LED аварії (розраховується: увімкнено при наявності активних аварій)
- **`binary_sensor.alarm_shutdown`** - Аварії вимкнення
- **`binary_sensor.alarm_warning`** - Попереджувальні аварії
- **`binary_sensor.alarm_loaddump`** - Аварії скидання навантаження

**Примітка**: Індикатори LED тепер розраховуються на основі стану та режиму генератора, а не з прямих API endpoints.

### Кнопки
- **`button.restart`** - Перезапуск контролера пристрою

## Приклад панелі

```yaml
type: entities
title: Стан генератора
entities:
  - entity: sensor.genset_state
    name: Стан генератора
  - entity: sensor.genset_mode
    name: Режим управління
  - entity: sensor.engine_rpm
    name: Оберти двигуна
  - entity: sensor.genset_tot_active_pwr
    name: Активна потужність
  - entity: sensor.avg_fuel_rate
    name: Середня витрата палива
  - entity: sensor.fuel_time_remaining
    name: Залишок часу роботи
  - entity: sensor.battery_health
    name: Стан батареї
```

## Структура проекту

```
HA_datakom/
├── custom_components/
│   └── datakom/
│       ├── __init__.py           # Ініціалізація інтеграції
│       ├── sensor.py             # Платформа сенсорів
│       ├── binary_sensor.py      # Платформа бінарних сенсорів
│       ├── button.py             # Платформа кнопок
│       ├── config_flow.py        # UI налаштування
│       ├── manifest.json         # Метадані інтеграції
│       ├── services.yaml         # Визначення служб
│       └── translations/
│           ├── en.json           # Англійські переклади
│           ├── ru.json           # Російські переклади
│           └── uk.json           # Українські переклади
├── www/
│   └── datakom/
│       ├── datakom-controller-card.js        # Користувацька картка Lovelace
│       ├── datakom-controller-card-editor.js # Візуальний редактор
│       ├── README.md             # Документація картки
│       └── img/                  # Зображення кнопок
├── dashboard/
│   └── dashboard_demo.yaml       # Приклад панелі
├── configuration.yaml
└── README.md
```

## Усунення несправностей

### Перевірка логів
Перейдіть до **Налаштування → Система → Логи** та шукайте записи `datakom`.

### Поширені проблеми
- **Сенсори не оновлюються**: Перевірте URL API та підключення до мережі
- **Відсутні переклади**: Переконайтеся, що мова встановлена в профілі Home Assistant
- **ENUM сенсори показують числа**: Перевірте, чи правильно завантажені файли перекладів

## Використовувані API endpoints

### Основні endpoints
- `/health` - Перевірка стану API та підключення
- `/dump_devm_param_names?language={lang}` - Отримання списку параметрів з перекладами
  - Опції мови: `uk` (українська), `en` (англійська), `ru` (російська)
- `/dump_devm?id={param_id}` - Отримання значення конкретного параметра
- `/dump_devm` - Отримання всіх параметрів (використовується для розрахункових сенсорів та станів LED)
- `/dump_devm_alarm` - Отримання активних аварійних сигналів

### Ключові ID параметрів
- `103` - Режим генератора (0=Стоп, 1=Авто, 2=Ручний, 4=Авто-запуск тощо)
- `105` - Стан генератора (0=У спокої, 1-25=Різні робочі стани)
- `237` - Оберти двигуна
- `239` - Напруга акумулятора двигуна 1
- `587` - Рівень палива у відсотках

## Ліцензія
Ця інтеграція надається як є для моніторингу контролерів генераторів Datakom.
