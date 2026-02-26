# Соответствие параметров API и entity_id сенсоров (Актуальные данные)

## Формат: ID | Label (EN) | LabelHint (UK) | Entity ID

### Основные параметры
- 103 | Genset Mode | Режим роботи | `sensor.datakom_device_rezhim_roboti`
- 105 | Genset State | Стан генератора | `sensor.datakom_device_stan_generatora`

### Генератор - Напруги
- 181 | Genset L1 | Генератор L1 | `sensor.datakom_device_generator_l1`
- 185 | Genset L2 | Генератор L2 | `sensor.datakom_device_generator_l2`
- 189 | Genset L3 | Генератор L3 | `sensor.datakom_device_generator_l3`
- 205 | Genset L1-L2 | Генератор L1-L2 | `sensor.datakom_device_generator_l1_l2`
- 209 | Genset L2-L3 | Генератор L2-L3 | `sensor.datakom_device_generator_l2_l3`
- 213 | Genset L3-L1 | Генератор L3-L1 | `sensor.datakom_device_generator_l3_l1`

### Генератор - Струми
- 193 | Genset I1 | Генератор I1 | `sensor.datakom_device_generator_i1`
- 197 | Genset I2 | Генератор I2 | `sensor.datakom_device_generator_i2`
- 201 | Genset I3 | Генератор I3 | `sensor.datakom_device_generator_i3`

### Генератор - Потужності
- 217 | Genset Tot Active Pwr | Загальна активна потужність | `sensor.datakom_device_zagalna_aktivna_potuzhnist`
- 225 | Genset Tot Apparent Pwr | Загальна повна потужність | `sensor.datakom_device_zagalna_povna_potuzhnist`
- 231 | Genset Freq | Частота генератора | `sensor.datakom_device_chastota_generatora`

### Двигун
- 237 | Engine RPM | Обороти двигуна | `sensor.datakom_device_oboroti_dviguna`
- 239 | Engine Battery Voltage1 | Напруга акумулятора 1 | `sensor.datakom_device_napruga_akumuliatora_1`
- 241 | Engine Charge Voltage | Напруга заряду | `sensor.datakom_device_napruga_zariadu`
- 243 | Engine Oil Pressure | Тиск мастила | `sensor.datakom_device_tisk_mastila`
- 245 | Engine Coolant Temp | Температура охолоджувальної рідини | `sensor.datakom_device_temperatura_okholodzhuvalnoi_ridini`
- 247 | Engine Fuel Level | Рівень палива | `sensor.datakom_device_riven_paliva`
- 249 | Engine Oil Temp | Температура мастила | `sensor.datakom_device_temperatura_mastila`
- 251 | Engine Canopy Temp | Температура кожуха | `sensor.datakom_device_temperatura_kozhuha`

### Двигун - Лічильники
- 503 | Engine Genset Runs | Кількість запусків | `sensor.datakom_device_kilkist_zapuskiv`
- 507 | Engine Genset Cranks | Кількість прокруток | `sensor.datakom_device_kilkist_prokrutok`
- 511 | Engine Run Hours | Години роботи | `sensor.datakom_device_godini_roboti`
- 515 | Engine Hours to Srv1 | Годин до обслуг. 1 | `sensor.datakom_device_godin_do_obslug_1`
- 519 | Engine Days to Srv1 | Днів до обслуг. 1 | `sensor.datakom_device_dniv_do_obslug_1`
- 523 | Engine Hours to Srv2 | Годин до обслуг. 2 | `sensor.datakom_device_godin_do_obslug_2`
- 527 | Engine Days to Srv2 | Днів до обслуг. 2 | `sensor.datakom_device_dniv_do_obslug_2`
- 531 | Engine Hours to Srv3 | Годин до обслуг. 3 | `sensor.datakom_device_godin_do_obslug_3`
- 535 | Engine Days to Srv3 | Днів до обслуг. 3 | `sensor.datakom_device_dniv_do_obslug_3`

### Енергія
- 539 | Genset Total kWh | Загальна енергія кВт·год | `sensor.datakom_device_zagalna_energiia_kvt_god`
- 543 | Genset Total kVArh (Ind) | Загальна реактивна енергія (інд) | `sensor.datakom_device_zagalna_reaktivna_energiia_ind`
- 547 | Genset Total kVArh (Cap) | Загальна реактивна енергія (ємн) | `sensor.datakom_device_zagalna_reaktivna_energiia_iemn`
- 553 | Genset Engine Pwr Rate | Потужність двигуна % | `sensor.datakom_device_potuzhnist_dviguna`
- 555 | Engine Battery Voltage2 | Напруга акумулятора 2 | `sensor.datakom_device_napruga_akumuliatora_2`

