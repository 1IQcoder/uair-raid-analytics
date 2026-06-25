from __future__ import annotations

from typing import Any

import httpx

from server.config import settings


BASE_URL = "https://api.alerts.in.ua"


class AlertsUaClientError(Exception):
    pass


class AlertsUaAuthError(AlertsUaClientError):
    pass


class AlertsUaRateLimitError(AlertsUaClientError):
    pass


class AlertsUaServerError(AlertsUaClientError):
    pass


class AlertsUaClient:
    def __init__(self, token: str | None = None, timeout: float = 30.0) -> None:
        self.token = token if token is not None else settings.alerts_in_ua_token
        self.timeout = timeout

    def history_month_ago(self, oblast_uid: str) -> list[dict[str, Any]]:
        if not self.token:
            raise AlertsUaAuthError("ALERTS_IN_UA_TOKEN is not configured.")

        url = f"{BASE_URL}/v1/regions/{oblast_uid}/alerts/month_ago.json"
        headers = {"Authorization": f"Bearer {self.token}"}
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(url, headers=headers)

        if response.status_code in {401, 403}:
            raise AlertsUaAuthError("alerts.in.ua authentication failed.")
        if response.status_code == 429:
            raise AlertsUaRateLimitError("alerts.in.ua rate limit exceeded.")
        if response.status_code >= 500:
            raise AlertsUaServerError(f"alerts.in.ua server error: HTTP {response.status_code}")
        if response.status_code != 200:
            raise AlertsUaClientError(f"alerts.in.ua returned HTTP {response.status_code}")

        payload = response.json()
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            alerts = payload.get("alerts") or payload.get("data") or []
            if isinstance(alerts, list):
                return alerts
        raise AlertsUaClientError("alerts.in.ua response does not contain an alerts list.")
