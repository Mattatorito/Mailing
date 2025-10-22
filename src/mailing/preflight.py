#!/usr/bin/env python3

from __future__ import annotations
from typing import List, Dict, Any
import os
from pathlib import Path
from src.mailing.config import settings


def validate_environment() -> Dict[str, Any]:
    """Проверяет окружение для запуска email кампаний."""
    
    errors = []
    warnings = []
    
    # Проверяем обязательные переменные окружения
    if not settings.resend_api_key:
        errors.append("RESEND_API_KEY is missing")
    
    if not settings.resend_from_email:
        errors.append("RESEND_FROM_EMAIL is missing")
    
    # Проверяем базу данных
    db_path = Path(settings.sqlite_db_path)
    if not db_path.parent.exists():
        warnings.append(f"Database directory doesn't exist: {db_path.parent}")
    
    # Проверяем папку с шаблонами
    templates_dir = Path(settings.templates_dir)
    if not templates_dir.exists():
        warnings.append(f"Templates directory '{settings.templates_dir}' doesn't exist")
    
    # Проверяем лимиты
    if settings.daily_limit <= 0:
        warnings.append("Daily limit is set to 0 or negative")
    
    return {
        'status': 'ok' if not errors else 'error',
        'errors': errors,
        'warnings': warnings,
        'config': {
            'api_key_set': bool(settings.resend_api_key),
            'from_email': settings.resend_from_email,
            'daily_limit': settings.daily_limit,
            'db_path': str(db_path),
            'templates_dir': settings.templates_dir
        }
    }


def check_template_exists(template_name: str) -> bool:
    """Проверяет существование шаблона."""
    # Validate against path traversal
    if '..' in template_name or template_name.startswith('/'):
        return False
        
    templates_dir = Path(settings.templates_dir).resolve()
    template_path = (templates_dir / template_name).resolve()
    
    # Ensure template path is within templates directory
    try:
        template_path.relative_to(templates_dir)
    except ValueError:
        return False
        
    return template_path.exists()


def validate_recipients_file(file_path: str) -> Dict[str, Any]:
    """Проверяет файл с получателями."""
    path = Path(file_path)
    
    if not path.exists():
        return {
            'valid': False,
            'error': f"File not found: {file_path}"
        }
    
    if not path.is_file():
        return {
            'valid': False,
            'error': f"Not a file: {file_path}"
        }
    
    # Проверяем расширение
    ext = path.suffix.lower()
    supported_formats = ['.csv', '.json', '.xlsx', '.xls']
    
    if ext not in supported_formats:
        return {
            'valid': False,
            'error': f"Unsupported format: {ext}. Supported: {supported_formats}"
        }
    
    # Проверяем размер файла
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > 100:  # 100MB limit
        return {
            'valid': False,
            'error': f"File too large: {size_mb:.1f}MB (max 100MB)"
        }
    
    return {
        'valid': True,
        'format': ext,
        'size_mb': round(size_mb, 2)
    }


def run_preflight_checks(template_name: str = None, recipients_file: str = None) -> Dict[str, Any]:
    """Запускает полную проверку перед кампанией."""
    
    results = {
        'environment': validate_environment(),
        'overall_status': 'ok'
    }
    
    # Проверяем шаблон если указан
    if template_name:
        results['template'] = {
            'name': template_name,
            'exists': check_template_exists(template_name)
        }
        if not results['template']['exists']:
            results['overall_status'] = 'error'
    
    # Проверяем файл получателей если указан
    if recipients_file:
        results['recipients'] = validate_recipients_file(recipients_file)
        if not results['recipients']['valid']:
            results['overall_status'] = 'error'
    
    # Общий статус
    if results['environment']['status'] == 'error':
        results['overall_status'] = 'error'
    
    return results


if __name__ == "__main__":
    import json
    
    # Запускаем проверки
    checks = run_preflight_checks()
    
    print("🔍 Preflight Checks")
    print("=" * 50)
    print(json.dumps(checks, indent=2, ensure_ascii=False))
    
    if checks['overall_status'] == 'ok':
        print("\nAll checks passed!")
    else:
        print("\nSome checks failed!")
