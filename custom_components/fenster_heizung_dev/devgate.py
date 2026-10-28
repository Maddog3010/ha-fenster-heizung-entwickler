"""Nur Entwickler-Version: Sperre per Schlüssel und Veröffentlichen ins Hauptprojekt.

Diese Datei gehört NICHT zum Hauptprojekt. tools/release_build.py entfernt sie beim Veröffentlichen.
Der Schlüssel wird lokal per Ed25519-Signatur geprüft. Der private Schlüssel liegt nie im Code.
"""
from __future__ import annotations

import base64
import json
import logging
import re
from datetime import date
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PUBLIC_KEY = "m9WrEMIIASjVO_NtcyLG1-WGgWeOlwMzC48m5JV0qcU"
PREFIX = "FHDEV1-"
KEY_MAX = 600
DEV_REPO = "Maddog3010/ha-fenster-heizung-entwickler"
MAIN_REPO = "Maddog3010/ha-fenster-heizung"
WORKFLOW = "release.yml"
VERSION_RE = re.compile(r"^\d+(\.\d+){2,3}$")
TOKEN_RE = re.compile(r"^[A-Za-z0-9_]{20,255}$")
API = "https://api.github.com"
RAW_MAIN = f"https://raw.githubusercontent.com/{MAIN_REPO}/main/custom_components/fenster_heizung/manifest.json"


