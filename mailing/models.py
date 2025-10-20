from __future__ import annotations
from typing import Any, Dict, Optional

from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Recipient:
    """Класс для работы с recipient."""
    email: str
    variables: Dict[str, Any] = field(default_factory=dict)

    def __init__(self, email: str, name: Optional[str] = None, **kwargs):
        """Create Recipient with email and optional name/variables.

        Args:
            email: Email address
            name: Optional name (stored in variables['name'])
            **kwargs: Additional variables
        """
        self.email = email
        self.variables = dict(kwargs)
        if name is not None:
            self.variables["name"] = name

    @property
    def name(self) -> Optional[str]:
        """Get name from variables"""
        return self.variables.get("name")

    def __getattr__(self, name: str) -> Any:
        """Allow access to variables as attributes"""
        if name in self.variables:
            return self.variables[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")


@dataclass
class EmailRequest:
    """Класс для работы с emailrequest."""
    to: str
    subject: str
    text_content: Optional[str] = None
    html_content: Optional[str] = None
    from_name: Optional[str] = None
    from_email: Optional[str] = None


@dataclass
class DeliveryResult:
    """Класс для работы с deliveryresult."""
    email: str
    success: bool
    status_code: int
    message_id: Optional[str] = None
    error: Optional[str] = None
    provider: Optional[str] = None  # 'resend' | 'dry-run'
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TemplateRender:
    """Класс для работы с templaterender."""
    subject: str
    body_html: str
    body_text: Optional[str] = None
