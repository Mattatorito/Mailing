#!/usr/bin/env python3
"""
Экстренное исправление отступов в тестовых файлах
"""

import os
from pathlib import Path


def fix_test_indentation(file_path: Path) -> bool:
    """Исправляет проблемы с отступами в тестовых файлах"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        fixed_lines = []
        need_fix = False
        
        for i, line in enumerate(lines):
            # Если первая строка начинается с отступа - это ошибка
            if i == 0 and line.startswith('    '):
                # Убираем лишний отступ у всех строк
                fixed_lines = []
                for l in lines:
                    if l.startswith('    '):
                        fixed_lines.append(l[4:])  # Убираем 4 пробела
                    else:
                        fixed_lines.append(l)
                need_fix = True
                break
            else:
                fixed_lines.append(line)
        
        if need_fix:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(fixed_lines)
            return True
        
        return False
        
    except Exception as e:
        print(f"Ошибка при исправлении {file_path}: {e}")
        return False


def main():
    """Основная функция"""
    project_root = Path("/Users/alexandr/Desktop/Projects/Scripts/Mailing")
    test_dir = project_root / "tests"
    
    print("🔧 Экстренное исправление отступов в тестах...")
    
    fixed_count = 0
    
    for test_file in test_dir.glob("*.py"):
        if fix_test_indentation(test_file):
            print(f"✅ {test_file.name}: исправлены отступы")
            fixed_count += 1
    
    print(f"\n🎉 Исправлено файлов: {fixed_count}")


if __name__ == "__main__":
    main()