def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def verify_dev_key(key: Any, today: date | None = None) -> dict[str, Any]:
    """Prüft einen Entwickler-Schlüssel. state: ok, expired oder invalid."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    today = today or dt_util.now().date()
    bad = {"state": "invalid", "ok": False}
    if not isinstance(key, str):
        return bad
    key = key.strip()
    if not key.startswith(PREFIX) or len(key) > KEY_MAX or "." not in key:
        return bad
    try:
        body, sig = key[len(PREFIX):].split(".", 1)
        raw = _b64d(body)
        Ed25519PublicKey.from_public_bytes(_b64d(PUBLIC_KEY)).verify(_b64d(sig), raw)
        d = json.loads(raw.decode())
        until = date.fromisoformat(str(d["b"]))
        name = re.sub(r"[\x00-\x1f<>]", "", str(d.get("n") or "")).strip()[:40]
    except Exception:  # noqa: BLE001 - jede Abweichung heißt ungültig
        return bad
    out = {"ok": True, "state": "ok", "name": name, "bis": until.isoformat()}
    if until < today:
        out.update(ok=False, state="expired")
    return out


def _vt(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", v or "")[:4])


class DevGate:
    """Hält den Entwickler-Schlüssel und das Token zum Starten des Veröffentlichens."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._store = Store(hass, 1, f"{DOMAIN}_dev")
        self._d: dict[str, Any] = {"key": "", "token": ""}

    async def async_start(self) -> None:
        raw = await self._store.async_load()
        if isinstance(raw, dict):
            self._d = {"key": str(raw.get("key") or ""), "token": str(raw.get("token") or "")}

    @property
    def unlocked(self) -> bool:
        return bool(verify_dev_key(self._d["key"])["ok"])

    def status(self) -> dict[str, Any]:
        v = verify_dev_key(self._d["key"]) if self._d["key"] else {"ok": False, "state": "none"}
        return {
            "unlocked": bool(v["ok"]),
            "state": v["state"],
            "name": v.get("name", ""),
            "bis": v.get("bis", ""),
            "token_set": bool(self._d["token"]),
            "dev_repo": DEV_REPO,
            "main_repo": MAIN_REPO,
        }

    async def async_unlock(self, key: str) -> dict[str, Any]:
        v = verify_dev_key(key)
        if v["ok"]:
            self._d["key"] = key.strip()
            await self._store.async_save(self._d)
        return {**self.status(), "state": v["state"]}

    async def async_lock(self) -> dict[str, Any]:
        self._d["key"] = ""
        await self._store.async_save(self._d)
        return self.status()

    async def async_set_token(self, token: str) -> dict[str, Any]:
        token = (token or "").strip()
        if token and not TOKEN_RE.match(token):
            return {**self.status(), "error": "Token ungültig"}
        self._d["token"] = token
        await self._store.async_save(self._d)
        return self.status()

    async def _get(self, url: str, auth: bool = False) -> tuple[int, Any]:
        sess = async_get_clientsession(self.hass)
        head = {"Accept": "application/vnd.github+json", "User-Agent": "fenster-heizung-dev"}
        if auth and self._d["token"]:
            head["Authorization"] = f"Bearer {self._d['token']}"
        async with sess.get(url, headers=head, timeout=15) as r:
            try:
                data = await r.json(content_type=None)
            except Exception:  # noqa: BLE001
                data = None
            return r.status, data

    async def async_main_version(self) -> str | None:
        try:
            st, data = await self._get(RAW_MAIN)
        except Exception:  # noqa: BLE001
            return None
        return str(data.get("version")) if st == 200 and isinstance(data, dict) else None

    async def async_publish(self, version: str, changelog: str) -> dict[str, Any]:
        """Startet den Workflow im Entwickler-Repo. Der baut ohne Entwickler-Teile und lädt ins Hauptprojekt hoch."""
        version = (version or "").strip()
        changelog = (changelog or "").strip()[:4000]
        if not VERSION_RE.match(version):
            return {"ok": False, "error": "Version ungültig (z. B. 3.0.5.6)"}
        if not changelog:
            return {"ok": False, "error": "Bitte die Änderungen eintragen"}
        if not self._d["token"]:
            return {"ok": False, "error": "Kein GitHub-Token hinterlegt"}
        main = await self.async_main_version()
        if main and _vt(version) <= _vt(main):
            return {"ok": False, "error": f"Die Version muss höher sein als im Hauptprojekt ({main})"}
        sess = async_get_clientsession(self.hass)
        head = {"Accept": "application/vnd.github+json", "User-Agent": "fenster-heizung-dev", "Authorization": f"Bearer {self._d['token']}"}
        try:
            async with sess.post(
                f"{API}/repos/{DEV_REPO}/actions/workflows/{WORKFLOW}/dispatches",
                headers=head, json={"ref": "main", "inputs": {"version": version, "changelog": changelog}}, timeout=15,
            ) as r:
                if r.status == 204:
                    return {"ok": True}
                txt = (await r.text())[:160]
                _LOGGER.warning("Veröffentlichen fehlgeschlagen: %s %s", r.status, txt)
                return {"ok": False, "error": "GitHub lehnt ab (%s). Token und Rechte prüfen." % r.status}
        except Exception as err:  # noqa: BLE001
            return {"ok": False, "error": f"Keine Verbindung zu GitHub: {err}"}

    async def async_run(self) -> dict[str, Any]:
        """Zustand des letzten Veröffentlichen-Laufs mit seinen Schritten."""
        if not self._d["token"]:
            return {"run": None}
        try:
            st, data = await self._get(f"{API}/repos/{DEV_REPO}/actions/workflows/{WORKFLOW}/runs?per_page=1", True)
            runs = (data or {}).get("workflow_runs") if st == 200 and isinstance(data, dict) else None
            if not runs:
                return {"run": None, "http": st}
            r = runs[0]
            st2, jd = await self._get(f"{API}/repos/{DEV_REPO}/actions/runs/{r['id']}/jobs", True)
            steps = []
            if st2 == 200 and isinstance(jd, dict) and jd.get("jobs"):
                for s in jd["jobs"][0].get("steps", []):
                    steps.append({"name": str(s.get("name")), "status": s.get("status"), "conclusion": s.get("conclusion")})
            return {"run": {"id": r["id"], "status": r.get("status"), "conclusion": r.get("conclusion"), "created": r.get("created_at"), "url": r.get("html_url")}, "steps": steps}
        except Exception as err:  # noqa: BLE001
            return {"run": None, "error": str(err)}
