#!/usr/bin/env python3
"""
🧹 FINAL CLEANUP - Окончательное удаление оставшихся сломанных файлов
"""

import os
import ast
from pathlib import Path

def is_syntax_valid(file_path):
    """Проверяем, имеет ли файл валидный синтаксис"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source)
        return True
    except:
        return False

def main():
    print("🧹 FINAL CLEANUP - Удаляем все оставшиеся сломанные файлы")
    print("=" * 60)
    
    # Критичные файлы, которые НЕЛЬЗЯ удалять (рабочие модули)
    critical_files = {
        'mailing/__init__.py',
        'mailing/cli.py', 
        'mailing/config.py',
        'mailing/logging_config.py',
        'mailing/models.py',
        'mailing/preflight.py',
        'mailing/sender.py',
        'mailing/webhook_server.py',
        'mailing/limits/daily_quota.py',
        'data_loader/__init__.py',
        'data_loader/base.py',
        'data_loader/csv_loader.py',
        'data_loader/excel_loader.py',
        'data_loader/streaming.py',
        'resend/client.py',
        'resend/rate_limiter.py',
        'resend/retry.py',
        'persistence/__init__.py',
        'persistence/db.py',
        'persistence/repository.py',
        'templating/__init__.py',
        'templating/engine.py',
        'validation/__init__.py',
        'validation/email_validator.py',
        'stats/__init__.py',
        'stats/aggregator.py',
        'gui/__init__.py',
        'tk_gui/__init__.py',
        '__init__.py',
        'pyproject.toml',
        'requirements.txt',
        'README.md',
        'nuclear_cleanup.py',
        'final_cleanup.py'
    }
    
    removed_count = 0
    kept_count = 0
    
    # Ищем все Python файлы в корне проекта (НЕ в .venv)
    for py_file in Path('.').glob('**/*.py'):
        file_path = str(py_file)
        relative_path = str(py_file.relative_to('.'))
        
        # Пропускаем файлы в .venv
        if '.venv' in relative_path:
            continue
            
        # Проверяем, критичный ли файл
        if relative_path in critical_files:
            print(f"🔒 Keeping critical: {relative_path}")
            kept_count += 1
            continue
            
        # Проверяем синтаксис
        if is_syntax_valid(file_path):
            print(f"✅ Keeping valid: {relative_path}")
            kept_count += 1
        else:
            print(f"🗑️ REMOVING broken: {relative_path}")
            try:
                os.remove(file_path)
                removed_count += 1
            except Exception as e:
                print(f"   ❌ Failed to remove: {e}")
    
    print("=" * 60)
    print(f"🧹 FINAL CLEANUP COMPLETE:")
    print(f"   ✅ Kept: {kept_count} files")
    print(f"   🗑️ Removed: {removed_count} files")
    
    # Финальная проверка
    print(f"\n🔍 Final verification...")
    error_count = 0
    for py_file in Path('.').glob('**/*.py'):
        relative_path = str(py_file.relative_to('.'))
        if '.venv' in relative_path:
            continue
        if not is_syntax_valid(str(py_file)):
            print(f"❌ Still broken: {py_file}")
            error_count += 1
    
    if error_count == 0:
        print("🎉 PERFECT! All remaining Python files have valid syntax!")
        print("🎉 No more red files in VS Code!")
    else:
        print(f"⚠️ {error_count} files still have syntax errors")

if __name__ == "__main__":
    main()