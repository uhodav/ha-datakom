import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import selector
from . import DOMAIN
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
        return DatakomOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            api_url = user_input.get("api_url", "").strip().rstrip("/")
            update_interval = user_input.get("update_interval", 5)
            language = user_input.get("language", "uk")
            if not api_url:
                errors["api_url"] = "required"
            elif not (1 <= update_interval <= 60):
                errors["update_interval"] = "invalid"
            else:
                self.api_url = api_url
                self.update_interval = update_interval
                self.language = language
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
                vol.Required("update_interval", default=5): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=60,
                        mode=selector.NumberSelectorMode.SLIDER,
                        unit_of_measurement="min",
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
                    "update_interval": self.update_interval,
                    "language": language,
                    "param_ids": selected_params,
                }
                _LOGGER.debug(f"Datakom: Creating entry with data: {entry_data}")
                return self.async_create_entry(
                    title="Datakom Device",
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

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry
        self.api_url = None
        self.update_interval = None
        self.language = None

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return await self.async_step_api()

    async def async_step_api(self, user_input=None):
        """Configure API settings."""
        errors = {}
        current_data = self.config_entry.data
        
        if user_input is not None:
            api_url = user_input.get("api_url", "").strip().rstrip("/")
            update_interval = user_input.get("update_interval", 5)
            language = user_input.get("language", "uk")
            if not api_url:
                errors["api_url"] = "required"
            elif not (1 <= update_interval <= 60):
                errors["update_interval"] = "invalid"
            else:
                self.api_url = api_url
                self.update_interval = update_interval
                self.language = language
                return await self.async_step_params()
        
        return self.async_show_form(
            step_id="api",
            data_schema=vol.Schema({
                vol.Required("api_url", default=current_data.get("api_url", "")): str,
                vol.Required("update_interval", default=current_data.get("update_interval", 5)): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=60,
                        mode=selector.NumberSelectorMode.SLIDER,
                        unit_of_measurement="min",
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
            }),
            errors=errors,
            description_placeholders={"step": "1"},
        )

    async def async_step_params(self, user_input=None):
        """Select parameters."""
        errors = {}
        param_choices = {}
        current_data = self.config_entry.data
        
        if not self.api_url:
            return await self.async_step_api()
        
        # Используем язык из первого шага
        language = getattr(self, 'language', current_data.get('language', 'uk'))
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
                try:
                    # Обновляем данные конфигурации
                    new_data = {
                        "api_url": self.api_url,
                        "update_interval": self.update_interval,
                        "language": language,
                        "param_ids": selected_params,
                    }
                    _LOGGER.debug(f"Datakom Options: Updating entry with new_data: {new_data}")
                    self.hass.config_entries.async_update_entry(
                        self.config_entry, data=new_data, title="Datakom Device"
                    )
                    # Перезагружаем интеграцию для применения изменений
                    await self.hass.config_entries.async_reload(self.config_entry.entry_id)
                    return self.async_create_entry(title="", data={})
                except Exception as e:
                    _LOGGER.error(f"Datakom Options: Failed to update entry: {e}")
                    errors["base"] = "update_failed"
        
        return self.async_show_form(
            step_id="params",
            data_schema=vol.Schema({
                vol.Required("param_ids", default=current_data.get("param_ids", [])): cv.multi_select(param_choices)
            }),
            errors=errors,
            description_placeholders={"step": "2"},
        )
