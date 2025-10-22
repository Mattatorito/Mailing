from __future__ import annotations
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from typing import Dict, Any
from mailing.models import TemplateRender

class TemplateEngine:
    def __init__(self, templates_dir: str | None = None) -> None:
        self.templates_dir = templates_dir or str(Path.cwd() / 'samples')
        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )

    def render(self, template_name: str, variables: Dict[str, Any]) -> TemplateRender:
        tmpl = self.env.get_template(template_name)
        subject = variables.get('subject') or variables.get('Subject') or 'No subject'
        body_html = tmpl.render(**variables)
        return TemplateRender(subject=subject, body_html=body_html)
