from __future__ import annotations
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from mailing.logging_config import configure_logging, logger
from persistence.repository import EventRepository
import uvicorn

app = FastAPI(title="Mailing Webhook Server (Resend Only)")
repo = EventRepository()

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/events")
async def list_events(limit: int = 50):
    return repo.get_recent_events(limit=limit)

@app.post("/resend/webhook")
async def resend_webhook(req: Request):
    """Заглушка под будущие события Resend.
    Документация Resend events (beta): на момент миграции публичные вебхуки могут отличаться.
    Сейчас просто сохраняем JSON без подписи (нет спецификации подписи под рукой).
    TODO: обновить после получения точной схемы и механизма верификации.
    """
    try:
        body = await req.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    event_type = body.get('type') or body.get('event') or 'unknown'
    message_id = body.get('message_id') or body.get('id')
    recipient = body.get('to') or body.get('recipient')
    # Пока подпись не проверяется
    repo.save_event(event_type=event_type, message_id=message_id, recipient=recipient, payload=body, signature_valid=False, provider="resend")
    logger.info(f"Resend webhook placeholder stored type={event_type} recipient={recipient}")
    return JSONResponse({"stored": True, "provider": "resend", "placeholder": True})

def run():  # entry point
    configure_logging()
    uvicorn.run("mailing.webhook_server:app", host="0.0.0.0", port=8000, reload=False)

if __name__ == "__main__":
    run()
