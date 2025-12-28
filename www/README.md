[![Stand With Ukraine](https://raw.githubusercontent.com/vshymanskyy/StandWithUkraine/main/badges/StandWithUkraine.svg)](https://stand-with-ukraine.pp.ua)

#### Ukraine is still suffering from Russian aggression, [please consider supporting Red Cross Ukraine with a donation](https://redcross.org.ua/en/).

[![Stand With Ukraine](https://raw.githubusercontent.com/vshymanskyy/StandWithUkraine/main/banner2-direct.svg)](https://stand-with-ukraine.pp.ua)

---

# Datakom Controller Card

Custom Lovelace card for Home Assistant that mimics the physical Datakom D-500 generator controller interface.

## Features

- **Authentic design**: Mimics the original D-500 panel appearance
- **Status indicators**: LED indicators for various system states
- **Display section**: Shows key parameters like fuel level, power output, voltages
- **Side indicators**: MAINS and GENSET status LEDs
- **Control buttons**: Visual representation of TEST, AUTO, MANUAL, STOP, RUN modes
- **Custom button images**: Support for custom on/off button images
- **Real-time updates**: Automatic state updates from Home Assistant entities

## Installation

### HACS (Recommended)
This card will be available through HACS soon.

### Manual Installation
1. Copy `datakom-controller-card.js` to your `/config/www/community/datakom/` directory
2. Copy button images to `/config/www/community/datakom/img/` directory
3. Add the card as a resource in Home Assistant:
   - Go to **Settings → Dashboards → Resources**
   - Click **Add Resource**
   - URL: `/local/community/datakom/datakom-controller-card.js`
   - Resource type: **JavaScript Module**
   - Click **Create**
4. Refresh your browser (Ctrl+F5)

## Configuration

Add the card to your Lovelace dashboard:

```yaml
type: custom:datakom-controller-card
model: D-500 MK3
display_title: Properties
status_indicators:
  - label: AUTO READY
    color: green
    entity: binary_sensor.auto
  - label: shutdown
    color: red
    entity: binary_sensor.alarm_shutdown
  - label: WARNING
    color: yellow
    entity: binary_sensor.alarm_warning
  - label: loaddump
    color: yellow
    entity: binary_sensor.alarm_loaddump
display_values:
  - label: Fuel
    entity: sensor.engine_fuel_level
  - label: kWt
    entity: sensor.genset_tot_active_pwr
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
    image_on: /local/community/datakom/img/test-k.png
    image_off: /local/community/datakom/img/test.png
    indicator_entity: binary_sensor.test
    indicator_color: yellow
  - action: auto
    label: AUTO
    class: btn-auto
    icon: 🔧
    image_on: /local/community/datakom/img/auto-k.png
    image_off: /local/community/datakom/img/auto.png
    indicator_entity: binary_sensor.auto
    indicator_color: yellow
  - action: manual
    label: MAN
    class: btn-manual
    icon: ✋
    image_on: /local/community/datakom/img/manual-k.png
    image_off: /local/community/datakom/img/manual.png
    indicator_entity: binary_sensor.manual
    indicator_color: yellow
  - action: stop
    label: STOP
    class: btn-stop
    icon: O
    image_on: /local/community/datakom/img/stop-k.png
    image_off: /local/community/datakom/img/stop.png
    indicator_entity: binary_sensor.stop
    indicator_color: yellow
  - action: run
    label: RUN
    class: btn-run
    icon: I
    image_on: /local/community/datakom/img/run-k.png
    image_off: /local/community/datakom/img/run.png
    indicator_entity: binary_sensor.run
    indicator_color: green
```

## Configuration Options

### Card Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `type` | string | Yes | - | Must be `custom:datakom-controller-card` |
| `model` | string | No | `D 500` | Model name displayed in header |
| `display_title` | string | No | `GEN PHASE VOLTAGES` | Title shown above display section |
| `status_indicators` | list | No | - | List of status LED indicators (left side) |
| `display_values` | list | No | - | List of values shown in display section |
| `side_indicators` | list | No | - | List of side LED indicators (right side) |
| `control_buttons` | list | No | - | List of control buttons at bottom |

### Status Indicators Options

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `label` | string | Yes | Label text for the indicator |
| `color` | string | Yes | LED color: `green`, `red`, or `yellow` |
| `entity` | string | Yes | Binary sensor entity to control LED state |

### Display Values Options

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `label` | string | Yes | Label text for the value |
| `entity` | string | Yes | Sensor entity to display value from |

### Side Indicators Options

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `label` | string | Yes | Label text for the indicator |
| `color` | string | Yes | LED color: `green`, `red`, or `yellow` |
| `entity` | string | Yes | Binary sensor entity to control LED state |

### Control Buttons Options

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `action` | string | Yes | Button action identifier |
| `label` | string | Yes | Button label text |
| `class` | string | No | CSS class for button styling |
| `icon` | string | No | Emoji or symbol to display (used when no images) |
| `image_on` | string | No | Path to image when button is active |
| `image_off` | string | No | Path to image when button is inactive |
| `indicator_entity` | string | Yes | Binary sensor to determine button state |
| `indicator_color` | string | Yes | Indicator LED color: `green`, `red`, or `yellow` |

## Button Images

Place your custom button images in `/config/www/community/datakom/img/` directory. The card supports separate images for on/off states:
- `test.png` / `test-k.png` - Test mode button
- `auto.png` / `auto-k.png` - Auto mode button
- `manual.png` / `manual-k.png` - Manual mode button
- `stop.png` / `stop-k.png` - Stop button
- `run.png` / `run-k.png` - Run button

Image format: PNG recommended, size: 70x70 pixels optimal.

## Styling

The card uses predefined button styles:
- `btn-test` - Yellow button (test mode)
- `btn-auto` - Dark button (auto mode)
- `btn-manual` - Dark button (manual mode)
- `btn-stop` - Red button (stop)
- `btn-run` - Green button (run)

## Troubleshooting

### Card not appearing
1. Verify the resource is added correctly in Settings → Dashboards → Resources
2. Check that the URL path is correct: `/local/community/datakom/datakom-controller-card.js`
3. Clear browser cache (Ctrl+F5) or open in incognito mode
4. Check browser console (F12) for JavaScript errors

### Images not loading
1. Verify images are in `/config/www/community/datakom/img/` directory
2. Check image paths in configuration start with `/local/community/datakom/img/`
3. Verify image file names match exactly (case-sensitive)
4. Clear browser cache

### LEDs not updating
1. Verify entity IDs are correct
2. Check that entities exist in Home Assistant
3. Ensure entity states are `on`/`off` for binary sensors
4. Check Home Assistant logs for errors

### Display values not showing
1. Verify sensor entity IDs are correct
2. Ensure sensors have numeric states or valid string values
3. Check that sensors are updating in Home Assistant

## Examples

### Minimal Configuration
```yaml
type: custom:datakom-controller-card
model: D-500
display_title: Status
status_indicators:
  - label: READY
    color: green
    entity: binary_sensor.ready
display_values:
  - label: Power
    entity: sensor.power
control_buttons:
  - action: start
    label: START
    icon: ▶
    indicator_entity: binary_sensor.running
    indicator_color: green
```

### Full Configuration with All Features
See the configuration example above with all available options.

## Support

For issues, feature requests, or questions:
- GitHub: [https://github.com/yourusername/ha-datakom](https://github.com/yourusername/ha-datakom)
- Home Assistant Community: [Link to forum topic]

## License

This card is provided as-is for use with Datakom generator controller integration.

---

# Картка контролера Datakom

Користувацька картка Lovelace для Home Assistant, що імітує фізичний інтерфейс контролера генератора Datakom D-500.

## Можливості

- **Автентичний дизайн**: Імітує зовнішній вигляд оригінальної панелі D-500
- **Індикатори стану**: LED індикатори для різних станів системи
- **Секція дисплею**: Відображає ключові параметри: рівень палива, вихідна потужність, напруга
- **Бічні індикатори**: LED стану MAINS та GENSET
- **Кнопки керування**: Візуальне представлення режимів TEST, AUTO, MANUAL, STOP, RUN
- **Власні зображення кнопок**: Підтримка користувацьких зображень для станів вкл/викл
- **Оновлення в реальному часі**: Автоматичне оновлення станів з сутностей Home Assistant

## Встановлення

### HACS (Рекомендовано)
Ця картка незабаром буде доступна через HACS.

### Ручне встановлення
1. Скопіюйте `datakom-controller-card.js` до директорії `/config/www/community/datakom/`
2. Скопіюйте зображення кнопок до директорії `/config/www/community/datakom/img/`
3. Додайте картку як ресурс у Home Assistant:
   - Перейдіть до **Налаштування → Панелі → Ресурси**
   - Натисніть **Додати ресурс**
   - URL: `/local/community/datakom/datakom-controller-card.js`
   - Тип ресурсу: **JavaScript Module**
   - Натисніть **Створити**
4. Оновіть браузер (Ctrl+F5)

## Налаштування

Додайте картку до панелі Lovelace:

```yaml
type: custom:datakom-controller-card
model: D-500 MK3
display_title: Властивості
status_indicators:
  - label: AUTO READY
    color: green
    entity: binary_sensor.auto
  - label: shutdown
    color: red
    entity: binary_sensor.alarm_shutdown
  - label: WARNING
    color: yellow
    entity: binary_sensor.alarm_warning
  - label: loaddump
    color: yellow
    entity: binary_sensor.alarm_loaddump
display_values:
  - label: Fuel
    entity: sensor.engine_fuel_level
  - label: kWt
    entity: sensor.genset_tot_active_pwr
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
    image_on: /local/community/datakom/img/test-k.png
    image_off: /local/community/datakom/img/test.png
    indicator_entity: binary_sensor.test
    indicator_color: yellow
  - action: auto
    label: AUTO
    class: btn-auto
    icon: 🔧
    image_on: /local/community/datakom/img/auto-k.png
    image_off: /local/community/datakom/img/auto.png
    indicator_entity: binary_sensor.auto
    indicator_color: yellow
  - action: manual
    label: MAN
    class: btn-manual
    icon: ✋
    image_on: /local/community/datakom/img/manual-k.png
    image_off: /local/community/datakom/img/manual.png
    indicator_entity: binary_sensor.manual
    indicator_color: yellow
  - action: stop
    label: STOP
    class: btn-stop
    icon: O
    image_on: /local/community/datakom/img/stop-k.png
    image_off: /local/community/datakom/img/stop.png
    indicator_entity: binary_sensor.stop
    indicator_color: yellow
  - action: run
    label: RUN
    class: btn-run
    icon: I
    image_on: /local/community/datakom/img/run-k.png
    image_off: /local/community/datakom/img/run.png
    indicator_entity: binary_sensor.run
    indicator_color: green
```

## Параметри налаштування

### Параметри картки

| Параметр | Тип | Обов'язковий | За замовчуванням | Опис |
|----------|-----|--------------|------------------|------|
| `type` | string | Так | - | Має бути `custom:datakom-controller-card` |
| `model` | string | Ні | `D 500` | Назва моделі у заголовку |
| `display_title` | string | Ні | `GEN PHASE VOLTAGES` | Заголовок над секцією дисплею |
| `status_indicators` | list | Ні | - | Список LED індикаторів стану (ліва сторона) |
| `display_values` | list | Ні | - | Список значень у секції дисплею |
| `side_indicators` | list | Ні | - | Список бічних LED індикаторів (права сторона) |
| `control_buttons` | list | Ні | - | Список кнопок керування внизу |

### Параметри індикаторів стану

| Параметр | Тип | Обов'язковий | Опис |
|----------|-----|--------------|------|
| `label` | string | Так | Текст мітки індикатора |
| `color` | string | Так | Колір LED: `green`, `red` або `yellow` |
| `entity` | string | Так | Бінарний сенсор для керування станом LED |

### Параметри значень дисплею

| Параметр | Тип | Обов'язковий | Опис |
|----------|-----|--------------|------|
| `label` | string | Так | Текст мітки значення |
| `entity` | string | Так | Сенсор для відображення значення |

### Параметри бічних індикаторів

| Параметр | Тип | Обов'язковий | Опис |
|----------|-----|--------------|------|
| `label` | string | Так | Текст мітки індикатора |
| `color` | string | Так | Колір LED: `green`, `red` або `yellow` |
| `entity` | string | Так | Бінарний сенсор для керування станом LED |

### Параметри кнопок керування

| Параметр | Тип | Обов'язковий | Опис |
|----------|-----|--------------|------|
| `action` | string | Так | Ідентифікатор дії кнопки |
| `label` | string | Так | Текст мітки кнопки |
| `class` | string | Ні | CSS клас для стилізації кнопки |
| `icon` | string | Ні | Емодзі або символ (використовується без зображень) |
| `image_on` | string | Ні | Шлях до зображення активної кнопки |
| `image_off` | string | Ні | Шлях до зображення неактивної кнопки |
| `indicator_entity` | string | Так | Бінарний сенсор для визначення стану кнопки |
| `indicator_color` | string | Так | Колір індикатора LED: `green`, `red` або `yellow` |

## Зображення кнопок

Розмістіть власні зображення кнопок у директорії `/config/www/community/datakom/img/`. Картка підтримує окремі зображення для станів вкл/викл:
- `test.png` / `test-k.png` - Кнопка тестового режиму
- `auto.png` / `auto-k.png` - Кнопка авто режиму
- `manual.png` / `manual-k.png` - Кнопка ручного режиму
- `stop.png` / `stop-k.png` - Кнопка зупинки
- `run.png` / `run-k.png` - Кнопка запуску

Формат зображення: Рекомендується PNG, розмір: оптимально 70x70 пікселів.

## Стилізація

Картка використовує попередньо визначені стилі кнопок:
- `btn-test` - Жовта кнопка (тестовий режим)
- `btn-auto` - Темна кнопка (авто режим)
- `btn-manual` - Темна кнопка (ручний режим)
- `btn-stop` - Червона кнопка (зупинка)
- `btn-run` - Зелена кнопка (запуск)

## Усунення несправностей

### Картка не відображається
1. Перевірте, що ресурс додано правильно у Налаштування → Панелі → Ресурси
2. Переконайтеся, що шлях URL правильний: `/local/community/datakom/datakom-controller-card.js`
3. Очистіть кеш браузера (Ctrl+F5) або відкрийте в режимі інкогніто
4. Перевірте консоль браузера (F12) на наявність помилок JavaScript

### Зображення не завантажуються
1. Перевірте, що зображення знаходяться у `/config/www/community/datakom/img/`
2. Переконайтеся, що шляхи зображень у конфігурації починаються з `/local/community/datakom/img/`
3. Перевірте, що імена файлів зображень точно збігаються (з урахуванням регістру)
4. Очистіть кеш браузера

### LED не оновлюються
1. Перевірте правильність ID сутностей
2. Переконайтеся, що сутності існують у Home Assistant
3. Переконайтеся, що стани сутностей `on`/`off` для бінарних сенсорів
4. Перевірте логи Home Assistant на наявність помилок

### Значення дисплею не відображаються
1. Перевірте правильність ID сенсорів
2. Переконайтеся, що сенсори мають числові стани або валідні текстові значення
3. Переконайтеся, що сенсори оновлюються у Home Assistant

## Приклади

### Мінімальна конфігурація
```yaml
type: custom:datakom-controller-card
model: D-500
display_title: Стан
status_indicators:
  - label: ГОТОВО
    color: green
    entity: binary_sensor.ready
display_values:
  - label: Потужність
    entity: sensor.power
control_buttons:
  - action: start
    label: ПУСК
    icon: ▶
    indicator_entity: binary_sensor.running
    indicator_color: green
```

### Повна конфігурація з усіма можливостями
Дивіться приклад конфігурації вище з усіма доступними параметрами.

## Підтримка

З питань, запитів функцій або питань:
- GitHub: [https://github.com/yourusername/ha-datakom](https://github.com/yourusername/ha-datakom)
- Спільнота Home Assistant: [Посилання на тему форуму]

## Ліцензія

Ця картка надається як є для використання з інтеграцією контролера генератора Datakom.
