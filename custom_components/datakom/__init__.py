import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

DOMAIN = "datakom"
_LOGGER = logging.getLogger(__name__)

__all__ = ["DOMAIN", "_cleanup_old_entities"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Datakom from a config entry (UI)."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data
    
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor", "button"])
    
    # Удаляем старые entity которых больше нет в конфигурации
    await _cleanup_old_entities(hass, entry)
    
    return True

async def _cleanup_old_entities(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Удаляет entity которых больше нет в текущей конфигурации."""
    try:
        entity_registry = er.async_get(hass)
        current_param_ids = entry.data.get("param_ids", [])
        
        _LOGGER.debug(f"Datakom: Starting cleanup. Current param_ids: {current_param_ids}")
        
        # Получаем все entity для этой интеграции
        entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
        
        _LOGGER.debug(f"Datakom: Found {len(entities)} total entities for this integration")
        
        removed_count = 0
        for entity in entities:
            _LOGGER.debug(f"Datakom: Checking entity {entity.entity_id} (domain={entity.domain}, unique_id={entity.unique_id})")
            
            # Проверяем только сенсоры параметров (не binary_sensor и button)
            if entity.domain == "sensor" and entity.unique_id.startswith("datakom_"):
                # Извлекаем param_id из unique_id (формат: datakom_{param_id})
                unique_id_parts = entity.unique_id.split("_")
                if len(unique_id_parts) >= 2:
                    # Проверяем второй элемент - если это число, то это param_id
                    if unique_id_parts[1].isdigit():
                        param_id = int(unique_id_parts[1])
                        # Если этого param_id больше нет в конфигурации - удаляем
                        if param_id not in current_param_ids:
                            _LOGGER.info(f"Datakom: Removing old entity {entity.entity_id} (param_id={param_id} not in config)")
                            entity_registry.async_remove(entity.entity_id)
                            removed_count += 1
                        else:
                            _LOGGER.debug(f"Datakom: Keeping entity {entity.entity_id} (param_id={param_id} is in config)")
                    else:
                        # Если второй элемент не число, проверяем есть ли числовой param_id в конце
                        # Например: datakom_information_hw_version -> нет числа -> удаляем если не в списке
                        # Старый формат, нужно удалить если нет в текущих param_ids
                        has_param_id = False
                        for part in unique_id_parts:
                            if part.isdigit():
                                param_id = int(part)
                                if param_id in current_param_ids:
                                    has_param_id = True
                                    break
                        
                        if not has_param_id:
                            _LOGGER.info(f"Datakom: Removing old entity {entity.entity_id} (old format, not in current config)")
                            entity_registry.async_remove(entity.entity_id)
                            removed_count += 1
        
        if removed_count > 0:
            _LOGGER.info(f"Datakom: Removed {removed_count} old entities")
        else:
            _LOGGER.debug(f"Datakom: No old entities to remove")
    except Exception as e:
        _LOGGER.error(f"Datakom: Error during entity cleanup: {e}", exc_info=True)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor", "binary_sensor", "button"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry
) -> bool:
    """Remove a config entry from a device."""
    return True
