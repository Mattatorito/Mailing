# API Documentation - Professional Email Marketing Tool

## Overview

Professional Email Marketing Tool предоставляет REST API для управления email кампаниями и обработки webhook событий от email провайдеров.

## Base URL

```
http://localhost:8080  # Development
https://your-domain.com  # Production
```

## Authentication

В настоящее время API не требует аутентификации для basic endpoints. Webhook endpoints защищены секретным ключом.

## Endpoints

### Health Check

Проверка состояния сервиса.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-20T10:30:00Z",
  "version": "1.0.0",
  "environment": "production"
}
```

**Status Codes:**
- `200` - Сервис работает нормально
- `503` - Сервис недоступен

**Example:**
```bash
curl -X GET http://localhost:8080/health
```

---

### Root Endpoint

Информация о сервисе.

**Endpoint:** `GET /`

**Response:**
```json
{
  "service": "Professional Email Marketing Tool",
  "version": "1.0.0",
  "description": "Webhook server for processing email delivery events",
  "endpoints": [
    "/health",
    "/webhook/resend"
  ],
  "documentation": "/api/docs"
}
```

**Example:**
```bash
curl -X GET http://localhost:8080/
```

---

### Resend Webhook

Обработка webhook событий от Resend.

**Endpoint:** `POST /webhook/resend`

**Headers:**
```
Content-Type: application/json
Resend-Signature: <webhook_signature>
```

**Request Body:**
```json
{
  "type": "email.delivered",
  "created_at": "2024-01-20T10:30:00.000Z",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "object": "email",
    "to": ["recipient@example.com"],
    "from": "sender@example.com",
    "subject": "Test Email",
    "html": "<h1>Hello World</h1>",
    "text": "Hello World",
    "delivered_at": "2024-01-20T10:30:05.000Z"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Event processed successfully",
  "event_id": "evt_123456789"
}
```

**Event Types:**
- `email.sent` - Email отправлен
- `email.delivered` - Email доставлен
- `email.delivery_delayed` - Доставка задержана
- `email.complained` - Жалоба на спам
- `email.bounced` - Email отклонен
- `email.clicked` - Клик по ссылке
- `email.opened` - Email открыт

**Status Codes:**
- `200` - Событие обработано успешно
- `400` - Неверный формат запроса
- `401` - Неверная подпись webhook
- `500` - Внутренняя ошибка сервера

**Example:**
```bash
curl -X POST http://localhost:8080/webhook/resend \
  -H "Content-Type: application/json" \
  -H "Resend-Signature: your_signature" \
  -d '{
    "type": "email.delivered",
    "created_at": "2024-01-20T10:30:00.000Z",
    "data": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "to": ["recipient@example.com"],
      "delivered_at": "2024-01-20T10:30:05.000Z"
    }
  }'
```

---

## Error Handling

API использует стандартные HTTP коды ошибок и возвращает JSON с описанием ошибки.

**Error Response Format:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request format",
    "details": {
      "field": "email",
      "issue": "Email format is invalid"
    }
  },
  "timestamp": "2024-01-20T10:30:00Z"
}
```

**Common Error Codes:**
- `400` Bad Request - Неверный формат запроса
- `401` Unauthorized - Неверная аутентификация
- `404` Not Found - Endpoint не найден
- `422` Unprocessable Entity - Ошибка валидации
- `429` Too Many Requests - Превышен лимит запросов
- `500` Internal Server Error - Внутренняя ошибка

---

## Webhook Security

### Signature Verification

Все webhook запросы подписываются секретным ключом. Для верификации:

1. Получите signature из заголовка `Resend-Signature`
2. Вычислите HMAC-SHA256 от тела запроса используя ваш webhook secret
3. Сравните полученную подпись с отправленной

**Python Example:**
```python
import hmac
import hashlib

def verify_signature(payload: str, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)
```

---

## Rate Limiting

API применяет rate limiting для защиты от злоупотреблений:

- **Health Check**: 100 запросов/минуту
- **Webhook Endpoints**: 1000 запросов/минуту
- **General API**: 500 запросов/минуту

