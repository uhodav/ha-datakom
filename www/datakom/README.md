# Datakom Controller Card

Кастомная карточка для визуализации контроллера генератора Datakom в стиле оригинальной панели управления D500.

## Установка

### Вариант 1: Через HACS (рекомендуется)
1. Откройте HACS в Home Assistant
2. Перейдите в раздел "Frontend"
3. Нажмите "+" и найдите "Datakom Controller Card"
4. Установите карточку
5. Перезагрузите Home Assistant

### Вариант 2: Вручную
1. Скопируйте содержимое папки `www` в `config/www/datakom/`:
   ```
   config/www/datakom/
     ├── datakom-controller-card.js
     └── datakom-controller-card-editor.js
   ```
2. Добавьте ресурс в Lovelace:
   - **Settings → Dashboards → Resources → Add Resource**
   - URL: `/local/datakom/datakom-controller-card.js`
   - Resource type: **JavaScript Module**
3. Перезагрузите страницу (Ctrl+F5)

## Использование

Добавьте карточку через визуальный редактор или YAML:

### Визуальный редактор
1. Откройте dashboard в режиме редактирования
2. Нажмите **Add Card**
3. Найдите **Datakom Controller Card**
4. Настройте привязки сенсоров

### YAML конфигурация

```yaml
type: custom:datakom-controller-card
model: D 500
display_title: GEN PHASE VOLTAGES

# Левая секция STATUS - индикаторы состояния
status_indicators:
  - label: AUTO READY
    color: green
    entity: binary_sensor.auto
  - label: ALARM
    color: red
    entity: binary_sensor.alarm_shutdown
  - label: WARNING
    color: red
    entity: binary_sensor.alarm_warning
  - label: SERVICE REQUEST
    color: red
    entity: binary_sensor.service_required

# Центральный дисплей - значения напряжений
display_values:
  - label: L1
    entity: sensor.genset_l1
    col: '0-2'
    entity2: sensor.mains_l1_l2
  - label: L2
    entity: sensor.genset_l2
    col: '0-3'
    entity2: sensor.mains_l2_l3
  - label: L3
    entity: sensor.genset_l3
    col: '0-1'
    entity2: sensor.mains_l3_l1

# Правая секция - Mimic Diagram (системная схема)
mains_available_entity: binary_sensor.mains
mains_contactor_entity: binary_sensor.mains_contactor
load_switch_entity: binary_sensor.load_active
genset_contactor_entity: binary_sensor.genset_contactor
genset_available_entity: binary_sensor.genset

# Кнопки управления с индикаторами
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
    icon: 🏠
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

## Параметры конфигурации

### Основные параметры
- `model` - Модель контроллера (по умолчанию: "D 500")
- `display_title` - Заголовок дисплея (по умолчанию: "GEN PHASE VOLTAGES")

### status_indicators (массив)
Индикаторы в левой части (STATUS секция):
- `label` - Текстовая метка
- `color` - Цвет LED: `green`, `red`, `yellow`
- `entity` - ID сенсора (binary_sensor)

### display_values (массив)
Значения на центральном дисплее:
- `label` - Метка (L1, L2, L3 и т.д.)
- `entity` - ID сенсора с числовым значением

### side_indicators (массив)
Вертикальные индикаторы справа:
- `label` - Метка (MAINS, LOAD, GENSET)
- `color` - Цвет LED: `green`, `red`, `yellow`
- `entity` - ID сенсора (binary_sensor)

### control_buttons (массив)
Кнопки управления внизу:
- `action` - Идентификатор действия
- `label` - Текст под кнопкой
- `class` - CSS класс для стиля (`btn-test`, `btn-auto`, `btn-manual`, `btn-stop`, `btn-run`)
- `icon` - Иконка на кнопке (emoji или символ)
- `image_on` - Путь к изображению для активного состояния
- `image_off` - Путь к изображению для неактивного состояния
- `indicator_entity` - Сенсор для индикатора состояния кнопки
- `indicator_color` - Цвет индикатора: `green`, `red`, `yellow`
- `button_entity` - **Кнопка управления Home Assistant** (новое, рекомендуется)
- `tap_action` - Действие при клике (устаревший способ, см. ниже)
- `hide_if_small` - Скрыть кнопку на маленьких экранах

### Привязка действий к кнопкам

#### Способ 1: button_entity (рекомендуется)
Интеграция Datakom создает кнопки управления автоматически. Просто укажите их в `button_entity`:

```yaml
control_buttons:
  - action: run
    label: RUN
    image_on: /local/community/datakom/img/run-k.png
    image_off: /local/community/datakom/img/run.png
    indicator_entity: binary_sensor.run
    indicator_color: green
    button_entity: button.datakom_device_control_run  # Кнопка управления
  
  - action: auto
    label: AUTO
    image_on: /local/community/datakom/img/auto-k.png
    image_off: /local/community/datakom/img/auto.png
    indicator_entity: binary_sensor.auto
    indicator_color: yellow
    button_entity: button.datakom_device_control_auto
  
  - action: manual
    label: MAN
    image_on: /local/community/datakom/img/manual-k.png
    image_off: /local/community/datakom/img/manual.png
    indicator_entity: binary_sensor.manual
    indicator_color: yellow
    button_entity: button.datakom_device_control_manual
  
  - action: test
    label: TEST
    image_on: /local/community/datakom/img/test-k.png
    image_off: /local/community/datakom/img/test.png
    indicator_entity: binary_sensor.test
    indicator_color: yellow
    button_entity: button.datakom_device_control_test
  
  - action: stop
    label: STOP
    image_on: /local/community/datakom/img/stop-k.png
    image_off: /local/community/datakom/img/stop.png
    indicator_entity: binary_sensor.stop
    indicator_color: yellow
    button_entity: button.datakom_device_control_stop
