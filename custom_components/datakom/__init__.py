from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

DOMAIN = "datakom"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Datakom from a config entry (UI)."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data
    
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor", "button"])
    
    # Удаляем сенсоры, которых больше нет в конфигурации
    await _cleanup_old_entities(hass, entry)
    
    return True

async def _cleanup_old_entities(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Удаляет entity которых больше нет в текущей конфигурации."""
    entity_registry = er.async_get(hass)
    current_param_ids = entry.data.get("param_ids", [])
    
    # Получаем все entity для этой интеграции
    entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    
    for entity in entities:
        # Проверяем только сенсоры параметров (не binary_sensor и button)
        if entity.domain == "sensor" and entity.unique_id.startswith("datakom_"):
            # Извлекаем param_id из unique_id (формат: datakom_{param_id})
            unique_id_parts = entity.unique_id.split("_")
            if len(unique_id_parts) >= 2 and unique_id_parts[1].isdigit():
                param_id = int(unique_id_parts[1])
                # Если этого param_id больше нет в конфигурации - удаляем
                if param_id not in current_param_ids:
                    entity_registry.async_remove(entity.entity_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor", "binary_sensor", "button"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
