import asyncio
import json
from typing import Any

import httpx


class HermesClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {"X-API-Key": api_key, "Content-Type": "application/json"}

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.request(
                method,
                f"{self.base_url}{path}",
                headers=self.headers,
                **kwargs,
            )
            if resp.status_code >= 400:
                try:
                    detail = resp.json().get("error") or resp.text
                except ValueError:
                    detail = resp.text
                raise HermesError(resp.status_code, str(detail)[:300])
            return resp.json() if resp.content else {}

    async def list_sessions(self) -> list:
        data = await self._request("GET", "/api/sessions")
        return data.get("sessions") or []

    async def create_session(self, name: str) -> str:
        data = await self._request("POST", "/api/sessions", json={"name": name})
        return data["id"]

    async def set_webhook(self, session_id: str, url: str) -> dict:
        return await self._request("POST", f"/api/sessions/{session_id}/webhook", json={"url": url})

    async def pair_code(self, session_id: str, phone: str) -> str:
        data = await self._request(
            "POST",
            f"/api/sessions/{session_id}/pair-code",
            json={"phone": phone},
        )
        return data.get("code", "")

    async def logout(self, session_id: str) -> dict:
        return await self._request("POST", f"/api/sessions/{session_id}/logout")

    async def get_settings(self) -> dict:
        return await self._request("GET", "/api/settings")

    async def send_text(self, session_id: str, to: str, text: str) -> dict:
        return await self._request(
            "POST",
            f"/api/sessions/{session_id}/messages/text",
            json={"to": to, "text": text},
        )

    async def send_image(
        self, session_id: str, to: str, url: str = "", base64: str = "", caption: str = ""
    ) -> dict:
        body: dict[str, Any] = {"to": to}
        if url:
            body["url"] = url
        if base64:
            body["base64"] = base64
        if caption:
            body["caption"] = caption
        return await self._request(
            "POST",
            f"/api/sessions/{session_id}/messages/image",
            json=body,
        )

    async def send_document(
        self, session_id: str, to: str, url: str = "", base64: str = "", filename: str = ""
    ) -> dict:
        body: dict[str, Any] = {"to": to}
        if url:
            body["url"] = url
        if base64:
            body["base64"] = base64
        if filename:
            body["filename"] = filename
        return await self._request(
            "POST",
            f"/api/sessions/{session_id}/messages/document",
            json=body,
        )

    async def start_qr(self, session_id: str, timeout: float = 25) -> str:
        """Reinicia o pareamento por QR e devolve o primeiro QR (vale ~60 s). O QR só chega pelo SSE do Hermes."""
        async def run() -> str:
            async with httpx.AsyncClient(timeout=httpx.Timeout(timeout, connect=10)) as client:
                async with client.stream("GET", f"{self.base_url}/api/events",
                                         headers={"X-API-Key": self.api_key, "Accept": "text/event-stream"}) as resp:
                    if resp.status_code >= 400:
                        raise HermesError(resp.status_code, (await resp.aread()).decode(errors="replace")[:300])
                    await self._request("POST", f"/api/sessions/{session_id}/pair")
                    async for line in resp.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        try:
                            ev = json.loads(line[6:])
                        except ValueError:
                            continue
                        if isinstance(ev, dict) and ev.get("sessionId") == session_id and ev.get("qr"):
                            return ev["qr"]
            raise HermesError(504, "o Hermes não mandou o QR")
        try:
            return await asyncio.wait_for(run(), timeout)
        except asyncio.TimeoutError:
            raise HermesError(504, "o Hermes não mandou o QR a tempo")

    async def send_poll(self, session_id: str, to: str, name: str, options: list[str]) -> dict:
        return await self._request(
            "POST",
            f"/api/sessions/{session_id}/messages/poll",
            json={"to": to, "name": name, "options": options, "multipleAnswers": False},
        )

    async def send_buttons(self, session_id: str, to: str, text: str, options: list[str]) -> dict:
        """Botões clicáveis (até 3). O id de cada botão é o próprio texto, que volta em `buttonReply`."""
        return await self._request(
            "POST",
            f"/api/sessions/{session_id}/messages/buttons",
            json={"to": to, "text": text, "buttons": [{"id": o, "text": o} for o in options]},
        )

    async def typing(self, session_id: str, to: str, on: bool = True) -> dict:
        return await self._request(
            "POST",
            f"/api/sessions/{session_id}/messages/typing",
            json={"to": to, "typing": on},
        )

    async def contact_info(self, session_id: str, jid: str) -> dict:
        return await self._request("GET", f"/api/sessions/{session_id}/contacts/{jid}")

    async def check_number(self, session_id: str, phone: str) -> dict:
        return await self._request(
            "GET",
            f"/api/sessions/{session_id}/contacts/check",
            params={"phone": phone},
        )

    async def get_session_info(self, session_id: str) -> dict:
        for s in await self.list_sessions():
            if s.get("id") == session_id:
                return s
        return {}

    async def chat_messages(self, session_id: str, chat_id: str, limit: int = 20) -> list[dict]:
        """Últimas mensagens do chat guardadas no Hermes, da mais nova para a mais antiga
        (campos `id`, `fromMe`, `type`, `body`, `timestamp`)."""
        data = await self._request("GET", f"/api/sessions/{session_id}/chats/{chat_id}/messages",
                                   params={"limit": limit})
        return data if isinstance(data, list) else []


class HermesError(Exception):
    def __init__(self, status: int, detail: str):
        super().__init__(f"Hermes {status}: {detail}")
        self.status = status
        self.detail = detail
