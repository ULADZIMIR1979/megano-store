#!/usr/bin/env python
"""
Скрипт для очистки устаревших файлов в папке media.
Этот скрипт находит файлы в папке media, которые не связаны с объектами в базе данных.
"""

import os
import sys
from pathlib import Path

# Добавляем директорию проекта в путь Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Устанавливаем настройки Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

from django.conf import settings
from products.models import Category, ProductImage
from users.models import User
from django.core.files.storage import default_storage


def find_orphaned_files():
    """Находит файлы в папке media, которые не связаны с объектами в базе данных"""
    
    # Получаем все используемые файлы из базы данных
    used_files = set()
    
    # Файлы из категорий
    for category in Category.objects.all():
        if category.image:
            used_files.add(category.image.name)
    
    # Файлы из изображений товаров
    for product_image in ProductImage.objects.all():
        if product_image.src:
            used_files.add(product_image.src.name)
    
    # Файлы из аватаров пользователей
    for user in User.objects.all():
        if user.avatar:
            used_files.add(user.avatar.name)
    
    # Сканируем папку media
    media_root = settings.MEDIA_ROOT
    orphaned_files = []
    
    for root, dirs, files in os.walk(media_root):
        for file in files:
            file_path = os.path.relpath(os.path.join(root, file), media_root)
            if file_path not in used_files:
                orphaned_files.append(os.path.join(root, file))
    
    return orphaned_files


def cleanup_media(dry_run=True):
    """Очищает устаревшие файлы из папки media"""
    
    orphaned_files = find_orphaned_files()
    
    if not orphaned_files:
        print("Не найдено устаревших файлов для удаления.")
        return
    
    print(f"Найдено {len(orphaned_files)} устаревших файлов:")
    for file_path in orphaned_files:
        print(f"  - {file_path}")
    
    if dry_run:
        print("\nЭто был тестовый запуск (--dry-run). Файлы не были удалены.")
        print("Для фактического удаления файлов запустите скрипт с параметром dry_run=False")
    else:
        print(f"\nУдаление {len(orphaned_files)} файлов...")
        for file_path in orphaned_files:
            try:
                os.remove(file_path)
                print(f"  Удален: {file_path}")
            except OSError as e:
                print(f"  Ошибка при удалении {file_path}: {e}")
        
        print("Удаление завершено.")


if __name__ == "__main__":
    # Для безопасности по умолчанию запускаем в режиме dry_run
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    cleanup_media(dry_run=dry_run)