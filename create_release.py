from pathlib import Path
import os
import sys

import shutil
import tempfile
import zipfile

#!/usr/bin/env python3
"""
Скрипт для подготовки релиза"""



def create_release():"""Создает релизную версию проекта"""
    """Выполняет create release."""
print("🚀 Подготовка релиза Professional Email Marketing Tool v1.0.0")print("=" * 60)

    # Текущая директория проекта
    project_dir = Path(__file__).parent

    # Создаем временную директорию для релиза
    with tempfile.TemporaryDirectory() as temp_dir:release_dir = Path(temp_dir) / "professional-email-marketing-tool-v1.0.0"
        release_dir.mkdir()
print("📦 Копирование файлов...")

        # Список файлов и папок для включения в релиз
        include_files = ["README.md","INSTALL.md","CHANGELOG.md","FEATURES.md","LICENSE",
            "VERSION","requirements.txt","pyproject.toml",".env.example",".gitignore",
            "run_gui.py","minimal_web_gui.py","enhanced_gui_app.py","mailing/","gui/",
            "data_loader/","templating/","validation/","persistence/","stats/","resend/",
            "samples/","tk_gui/",
        ]

        # Копируем файлы
        for item in include_files:
            src = project_dir / item
            dst = release_dir / item

            if src.exists():
                if src.is_file():print(f"  📄 {item}")
                    shutil.copy2(src, dst)
                elif src.is_dir():print(f"  📁 {item}/")
                    shutil.copytree(
                        src,
                        dst,
                        ignore = shutil.ignore_patterns("__pycache__","*.pyc","*.pyo", ".DS_Store"
                        ),
                    )
            else:print(f"  ⚠️  {item} не найден")

        # Создаем архивarchive_name = project_dir / "professional-email-marketing-tool-v1.0.0.zip"
print(f"\n📦 Создание архива: {archive_name.name}")
with zipfile.ZipFile(archive_name,"w", zipfile.ZIP_DEFLATED) as zipf:for file_path in release_dir.rglob("*"):
                if file_path.is_file():
                    arc_name = file_path.relative_to(release_dir.parent)
                    zipf.write(file_path, arc_name)
print(f"✅ Релиз создан: {archive_name}")print(f"📊 Размер архива: {archive_name.stat().st_size / 1024 / 1024:.1f} MB")
print("\n🎉 Релиз готов к продаже!")print("\n📋 Что включено:")print("  • Веб-интерфейс")print("  • Desktop GUI")print("  • CLI интерфейс")print("  • Полная документация")print("  • Примеры файлов")print("  • Все модули и зависимости")

    return archive_name

if __name__ == "__main__":
    try:
        archive_path = create_release()print(f"\n✅ Релиз сохранен: {archive_path}")
    except Exception as e:print(f"\n❌ Ошибка создания релиза: {e}")
        sys.exit(1)
