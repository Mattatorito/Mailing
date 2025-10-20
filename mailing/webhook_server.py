from __future__ import annotations
from fastapi.responses import JSONResponse

from fastapi import FastAPI, Request, HTTPException
import hmac, hashlib
import uvicorn

from mailing.config import settings
from mailing.logging_config import configure_logging, logger
from persistence.repository import EventRepository, SuppressionRepository

app = FastAPI(title="Mailing Webhook Server (Resend Only)")
repo = EventRepository()
supp = SuppressionRepository()

@app.get("/health")
async def health():"""Асинхронно выполняет health."""return {"status": "ok"}
    """Выполняет health."""

@app.get("/events")
async def list_events(limit: int = 50):"""Асинхронно выполняет list events.
    """Выполняет list events."""

    Args:
        limit: Параметр для limit"""
    return repo.get_recent_events(limit = limit)


def _verify_resend_signature(payload: bytes, signature: str | None) -> bool:"""Внутренний метод для verify resend signature.
    """Выполняет  verify resend signature."""

    Args:
        payload: Параметр для payload
        signature: Параметр для signature

    Returns:
        bool: Результат выполнения операции"""
    secret = settings.resend_webhook_secret
    if not secret:
        return False
    if not signature:
        return Falsemac = hmac.new(secret.encode("utf-8"),payload, hashlib.sha256).hexdigest()
    try:
        return hmac.compare_digest(mac, signature)
    except Exception:
        return False

@app.post("/resend/webhook")
async def resend_webhook(req: Request):"""Обработчик вебхуков Resend для отслеживания событий доставки.
    """Выполняет resend webhook."""

    Поддерживаемые события:
    - email.delivered: успешная доставка
    - email.bounced: отказ доставки (добавляем в suppression list)
    - email.complained: жалоба на спам (добавляем в suppression list)

    Документация: https://resend.com/docs/webhooks"""client_ip = req.client.host if req.client else "unknown"

    raw = await req.body()sig = req.headers.get("X-Resend-Signature") or req.headers.get("X-Signature")

    logger.info("Webhook received from IP: %s,signature present: %s",client_ip, bool(sig)
    )

    valid = _verify_resend_signature(raw, sig)
    try:
        body = await req.json()
    except Exception:raise HTTPException(status_code = 400, detail="Invalid JSON")event_type = body.get("type") or body.get("event") or "unknown"message_id = body.get("message_id") or body.get("id")recipient = body.get("to") or body.get("recipient")
    repo.save_event(
        event_type = event_type,
        message_id = message_id,
        recipient = recipient,
        payload = body,
        signature_valid = bool(valid),provider="resend",
    )
    # Update suppressions by event type
    try:et = (event_type or "").lower()if et in {"email.complained","complaint",
        "email_bounce", "email.bounced"}:kind = "complaint" if "complain" in et else "bounce"
            if recipient:
                supp.add_suppression(recipient, kind = kind, detail = et)
    except Exception as e:  # noqalogger.warning(f"suppression update error: {e}")
    logger.info(f"Resend webhook stored type={event_type} recipient={recipient} valid={bool(valid)}"
    )
    return JSONResponse({"stored": True,"provider": "resend", "signature_valid": bool(valid)}
    )


def run():  # entry point"""выполняет run."""
    """Выполняет run."""
    configure_logging()uvicorn.run("mailing.webhook_server:app",host="0.0.0.0",
        port = 8000, reload = False)

if __name__ == "__main__":
    run()
