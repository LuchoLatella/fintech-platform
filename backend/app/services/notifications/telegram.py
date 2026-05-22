"""
Servicio de notificaciones: Telegram + Email.
"""
from __future__ import annotations
from typing import Optional
import httpx
import structlog

from app.config import settings

log = structlog.get_logger()


class TelegramService:
    """
    Envía mensajes via Telegram Bot API.
    Cada usuario debe iniciar conversación con el bot y proveer su chat_id.
    """
    BASE_URL = "https://api.telegram.org/bot{token}/{method}"

    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self._http = httpx.AsyncClient(timeout=10)

    async def send_message(self, chat_id: str, text: str, parse_mode: str = "HTML") -> bool:
        """Envía un mensaje a un chat de Telegram."""
        if not self.token:
            log.warning("telegram_not_configured")
            return False
        try:
            url = self.BASE_URL.format(token=self.token, method="sendMessage")
            r = await self._http.post(url, json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True,
            })
            r.raise_for_status()
            log.info("telegram_sent", chat_id=chat_id)
            return True
        except Exception as e:
            log.error("telegram_failed", chat_id=chat_id, error=str(e))
            return False

    async def send_alert(self, chat_id: str, alert_message: str,
                          asset_symbol: Optional[str] = None,
                          signal_type: Optional[str] = None,
                          confidence: Optional[float] = None) -> bool:
        """Formatea y envía una alerta financiera."""
        emoji_map = {"buy": "🟢", "sell": "🔴", "watch": "🟡", "risk": "⚠️", "news": "📰"}
        emoji = emoji_map.get(signal_type or "", "🔔")

        lines = [f"{emoji} <b>Alerta Fintech Platform</b>"]
        if asset_symbol:
            lines.append(f"📊 Activo: <code>{asset_symbol}</code>")
        if signal_type:
            lines.append(f"📌 Señal: <b>{signal_type.upper()}</b>")
        if confidence is not None:
            lines.append(f"🎯 Confianza: <b>{confidence:.0f}%</b>")
        lines.append("")
        lines.append(alert_message)
        lines.append("")
        lines.append("<i>⚠️ No constituye asesoramiento financiero.</i>")

        return await self.send_message(chat_id, "\n".join(lines))

    async def close(self):
        await self._http.aclose()


class EmailService:
    """Envío de emails via SendGrid."""

    def __init__(self):
        self.api_key = settings.SENDGRID_KEY
        self.from_email = settings.FROM_EMAIL
        self._http = httpx.AsyncClient(timeout=15)

    async def send(self, to_email: str, subject: str, html_body: str) -> bool:
        if not self.api_key:
            log.warning("sendgrid_not_configured")
            return False
        try:
            r = await self._http.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "personalizations": [{"to": [{"email": to_email}]}],
                    "from": {"email": self.from_email, "name": "Fintech Platform"},
                    "subject": subject,
                    "content": [{"type": "text/html", "value": html_body}],
                }
            )
            r.raise_for_status()
            log.info("email_sent", to=to_email, subject=subject)
            return True
        except Exception as e:
            log.error("email_failed", to=to_email, error=str(e))
            return False

    async def send_alert_email(self, to_email: str, alert_message: str,
                                asset_symbol: Optional[str] = None,
                                signal_type: Optional[str] = None) -> bool:
        subject = f"🔔 Alerta{f' {asset_symbol}' if asset_symbol else ''} — Fintech Platform"
        color_map = {"buy": "#1D9E75", "sell": "#E24B4A", "watch": "#EF9F27"}
        color = color_map.get(signal_type or "", "#378ADD")

        html = f"""
        <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto; padding: 24px;">
          <h2 style="color: {color}; margin: 0 0 16px;">
            {'📈 Señal de compra' if signal_type == 'buy' else '📉 Señal de venta' if signal_type == 'sell' else '🔔 Alerta de mercado'}
          </h2>
          {'<p style="font-size:20px; font-weight:bold; color:#111;">' + asset_symbol + '</p>' if asset_symbol else ''}
          <p style="font-size:15px; line-height:1.6; color:#333;">{alert_message}</p>
          <hr style="border:none; border-top:1px solid #eee; margin:20px 0;">
          <p style="font-size:12px; color:#888;">
            Este mensaje es informativo y no constituye asesoramiento financiero profesional.
            Toda inversión implica riesgo de pérdida de capital.
          </p>
        </div>
        """
        return await self.send(to_email, subject, html)

    async def close(self):
        await self._http.aclose()