"""Client de l'API HTTP de Printr (https://github.com/XNinety9/Printr)."""

from __future__ import annotations

from typing import Any

import aiohttp


class PrintrError(Exception):
    """Erreur renvoyée par Printr ou serveur injoignable."""


class PrintrAuthError(PrintrError):
    """Jeton refusé."""


class PrintrClient:
    """Accès à un serveur `printr serve`, avec le jeton des scripts (`--token`)."""

    def __init__(self, session: aiohttp.ClientSession, url: str, token: str) -> None:
        self._session = session
        self.url = url.rstrip("/")
        self._token = token

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        timeout: float = 15,
        text: bool = False,
    ) -> Any:
        try:
            async with self._session.request(
                method,
                f"{self.url}{path}",
                json=json,
                headers={"Authorization": f"Bearer {self._token}"},
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as resp:
                if resp.status == 401:
                    raise PrintrAuthError("jeton refusé")
                if resp.status < 400 and text:
                    return await resp.text()
                try:
                    data = await resp.json(content_type=None)
                except ValueError:
                    data = None
                if resp.status >= 400:
                    message = data.get("error") if isinstance(data, dict) else None
                    raise PrintrError(message or f"HTTP {resp.status}")
                return data
        except (aiohttp.ClientError, TimeoutError) as err:
            raise PrintrError(f"Printr injoignable : {err}") from err

    async def status(self, timeout: float = 15) -> dict[str, Any]:
        return await self._request("GET", "/api/status", timeout=timeout)

    async def presets(self) -> list[dict[str, Any]]:
        return await self._request("GET", "/api/presets")

    async def shopping(self) -> list[dict[str, Any]]:
        return await self._request("GET", "/api/shopping")

    async def history(self) -> list[dict[str, Any]]:
        return await self._request("GET", "/api/history")

    async def print_ticket(self, ticket: dict[str, Any], label: str | None, timeout: float) -> list[str]:
        """Imprime un ticket ; renvoie les blocs en échec."""
        body: dict[str, Any] = {"ticket": ticket}
        if label:
            body["label"] = label
        data = await self._request("POST", "/api/print", json=body, timeout=timeout)
        return data.get("errors", [])

    async def print_preset(self, preset_id: str, timeout: float) -> list[str]:
        data = await self._request("POST", f"/api/presets/{preset_id}/print", timeout=timeout)
        return data.get("errors", [])

    async def preview(self, ticket: dict[str, Any], timeout: float) -> str:
        """Aperçu texte du ticket, sans imprimer."""
        return await self._request("POST", "/print?preview", json=ticket, timeout=timeout, text=True)

    async def add_shopping(self, text: str) -> list[dict[str, Any]]:
        return await self._request("POST", "/api/shopping", json={"text": text})

    async def remove_shopping(self, item_id: str) -> list[dict[str, Any]]:
        return await self._request("DELETE", f"/api/shopping/{item_id}")
