from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from datetime import datetime

@dataclass
class Recipient:
    email: str
    variables: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EmailRequest:
    to: str
    subject: str
    text_content: Optional[str] = None
    html_content: Optional[str] = None
    from_name: Optional[str] = None
    from_email: Optional[str] = None

@dataclass
class DeliveryResult:
    email: str
    success: bool
    status_code: int
    message_id: Optional[str] = None
    error: Optional[str] = None
    provider: Optional[str] = None  # 'resend' | 'dry-run'
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class TemplateRender:
    subject: str
    body_html: str
    body_text: Optional[str] = None