### Мережа (Mains)
- 125 | Mains L1 | Мережа L1 | `sensor.datakom_device_merezha_l1`
- 129 | Mains L2 | Мережа L2 | `sensor.datakom_device_merezha_l2`
- 133 | Mains L3 | Мережа L3 | `sensor.datakom_device_merezha_l3`
- 137 | Mains I1 | Мережа I1 | `sensor.datakom_device_merezha_i1`
- 141 | Mains I2 | Мережа I2 | `sensor.datakom_device_merezha_i2`
- 145 | Mains I3 | Мережа I3 | `sensor.datakom_device_merezha_i3`
- 149 | Mains L1-L2 | Мережа L1-L2 | `sensor.datakom_device_merezha_l1_l2`
- 153 | Mains L2-L3 | Мережа L2-L3 | `sensor.datakom_device_merezha_l2_l3`
- 157 | Mains L3-L1 | Мережа L3-L1 | `sensor.datakom_device_merezha_l3_l1`
- 161 | Mains Tot Active Pwr | Загальна активна потужність мережі | `sensor.datakom_device_zagalna_aktivna_potuzhnist_merezhi`
- 165 | Mains Tot Reactive Pwr | Загальна реактивна потужність мережі | `sensor.datakom_device_zagalna_reaktivna_potuzhnist_merezhi`
- 169 | Mains Tot Apparent Pwr | Загальна повна потужність мережі | `sensor.datakom_device_zagalna_povna_potuzhnist_merezhi`
- 175 | Mains Freq | Частота мережі | `sensor.datakom_device_chastota_merezhi`

### Мережа - Енергія
- 561 | Mains Total kWh | Загальна енергія мережі кВт·год | `sensor.datakom_device_zagalna_energiia_merezhi_kvt_god`
- 565 | Mains Total kVArh (Ind) | Загальна реактивна енергія мережі (інд) | `sensor.datakom_device_zagalna_reaktivna_energiia_merezhi_ind`
- 569 | Mains Total kVArh (Cap) | Загальна реактивна енергія мережі (ємн) | `sensor.datakom_device_zagalna_reaktivna_energiia_merezhi_iemn`
- 573 | Mains Total Export kWh | Загальна експортована енергія кВт·год | `sensor.datakom_device_zagalna_eksportovana_energiia_kvt_god`

### Паливо
- 577 | Engine Fuel Consump(FlowM) | Витрата палива (витратомір) | `sensor.datakom_device_vitrata_paliva_vitratomir`
- 585 | Engine Fuel Status | Статус палива | `sensor.datakom_device_status_paliva`
- 587 | Engine Fuel Percent | Паливо % | `sensor.datakom_device_palivo`
- 598 | Engine Fuel Consumption (ECU) | Витрата палива (ECU) | `sensor.datakom_device_vitrata_paliva_ecu`
- 612 | Engine Fuel Rate(FlowM) | Швидкість витрати палива (витратомір) | `sensor.datakom_device_shvidkist_vitrati_paliva_vitratomir`
- 614 | Engine Fuel Rate(ECU) | Швидкість витрати палива (ECU) | `sensor.datakom_device_shvidkist_vitrati_paliva_ecu`

### Інформація
- 19 | Information ModBus Port | ModBus порт | `sensor.datakom_device_modbus_port`
- 21 | Information UniqueID | Унікальний ID | `sensor.datakom_device_unikalnii_id`
- 37 | Information LAN-IP | LAN IP-адреса | `sensor.datakom_device_lan_ip_adresa`
- 589 | Information Satellite(s) | Супутник(и) | `sensor.datakom_device_suputnik_i`
- 592 | Information MAC-Adr | MAC адреса | `sensor.datakom_device_mac_adresa`
- 602 | Information Min Battery Voltage | Мінімальна напруга акумулятора | `sensor.datakom_device_minimalna_napruga_akumuliatora`
- 604 | Information Battery Group Voltage | Напруга групи акумуляторів | `sensor.datakom_device_napruga_grupi_akumuliatoriv`
- 606 | Information Battery Group Current | Струм групи акумуляторів | `sensor.datakom_device_strum_grupi_akumuliatoriv`
- 608 | Information Discharge Current Counter | Лічильник струму розряду | `sensor.datakom_device_lichilnik_strumu_rozriadu`
- 616 | Engine Alternator Voltage | Напруга альтернатора | `sensor.datakom_device_napruga_alternatora`
- 618 | Engine Load Battery Voltage | Напруга навантажувального акумулятора | `sensor.datakom_device_napruga_navantazhuvalnoho_akumuliatora`
- 620 | Engine DC Actual Current | Поточний струм DC | `sensor.datakom_device_potochnii_strum_dc`
- 622 | Engine DC Battery Temp | Температура акумулятора DC | `sensor.datakom_device_temperatura_akumuliatora_dc`
- 624 | Engine Charge State | Стан заряду | `sensor.datakom_device_stan_zariadu`

## Binary Sensors
- `binary_sensor.datakom_device_api_connection` - API Connection / Health
- `binary_sensor.datakom_device_auto` - LED Auto (параметр 103 == 1 або 4)
- `binary_sensor.datakom_device_mains` - LED Mains (параметр 105 == 0)
- `binary_sensor.datakom_device_genset` - LED Genset (параметр 105 != 0)
- `binary_sensor.datakom_device_manual` - LED Manual (параметр 103 == 2)
- `binary_sensor.datakom_device_test` - LED Test (параметр 103 == 3)
- `binary_sensor.datakom_device_run` - LED Run (параметр 105 != 0)
- `binary_sensor.datakom_device_stop` - LED Stop (параметр 103 == 0)
- `binary_sensor.datakom_device_alarm_shutdown` - Shutdown Alarms
- `binary_sensor.datakom_device_alarm_warning` - Warning Alarms
- `binary_sensor.datakom_device_alarm_loaddump` - LoadDump Alarms