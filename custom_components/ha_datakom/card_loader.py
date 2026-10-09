"""Подключение Lovelace-карточек интеграции так, чтобы они были доступны сразу после старта HA.

Карточка копируется в config/www/<domain>/ (отдаётся по /local с первых секунд старта) и регистрируется
ресурсом панелей. Без этого карточка появляется только после загрузки интеграции, и панель, открытая во время
старта HA, показывает «Custom element doesn't exist». Если ресурсы панелей в YAML-режиме или /local ещё не
отдаётся (папки www не было при старте) - карточка подключается через add_extra_js_url, как раньше.
"""
import logging
import shutil
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


def _copy_changed(src_dir: Path, dst_dir: Path, scripts: list[str]) -> None:
    dst_dir.mkdir(parents=True, exist_ok=True)
    for script in scripts:
        src, dst = src_dir / script, dst_dir / script
        if not dst.exists() or dst.read_bytes() != src.read_bytes():
            shutil.copyfile(src, dst)


def _lovelace_resources(hass: HomeAssistant):
    """Коллекция ресурсов панелей (только storage-режим), иначе None. Структура hass.data менялась между версиями HA."""
    data = hass.data.get("lovelace")
    if data is None:
        return None
    if isinstance(data, dict):
        resources, mode = data.get("resources"), data.get("resource_mode") or data.get("mode")
    else:
        resources, mode = getattr(data, "resources", None), getattr(data, "resource_mode", None)
    if mode == "yaml" or not hasattr(resources, "async_create_item"):
        return None
    return resources


async def _async_ensure_resource(resources, url: str) -> bool:
    """Создаёт ресурс или обновляет версию существующего. True - если ресурс был создан только что."""
    # async_get_info сам загружает коллекцию из хранилища (во всех версиях HA)
    await resources.async_get_info()
    path = url.split("?")[0]
    for item in resources.async_items():
        if item["url"].split("?")[0] == path:
            if item["url"] != url:
                await resources.async_update_item(item["id"], {"res_type": "module", "url": url})
            return False
    await resources.async_create_item({"res_type": "module", "url": url})
    return True


async def async_register_cards(
    hass: HomeAssistant, domain: str, src_dir: Path, scripts: list[str], static_url: str, version: str
) -> None:
    """Подключает карточки из src_dir (уже отдаваемого по static_url) через /local и ресурс панелей."""
    local_served = Path(hass.config.path("www")).is_dir()
    use_fallback = not local_served
    try:
        await hass.async_add_executor_job(_copy_changed, src_dir, Path(hass.config.path("www", domain)), scripts)
        resources = _lovelace_resources(hass)
        if resources is None:
            use_fallback = True
        else:
            for script in scripts:
                # Только что созданный ресурс открытые страницы не подхватят до перезагрузки - на этот запуск ещё и extra_js
                if await _async_ensure_resource(resources, f"/local/{domain}/{script}?v={version}"):
                    use_fallback = True
    except Exception:  # noqa: BLE001 - карточка не должна мешать загрузке интеграции
        _LOGGER.warning("%s: could not register card as a dashboard resource, using extra_js", domain, exc_info=True)
        use_fallback = True

    if use_fallback:
        for script in scripts:
            add_extra_js_url(hass, f"{static_url}/{script}?v={version}")
