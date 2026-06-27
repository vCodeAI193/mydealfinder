"""Alert notification channels (F028 email, F030 webhook).

A `Notifier` turns a triggered alert into a delivered message. The default
`ChannelNotifier` routes by the alert's `channel`, falling back to logging when
a channel is not configured, so the app always degrades gracefully.
"""
import asyncio
import json
import smtplib
import urllib.request
from email.message import EmailMessage

from app.core.config import Settings, get_settings
from app.domain.models import Alert


def build_message(alert: Alert, current_price: float | None) -> str:
    """Human-readable notification body shared by every channel."""
    if alert.alert_type == "restock":
        return f"Good news! Product {alert.product_id} is back in stock."
    threshold = alert.effective_threshold
    return (
        f"Price drop! Product {alert.product_id} is now {current_price} {alert.currency} "
        f"(your target was {threshold} {alert.currency})."
    )


class AlertNotifier:
    """Base notifier. The default behaviour logs to stdout."""

    async def notify(self, alert: Alert, current_price: float | None) -> None:
        print(f"[ALERT] {alert.email}: {build_message(alert, current_price)}")

    async def notify_digest(self, email: str, lines: list[str]) -> None:
        joined = "\n".join(f" - {line}" for line in lines)
        print(f"[DIGEST] {email}:\n{joined}")


class LogNotifier(AlertNotifier):
    """Explicit log-only notifier (same as the base)."""


class EmailNotifier(AlertNotifier):
    """Send notifications over SMTP (F028); falls back to logging if unconfigured."""

    def __init__(self, settings: Settings) -> None:
        self._s = settings

    def _send_sync(self, to: str, subject: str, body: str) -> None:
        msg = EmailMessage()
        msg["From"] = self._s.smtp_from
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        with smtplib.SMTP(self._s.smtp_host, self._s.smtp_port, timeout=10) as server:
            if self._s.smtp_use_tls:
                server.starttls()
            if self._s.smtp_user:
                server.login(self._s.smtp_user, self._s.smtp_password or "")
            server.send_message(msg)

    async def _send(self, to: str, subject: str, body: str) -> None:
        if not self._s.email_enabled:
            print(f"[EMAIL:log] {to} | {subject} | {body}")
            return
        # smtplib is blocking; run it off the event loop.
        await asyncio.get_event_loop().run_in_executor(
            None, self._send_sync, to, subject, body
        )

    async def notify(self, alert: Alert, current_price: float | None) -> None:
        await self._send(alert.email, "MyDealFinder price alert", build_message(alert, current_price))

    async def notify_digest(self, email: str, lines: list[str]) -> None:
        body = "Here are your MyDealFinder alerts:\n\n" + "\n".join(f" - {ln}" for ln in lines)
        await self._send(email, "Your MyDealFinder alert digest", body)


class WebhookNotifier(AlertNotifier):
    """POST a JSON payload to the alert's webhook URL (F030)."""

    def _post_sync(self, url: str, payload: dict) -> None:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}, method="POST"
        )
        urllib.request.urlopen(req, timeout=10).close()

    async def _post(self, url: str, payload: dict) -> None:
        try:
            await asyncio.get_event_loop().run_in_executor(None, self._post_sync, url, payload)
        except Exception as exc:  # delivery failures must not break alert evaluation
            print(f"[WEBHOOK:error] {url}: {exc}")

    async def notify(self, alert: Alert, current_price: float | None) -> None:
        if not alert.webhook_url:
            print(f"[WEBHOOK:log] (no url) {build_message(alert, current_price)}")
            return
        await self._post(
            alert.webhook_url,
            {
                "product_id": alert.product_id,
                "type": alert.alert_type,
                "price": current_price,
                "currency": alert.currency,
                "message": build_message(alert, current_price),
            },
        )

    async def notify_digest(self, email: str, lines: list[str]) -> None:
        print(f"[WEBHOOK:digest:log] {email}: {lines}")


class ChannelNotifier(AlertNotifier):
    """Route to the right channel based on `alert.channel`."""

    def __init__(self, settings: Settings | None = None) -> None:
        s = settings or get_settings()
        self._email = EmailNotifier(s)
        self._webhook = WebhookNotifier()

    def _for(self, alert: Alert) -> AlertNotifier:
        return self._webhook if alert.channel == "webhook" else self._email

    async def notify(self, alert: Alert, current_price: float | None) -> None:
        await self._for(alert).notify(alert, current_price)

    async def notify_digest(self, email: str, lines: list[str]) -> None:
        await self._email.notify_digest(email, lines)
