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
    
    # Удаляем старые entity перед созданием новых
    await _cleanup_old_entities(hass, entry)
    
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor", "button"])
    
    return True

async def _cleanup_old_entities(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Удаляет старые entity которых больше нет в текущей конфигурации."""
    try:
        entity_registry = er.async_get(hass)
        current_param_ids = [int(pid) if isinstance(pid, str) else pid for pid in entry.data.get("param_ids", [])]
        
        _LOGGER.debug(f"Datakom: Starting cleanup. Current param_ids: {current_param_ids}")
        
        # Получаем все entity для этой интеграции
        entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
        
        _LOGGER.debug(f"Datakom: Found {len(entities)} total entities for this integration")
        
        # Список правильных unique_id для binary_sensor и button
        valid_binary_sensor_ids = {
            "datakom_health",
            "datakom_led_mains", "datakom_led_genset", "datakom_led_auto", "datakom_led_manual", 
            "datakom_led_test", "datakom_led_run", "datakom_led_stop", "datakom_led_alarm",
            "datakom_alarm_shutdown", "datakom_alarm_loaddump", "datakom_alarm_warning"
        }
        valid_button_ids = {
            "datakom_restart",
            "datakom_control_run", "datakom_control_auto", "datakom_control_manual",
            "datakom_control_test", "datakom_control_stop"
        }
        
        removed_count = 0
        for entity in entities:
            should_remove = False
            
            if entity.domain == "sensor":
                # Для sensor: удаляем если unique_id не в формате datakom_{число} или число не в param_ids
                if entity.unique_id.startswith("datakom_"):
                    parts = entity.unique_id.split("_", 1)
                    if len(parts) == 2 and parts[1].isdigit():
                        param_id = int(parts[1])
                        if param_id not in current_param_ids:
                            should_remove = True
                            _LOGGER.debug(f"Datakom: Will remove sensor {entity.entity_id} - param_id {param_id} not in config")
                    else:
                        # Старый формат типа datakom_engine_coolant_temp
                        should_remove = True
                        _LOGGER.debug(f"Datakom: Will remove sensor {entity.entity_id} - old name format")
                elif entity.unique_id.startswith("terrakotta_"):
                    # Старый prefix terrakotta
                    should_remove = True
                    _LOGGER.debug(f"Datakom: Will remove sensor {entity.entity_id} - old terrakotta prefix")
                    
            elif entity.domain == "binary_sensor":
                # Для binary_sensor: удаляем если unique_id не в списке правильных или имеет старый prefix
                if entity.unique_id.startswith("terrakotta_"):
                    should_remove = True
                    _LOGGER.debug(f"Datakom: Will remove binary_sensor {entity.entity_id} - old terrakotta prefix")
                elif entity.unique_id not in valid_binary_sensor_ids:
                    should_remove = True
                    _LOGGER.debug(f"Datakom: Will remove binary_sensor {entity.entity_id} - not in valid list")
                    
            elif entity.domain == "button":
                # Для button: удаляем если unique_id не в списке правильных или имеет старый prefix
                if entity.unique_id.startswith("terrakotta_"):
                    should_remove = True
                    _LOGGER.debug(f"Datakom: Will remove button {entity.entity_id} - old terrakotta prefix")
                elif entity.unique_id not in valid_button_ids:
                    should_remove = True
                    _LOGGER.debug(f"Datakom: Will remove button {entity.entity_id} - not in valid list")
            
            if should_remove:
                _LOGGER.info(f"Datakom: Removing old entity {entity.entity_id} (unique_id={entity.unique_id})")
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
