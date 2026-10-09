import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import selector
from . import DOMAIN, FUEL_DEFAULTS, _cleanup_old_entities
from .coordinator import DEFAULT_SCAN_INTERVAL, MIN_SCAN_INTERVAL, MAX_SCAN_INTERVAL
import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)



class DatakomConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Datakom."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    @staticmethod
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return DatakomOptionsFlow()

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            api_url = user_input.get("api_url", "").strip().rstrip("/")
            scan_interval = user_input.get("scan_interval", DEFAULT_SCAN_INTERVAL)
            language = user_input.get("language", "uk")
            if not api_url:
                errors["api_url"] = "required"
            elif not (MIN_SCAN_INTERVAL <= scan_interval <= MAX_SCAN_INTERVAL):
                errors["scan_interval"] = "invalid"
            else:
                self.api_url = api_url
                self.scan_interval = scan_interval
                self.language = language
                self.control_key = user_input.get("control_key", "").strip()
                # Проверяем доступность API
                url = f"{api_url}/health"
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=15) as resp:
                            data = await resp.json()
                            if not data.get("status"):
                                errors["base"] = "cannot_connect"
                except Exception as e:
                    _LOGGER.error(f"Datakom: health check error: {e}")
                    errors["base"] = "cannot_connect"
                
                if not errors:
                    return await self.async_step_params()
        
        # Автоопределение языка из настроек HA
        default_language = "uk"  # По умолчанию украинский
        if self.hass and hasattr(self.hass.config, "language"):
            ha_lang = self.hass.config.language.lower()
            if ha_lang in ["uk", "en", "ru"]:
                default_language = ha_lang
            elif ha_lang.startswith("en"):
                default_language = "en"
            elif ha_lang.startswith("ru"):
                default_language = "ru"
        
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("api_url"): str,
                vol.Required("scan_interval", default=DEFAULT_SCAN_INTERVAL): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=MIN_SCAN_INTERVAL,
                        max=MAX_SCAN_INTERVAL,
                        mode=selector.NumberSelectorMode.BOX,
                        unit_of_measurement="s",
                    )
                ),
                vol.Required("language", default=default_language): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": "uk", "label": "Українська"},
                            {"value": "en", "label": "English"},
                            {"value": "ru", "label": "Русский"},
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                # Ключ керування (X-API-Key); без нього кнопки керування не створюються
                vol.Optional("control_key", default=""): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                ),
            }),
            errors=errors,
            description_placeholders={"step": "1"},
        )

    async def async_step_params(self, user_input=None):
        errors = {}
        param_choices = {}
        # Используем язык из первого шага
        language = getattr(self, 'language', 'uk')
        url = f"{self.api_url}/dump_devm_param_names?language={language}"
        _LOGGER.debug(f"Datakom: requesting param names from {url}")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=15) as resp:
                    text = await resp.text()
                    _LOGGER.debug(f"Datakom: param_names response: {text}")
                    data = await resp.json()
                    if data.get("success") and "params" in data:
                        # Используем title (перевод) если доступен, иначе label
                        param_choices = {str(p["id"]): p.get("title") or p["label"] for p in data["params"]}
                        _LOGGER.debug(f"Datakom: param_choices formed: {len(param_choices)} parameters")
                    else:
                        _LOGGER.error(f"Datakom: param_names failed, response: {data}")
                        errors["base"] = "param_names_failed"
            except Exception as e:
                _LOGGER.error(f"Datakom: param_names request error: {e}")
                errors["base"] = "param_names_failed"
        
        if not param_choices:
            errors["base"] = "no_params_found"
            return self.async_show_form(
                step_id="params",
                data_schema=vol.Schema({
                    vol.Optional("param_ids", default=[]): cv.multi_select({})
                }),
                errors=errors
            )
        
        if user_input is not None:
            selected_params = user_input.get("param_ids", [])
            if not selected_params:
                errors["param_ids"] = "required"
            else:
                # Сохраняем все настройки
                entry_data = {
                    "api_url": self.api_url,
                    "scan_interval": self.scan_interval,
                    "language": language,
                    "param_ids": selected_params,
                    "device_name": "Datakom Device",
                    "control_key": getattr(self, "control_key", ""),
                    **FUEL_DEFAULTS,
                }
                _LOGGER.debug(f"Datakom: Creating entry with data: {entry_data}")
                return self.async_create_entry(
                    title="Datakom listener",
                    data=entry_data
                )
        
        # По умолчанию выбираем все параметры
        default_params = list(param_choices.keys())
        
        return self.async_show_form(
            step_id="params",
            data_schema=vol.Schema({
                vol.Required("param_ids", description="Select parameters", default=default_params): cv.multi_select(param_choices)
            }),
            errors=errors,
            description_placeholders={"step": "2"},
        )


class DatakomOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Datakom."""

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        _LOGGER.debug(f"Datakom Options: async_step_init called with user_input={user_input}")
        try:
            return await self.async_step_api()
        except Exception as e:
            _LOGGER.error(f"Datakom Options: Error in async_step_init: {e}", exc_info=True)
            raise

    async def async_step_api(self, user_input=None):
        """Configure API settings."""
        _LOGGER.debug(f"Datakom Options: async_step_api called with user_input={user_input}")
        errors = {}
        current_data = self.config_entry.data
        _LOGGER.debug(f"Datakom Options: current_data={current_data}")
        
        try:
            if user_input is not None:
                api_url = user_input.get("api_url", "").strip().rstrip("/")
                scan_interval = user_input.get("scan_interval", DEFAULT_SCAN_INTERVAL)
                language = user_input.get("language", "uk")
                if not api_url:
                    errors["api_url"] = "required"
                elif not (MIN_SCAN_INTERVAL <= scan_interval <= MAX_SCAN_INTERVAL):
                    errors["scan_interval"] = "invalid"
                else:
                    self.api_url = api_url
                    self.scan_interval = scan_interval
                    self.language = language
                    self.control_key = user_input.get("control_key", "").strip()
                    return await self.async_step_params()
        except Exception as e:
            _LOGGER.error(f"Datakom Options: Error in async_step_api: {e}", exc_info=True)
            errors["base"] = "unknown"
        
        _LOGGER.debug(f"Datakom Options: Showing api form with errors={errors}")
        return self.async_show_form(
            step_id="api",
            data_schema=vol.Schema({
                vol.Required("api_url", default=current_data.get("api_url", "")): str,
                vol.Required("scan_interval", default=current_data.get("scan_interval", DEFAULT_SCAN_INTERVAL)): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=MIN_SCAN_INTERVAL,
                        max=MAX_SCAN_INTERVAL,
                        mode=selector.NumberSelectorMode.BOX,
                        unit_of_measurement="s",
                    )
                ),
                vol.Required("language", default=current_data.get("language", "uk")): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": "uk", "label": "Українська"},
                            {"value": "en", "label": "English"},
                            {"value": "ru", "label": "Русский"},
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional("control_key", default=current_data.get("control_key", "")): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                ),
            }),
            errors=errors,
        )

    async def async_step_params(self, user_input=None):
        """Select parameters."""
        _LOGGER.debug(f"Datakom Options: async_step_params called with user_input={user_input}")
        errors = {}
        param_choices = {}
        current_data = self.config_entry.data
        _LOGGER.debug(f"Datakom Options: current_data={current_data}, self.api_url={self.api_url}")
        
        if not self.api_url:
            return await self.async_step_api()
        
        # Используем язык из self (установлен в __init__ или async_step_api)
        language = self.language
        url = f"{self.api_url}/dump_devm_param_names?language={language}"
        _LOGGER.debug(f"Datakom Options: requesting param names from {url}")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=15) as resp:
                    data = await resp.json()
                    if data.get("success") and "params" in data:
                        # Используем title (перевод) если доступен, иначе label
                        param_choices = {str(p["id"]): p.get("title") or p["label"] for p in data["params"]}
                    else:
                        errors["base"] = "param_names_failed"
            except Exception as e:
                _LOGGER.error(f"Datakom Options: param_names request error: {e}")
                errors["base"] = "param_names_failed"
        
        if not param_choices:
            errors["base"] = "no_params_found"
            return self.async_show_form(
                step_id="params",
                data_schema=vol.Schema({
                    vol.Optional("param_ids", default=[]): cv.multi_select({})
                }),
                errors=errors
            )
        
        if user_input is not None:
            selected_params = user_input.get("param_ids", [])
            if not selected_params:
                errors["param_ids"] = "required"
            else:
                # Оставляем только параметры, которые реально доступны
                self.param_ids = [p for p in selected_params if p in param_choices]
                return await self.async_step_fuel()
        
        return self.async_show_form(
            step_id="params",
            data_schema=vol.Schema({
                vol.Required("param_ids", default=current_data.get("param_ids", [])): cv.multi_select(param_choices)
            }),
            errors=errors,
        )

    async def async_step_fuel(self, user_input=None):
        """Fuel consumption model: Q = max(idle_rate, slope * P - offset)."""
        errors = {}
        current_data = self.config_entry.data

        if user_input is not None:
            try:
                new_data = {
                    "api_url": self.api_url,
                    "scan_interval": self.scan_interval,
                    "language": self.language,
                    "param_ids": self.param_ids,
                    "device_name": current_data.get("device_name", "Datakom Device"),
                    "control_key": getattr(self, "control_key", current_data.get("control_key", "")),
                    **{key: float(user_input[key]) for key in FUEL_DEFAULTS},
                }
                _LOGGER.debug(f"Datakom Options: Updating entry with new_data: {new_data}")
                self.hass.config_entries.async_update_entry(
                    self.config_entry, data=new_data, title="Datakom listener"
                )
                # Перезагружаем интеграцию (cleanup выполнится в async_setup_entry)
                await self.hass.config_entries.async_reload(self.config_entry.entry_id)
                return self.async_create_entry(title="", data={})
            except Exception as e:
                _LOGGER.error(f"Datakom Options: Failed to update entry: {e}")
                errors["base"] = "update_failed"

        def number(unit, step):
            return selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0, max=1000, step=step, mode=selector.NumberSelectorMode.BOX, unit_of_measurement=unit
                )
            )

        units = {
            "fuel_idle_rate": ("L/h", 0.01),
            "fuel_slope": ("L/kVAh", 0.001),
            "fuel_offset": ("L/h", 0.01),
            "fuel_reserve": ("L", 1),
        }
        return self.async_show_form(
            step_id="fuel",
            data_schema=vol.Schema({
                vol.Required(key, default=current_data.get(key, default)): number(*units[key])
                for key, default in FUEL_DEFAULTS.items()
            }),
            errors=errors,
        )
