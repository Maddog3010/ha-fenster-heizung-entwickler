"""Nur Entwickler-Version: Schnittstelle der Sperre und des Veröffentlichens (nicht im Hauptprojekt)."""
from __future__ import annotations

import functools
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant

from .const import DOMAIN


def _gate(hass: HomeAssistant):
    return hass.data.get(DOMAIN, {}).get("devgate")


def gated(fn):
    """Lässt einen Befehl nur durch, wenn der Entwickler-Schlüssel freigeschaltet ist."""
    @functools.wraps(fn)
    def inner(hass, connection, msg):
        g = _gate(hass)
        if g is None or not g.unlocked:
            connection.send_error(msg["id"], "gesperrt", "Entwickler-Version gesperrt")
            return None
        return fn(hass, connection, msg)
    return inner


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/dev_status"})
@websocket_api.async_response
async def ws_dev_status(hass, connection, msg):
    g = _gate(hass)
    connection.send_result(msg["id"], g.status() if g else {"unlocked": False, "state": "none"})


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/dev_unlock", vol.Required("key"): str})
@websocket_api.require_admin
@websocket_api.async_response
async def ws_dev_unlock(hass, connection, msg):
    g = _gate(hass)
    if g is None:
        connection.send_error(msg["id"], "gesperrt", "Nicht bereit")
        return
    res = await g.async_unlock(msg["key"])
    if res["unlocked"]:
        _reload_all(hass)
    connection.send_result(msg["id"], res)


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/dev_lock"})
@websocket_api.require_admin
@websocket_api.async_response
async def ws_dev_lock(hass, connection, msg):
    g = _gate(hass)
    res = await g.async_lock() if g else {"unlocked": False}
    _reload_all(hass)
    connection.send_result(msg["id"], res)


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/dev_token", vol.Required("token"): str})
@websocket_api.require_admin
@websocket_api.async_response
async def ws_dev_token(hass, connection, msg):
    g = _gate(hass)
    if g is None or not g.unlocked:
        connection.send_error(msg["id"], "gesperrt", "Entwickler-Version gesperrt")
        return
    connection.send_result(msg["id"], await g.async_set_token(msg["token"]))


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/dev_info"})
@websocket_api.require_admin
@websocket_api.async_response
async def ws_dev_info(hass, connection, msg):
    g = _gate(hass)
    if g is None or not g.unlocked:
        connection.send_error(msg["id"], "gesperrt", "Entwickler-Version gesperrt")
        return
    run = await g.async_run()
    connection.send_result(msg["id"], {**g.status(), "main_version": await g.async_main_version(), **run})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/dev_publish",
    vol.Required("version"): str,
    vol.Required("changelog"): str,
})
@websocket_api.require_admin
@websocket_api.async_response
async def ws_dev_publish(hass, connection, msg):
    g = _gate(hass)
    if g is None or not g.unlocked:
        connection.send_error(msg["id"], "gesperrt", "Entwickler-Version gesperrt")
        return
    connection.send_result(msg["id"], await g.async_publish(msg["version"], msg["changelog"]))


def _reload_all(hass: HomeAssistant) -> None:
    """Nach Entsperren oder Sperren alle Einträge neu laden, damit Dienste und Sensoren erscheinen oder verschwinden."""
    for e in hass.config_entries.async_entries(DOMAIN):
        hass.async_create_task(hass.config_entries.async_reload(e.entry_id))


def async_register_dev_api(hass: HomeAssistant) -> None:
    for command in (ws_dev_status, ws_dev_unlock, ws_dev_lock, ws_dev_token, ws_dev_info, ws_dev_publish):
        websocket_api.async_register_command(hass, command)