```

**Доступные кнопки управления:**
- `button.datakom_device_control_run` - Запуск генератора
- `button.datakom_device_control_auto` - Автоматический режим
- `button.datakom_device_control_manual` - Ручной режим
- `button.datakom_device_control_test` - Тестовый режим
- `button.datakom_device_control_stop` - Остановка

#### Способ 2: tap_action (устаревший)

**Вызов сервиса:**
```yaml
tap_action:
  action: call-service
  service: button.press
  service_data:
    entity_id: button.restart
```

**Навигация:**
```yaml
tap_action:
  action: navigate
  navigation_path: /lovelace/generator
```

**Информация о сущности:**
```yaml
tap_action:
  action: more-info
  entity: sensor.genset_state
```

## Примеры

### Минимальная конфигурация
```yaml
type: custom:datakom-controller-card
display_values:
  - label: L1
    entity: sensor.genset_l1
  - label: L2
    entity: sensor.genset_l2
  - label: L3
    entity: sensor.genset_l3
```

### Полная конфигурация с алармами
```yaml
type: custom:datakom-controller-card
model: D 500
display_title: GENERATOR STATUS
status_indicators:
  - label: ONLINE
    color: green
    entity: binary_sensor.api_connection
  - label: ALARM
    color: red
    entity: binary_sensor.alarm_shutdown
  - label: WARNING
    color: red
    entity: binary_sensor.alarm_warning
  - label: SERVICE
    color: yellow
    entity: binary_sensor.service_required
display_values:
  - label: L1
    entity: sensor.genset_l1
  - label: L2
    entity: sensor.genset_l2
  - label: L3
    entity: sensor.genset_l3
  - label: I1
    entity: sensor.genset_i1
  - label: I2
    entity: sensor.genset_i2
  - label: I3
    entity: sensor.genset_i3
side_indicators:
  - label: MAINS
    color: green
    entity: binary_sensor.mains
  - label: LOAD
    color: yellow
    entity: binary_sensor.load_active
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
    button_entity: button.datakom_device_control_test
  - action: auto
    label: AUTO
    class: btn-auto
    icon: 🔧
    image_on: /local/community/datakom/img/auto-k.png
    image_off: /local/community/datakom/img/auto.png
    indicator_entity: binary_sensor.auto
    indicator_color: green
    button_entity: button.datakom_device_control_auto
  - action: manual
    label: MAN
    class: btn-manual
    icon: ✋
    image_on: /local/community/datakom/img/manual-k.png
    image_off: /local/community/datakom/img/manual.png
    indicator_entity: binary_sensor.manual
    indicator_color: yellow
    button_entity: button.datakom_device_control_manual
  - action: stop
    label: STOP
    class: btn-stop
    icon: O
    image_on: /local/community/datakom/img/stop-k.png
    image_off: /local/community/datakom/img/stop.png
    indicator_entity: binary_sensor.stop
    indicator_color: red
    button_entity: button.datakom_device_control_stop
  - action: run
    label: RUN
    class: btn-run
    icon: I
    image_on: /local/community/datakom/img/run-k.png
    image_off: /local/community/datakom/img/run.png
    indicator_entity: binary_sensor.run
    indicator_color: green
    button_entity: button.datakom_device_control_run
```

## Кастомизация внешнего вида

Карточка использует CSS переменные Home Assistant для адаптации к теме. Все цвета и размеры можно переопределить через темы.

## Поддержка

GitHub: https://github.com/uhodav/ha-datakom
Issues: https://github.com/uhodav/ha-datakom/issues
