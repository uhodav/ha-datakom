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
            if not api_url:
                errors["api_url"] = "required"
            elif not (2 <= update_interval <= 10):
                errors["update_interval"] = "invalid"
            else:
                self.api_url = api_url
                self.update_interval = update_interval
                return await self.async_step_device()
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
            }),
            errors=errors,
            description_placeholders={"step": "1"},
        )

    async def async_step_device(self, user_input=None):
        errors = {}
        node_list = []
        # Запрос к /node_list для получения списка нодов
        url = f"{self.api_url}/node_list"
        _LOGGER.debug(f"Datakom: requesting node list from {url}")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=15) as resp:
                    text = await resp.text()
                    _LOGGER.debug(f"Datakom: node_list response: {text}")
                    data = await resp.json()
                    if data.get("success") and "NodeList" in data.get("data", {}):
                        node_list = data["data"]["NodeList"]
                    else:
                        _LOGGER.error(f"Datakom: node_list failed, response: {data}")
                        errors["base"] = "node_list_failed"
            except Exception as e:
                _LOGGER.error(f"Datakom: node_list request error: {e}")
                errors["base"] = "node_list_failed"
        
        if not node_list:
            errors["base"] = "no_nodes_found"
            return self.async_show_form(
                step_id="device",
                data_schema=vol.Schema({}),
                errors=errors
            )
        
        # Используем первую ноду или сохраненную
        node_id = node_list[0]["id"] if node_list else None
        if not node_id:
            errors["base"] = "no_nodes_found"
            return self.async_show_form(
                step_id="device",
                data_schema=vol.Schema({}),
                errors=errors
            )
        
        self.node_id = node_id
        
        # Запрос к /devx_list для получения устройств ноды
        device_list = []
        url = f"{self.api_url}/devx_list?node_id={node_id}"
        _LOGGER.debug(f"Datakom: requesting device list from {url}")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=15) as resp:
                    text = await resp.text()
                    _LOGGER.debug(f"Datakom: devx_list response: {text}")
                    data = await resp.json()
                    if data.get("success") and "DevxList" in data.get("data", {}):
                        device_list = data["data"]["DevxList"]
                    else:
                        _LOGGER.error(f"Datakom: devx_list failed, response: {data}")
                        errors["base"] = "device_list_failed"
            except Exception as e:
                _LOGGER.error(f"Datakom: devx_list request error: {e}")
                errors["base"] = "device_list_failed"
        
        device_choices = {str(dev["did"]): dev.get("sid", dev.get("device_type", str(dev["did"]))) for dev in device_list}
        
        if not device_choices:
            errors["base"] = "device_list_failed"
            return self.async_show_form(
                step_id="device",
                data_schema=vol.Schema({}),
                errors=errors
            )
        
        if user_input is not None:
            did = user_input.get("device_id")
            if not did:
                errors["device_id"] = "required"
            else:
                self.did = did
                self.device_name = device_choices.get(did, did)
                return await self.async_step_params()
        return self.async_show_form(
            step_id="device",
            data_schema=vol.Schema({
                vol.Required("device_id", description="step2_device_id"): vol.In(device_choices)
            }),
            errors=errors,
            description_placeholders={"step": "2"}
        )

    async def async_step_params(self, user_input=None):
        errors = {}
        param_choices = {}
        # Логируем актуальный api_url
        _LOGGER.debug(f"Datakom: async_step_params using api_url: {getattr(self, 'api_url', None)}, node_id: {getattr(self, 'node_id', None)}, did: {getattr(self, 'did', None)}")
        url = f"{self.api_url}/dump_devm_param_names?did={self.did}&node_id={self.node_id}"
        _LOGGER.debug(f"Datakom: requesting param names from {url}")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=15) as resp:
                    text = await resp.text()
                    _LOGGER.debug(f"Datakom: param_names response: {text}")
                    data = await resp.json()
                    # Логируем формирование param_choices
                    _LOGGER.debug(f"Datakom: forming param_choices from data['params']: {data.get('params')}")
                    if data.get("success") and "params" in data:
                        param_choices = {str(p["id"]): p["label"] for p in data["params"]}
                        _LOGGER.debug(f"Datakom: param_choices formed: {param_choices}")
                    else:
                        _LOGGER.error(f"Datakom: param_names failed, response: {data}")
                        errors["base"] = "param_names_failed"
            except Exception as e:
                _LOGGER.error(f"Datakom: param_names request error: {e}")
                errors["base"] = "param_names_failed"
        # Логируем финальный param_choices перед формой
        _LOGGER.debug(f"Datakom: param_choices before form: {param_choices}")
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
                _LOGGER.debug(f"Datakom: Saving config with node_id={getattr(self, 'node_id', None)}, did={getattr(self, 'did', None)}")
                entry_data = {
                    "api_url": self.api_url,
                    "update_interval": self.update_interval,
                    "node_id": self.node_id,
                    "device_id": self.did,
                    "device_name": self.device_name,
                    "param_ids": selected_params,
                }
                _LOGGER.debug(f"Datakom: entry_data = {entry_data}")
                return self.async_create_entry(
                    title=self.device_name,
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
            description_placeholders={"step": "3"},
        )


class DatakomOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Datakom."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.api_url = None
        self.update_interval = None
        self.node_id = None
        self.did = None
        self.device_name = None

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
            if not api_url:
                errors["api_url"] = "required"
            elif not (2 <= update_interval <= 10):
                errors["update_interval"] = "invalid"
            else:
                self.api_url = api_url
                self.update_interval = update_interval
                return await self.async_step_device()
        
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
            }),
            errors=errors,
            description_placeholders={"step": "1"},
        )

    async def async_step_device(self, user_input=None):
        """Select device."""
        errors = {}
        node_list = []
        current_data = self.config_entry.data
        
        if not self.api_url:
            return await self.async_step_api()
        
        # Запрос к /node_list
        url = f"{self.api_url}/node_list"
        _LOGGER.debug(f"Datakom Options: requesting node list from {url}")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=15) as resp:
                    data = await resp.json()
                    if data.get("success") and "NodeList" in data.get("data", {}):
                        node_list = data["data"]["NodeList"]
                    else:
                        errors["base"] = "node_list_failed"
            except Exception as e:
                _LOGGER.error(f"Datakom Options: node_list request error: {e}")
                errors["base"] = "node_list_failed"
        
        if not node_list:
            errors["base"] = "no_nodes_found"
            return self.async_show_form(
                step_id="device",
                data_schema=vol.Schema({}),
                errors=errors
            )
        
        node_id = node_list[0]["id"] if node_list else None
        if not node_id:
            errors["base"] = "no_nodes_found"
            return self.async_show_form(
                step_id="device",
                data_schema=vol.Schema({}),
                errors=errors
            )
        
        self.node_id = node_id
        
        # Запрос к /devx_list
        device_list = []
        url = f"{self.api_url}/devx_list?node_id={node_id}"
        _LOGGER.debug(f"Datakom Options: requesting device list from {url}")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=15) as resp:
                    data = await resp.json()
                    if data.get("success") and "DevxList" in data.get("data", {}):
                        device_list = data["data"]["DevxList"]
                    else:
                        errors["base"] = "device_list_failed"
            except Exception as e:
                _LOGGER.error(f"Datakom Options: devx_list request error: {e}")
                errors["base"] = "device_list_failed"
        
        device_choices = {str(dev["did"]): dev.get("sid", dev.get("device_type", str(dev["did"]))) for dev in device_list}
        
        if user_input is not None:
            did = user_input.get("device_id")
            if not did:
                errors["device_id"] = "required"
            else:
                self.did = did
                self.device_name = device_choices.get(did, did)
                return await self.async_step_params()
        
        return self.async_show_form(
            step_id="device",
            data_schema=vol.Schema({
                vol.Required("device_id", default=current_data.get("device_id", "")): vol.In(device_choices)
            }),
            errors=errors,
            description_placeholders={"step": "2"}
        )

    async def async_step_params(self, user_input=None):
        """Select parameters."""
        errors = {}
        param_choices = {}
        current_data = self.config_entry.data
        
        if not self.api_url or not self.did:
            return await self.async_step_api()
        
        url = f"{self.api_url}/dump_devm_param_names?did={self.did}&node_id={self.node_id}"
        _LOGGER.debug(f"Datakom Options: requesting param names from {url}")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=15) as resp:
                    data = await resp.json()
                    if data.get("success") and "params" in data:
                        param_choices = {str(p["id"]): p["label"] for p in data["params"]}
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
                        "node_id": self.node_id,
                        "device_id": self.did,
                        "device_name": self.device_name,
                        "param_ids": selected_params,
                    }
                    _LOGGER.debug(f"Datakom Options: Updating entry with new_data: {new_data}")
                    self.hass.config_entries.async_update_entry(
                        self.config_entry, data=new_data, title=self.device_name
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
            description_placeholders={"step": "3"},
        )