При превышении лимита возвращается код `429` с заголовками:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1642680000
```

---

## Monitoring & Metrics

### Health Metrics

Endpoint `/health` предоставляет расширенную информацию о состоянии системы:

```json
{
  "status": "healthy",
  "checks": {
    "database": "healthy",
    "email_service": "healthy",
    "disk_space": "healthy"
  },
  "metrics": {
    "uptime": "24h 15m 30s",
    "requests_total": 15432,
    "requests_per_second": 12.5,
    "error_rate": 0.02
  }
}
```

---

## OpenAPI Specification

Полная OpenAPI спецификация доступна по адресу:
```
GET /api/openapi.json
```

Swagger UI доступен по адресу:
```
GET /api/docs
```

---

## Examples

### Complete Integration Example

```python
import asyncio
import aiohttp
from typing import Dict, Any

class EmailMarketingAPI:
    def __init__(self, base_url: str, webhook_secret: str):
        self.base_url = base_url
        self.webhook_secret = webhook_secret
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверка состояния API."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/health") as response:
                return await response.json()
    
    async def process_webhook(self, payload: Dict[str, Any], signature: str) -> bool:
        """Обработка webhook события."""
        # Verify signature here
        if not self._verify_signature(payload, signature):
            return False
        
        # Process event
        event_type = payload.get('type')
        if event_type == 'email.delivered':
            await self._handle_delivery(payload['data'])
        elif event_type == 'email.bounced':
            await self._handle_bounce(payload['data'])
        
        return True
    
    def _verify_signature(self, payload: Dict[str, Any], signature: str) -> bool:
        # Implementation here
        pass
    
    async def _handle_delivery(self, data: Dict[str, Any]):
        print(f"Email delivered to {data.get('to')}")
    
    async def _handle_bounce(self, data: Dict[str, Any]):
        print(f"Email bounced for {data.get('to')}")

# Usage
async def main():
    api = EmailMarketingAPI("http://localhost:8080", "your-secret")
    health = await api.health_check()
    print(f"API Status: {health['status']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### cURL Examples

```bash
# Health check
curl -X GET http://localhost:8080/health

# Get service info
curl -X GET http://localhost:8080/

# Process webhook event
curl -X POST http://localhost:8080/webhook/resend \
  -H "Content-Type: application/json" \
  -H "Resend-Signature: $(echo -n '{"type":"email.delivered"}' | openssl dgst -sha256 -hmac 'your-secret' -binary | base64)" \
  -d '{"type":"email.delivered","data":{"id":"123","to":["test@example.com"]}}'
```

---

## SDK Examples

### JavaScript/Node.js

```javascript
const crypto = require('crypto');
const axios = require('axios');

class EmailMarketingClient {
  constructor(baseUrl, webhookSecret) {
    this.baseUrl = baseUrl;
    this.webhookSecret = webhookSecret;
  }

  async healthCheck() {
    const response = await axios.get(`${this.baseUrl}/health`);
    return response.data;
  }

  verifyWebhookSignature(payload, signature) {
    const expectedSignature = crypto
      .createHmac('sha256', this.webhookSecret)
      .update(JSON.stringify(payload))
      .digest('hex');
    
    return crypto.timingSafeEqual(
      Buffer.from(signature),
      Buffer.from(expectedSignature)
    );
  }
}
```

### PHP

```php
class EmailMarketingClient {
    private $baseUrl;
    private $webhookSecret;

    public function __construct($baseUrl, $webhookSecret) {
        $this->baseUrl = $baseUrl;
        $this->webhookSecret = $webhookSecret;
    }

    public function healthCheck() {
        $response = file_get_contents($this->baseUrl . '/health');
        return json_decode($response, true);
    }

    public function verifyWebhookSignature($payload, $signature) {
        $expectedSignature = hash_hmac('sha256', $payload, $this->webhookSecret);
        return hash_equals($signature, $expectedSignature);
    }
}
```

---

## Troubleshooting

### Common Issues

1. **Webhook signature verification fails**
   - Проверьте правильность webhook secret
   - Убедитесь что используете raw body для вычисления подписи
   - Проверьте кодировку (UTF-8)

2. **Rate limiting errors**
   - Реализуйте exponential backoff
   - Кэшируйте результаты где возможно
   - Мониторьте заголовки rate limit

3. **Connection timeouts**
   - Увеличьте timeout значения
   - Реализуйте retry logic
   - Проверьте сетевую связность

### Debug Mode

Для включения отладочного режима установите переменную окружения:
```bash
export DEBUG=true
export LOG_LEVEL=debug
```

Это активирует подробное логирование всех запросов и ответов.