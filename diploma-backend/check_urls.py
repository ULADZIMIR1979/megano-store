import os
import sys
import django

# Укажите правильное имя вашего Django проекта
project_name = "название_вашего_проекта"  # ← ЗАМЕНИТЕ ЭТО!

# Настройка Django
sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'{project_name}.settings')

try:
    django.setup()
except Exception as e:
    print(f"Ошибка инициализации Django: {e}")
    print("\nУбедитесь, что вы указали правильное имя проекта.")
    print(f"Текущая директория: {os.getcwd()}")
    print("Содержимое директории:")
    for item in os.listdir('.'):
        if os.path.isdir(item) and os.path.exists(os.path.join(item, 'settings.py')):
            print(f"  Возможный проект: {item}/")
    sys.exit(1)

from django.urls import get_resolver, URLPattern, URLResolver

def print_urls(patterns, prefix=''):
    for pattern in patterns:
        full_path = prefix + str(pattern.pattern)
        
        # Показываем все URL, но выделяем sign-in
        if 'sign' in full_path.lower():
            print(f"🔵 SIGN-IN URL: {full_path}")
            if hasattr(pattern, 'name'):
                print(f"   Имя: {pattern.name}")
            if hasattr(pattern, 'callback'):
                print(f"   Обработчик: {pattern.callback.__module__}")
            print()
        else:
            # Можно показать все URL для отладки
            # print(f"  {full_path}")
            pass
        
        # Рекурсивно проверяем вложенные URL
        if hasattr(pattern, 'url_patterns'):
            print_urls(pattern.url_patterns, full_path)

print("=" * 50)
print("ПОИСК URL СОДЕРЖАЩИХ 'sign'")
print("=" * 50)

resolver = get_resolver()
print_urls(resolver.url_patterns)

print("=" * 50)
print("ПРОВЕРКА КОНКРЕТНОГО URL /api/sign-in/")
print("=" * 50)

# Попробуем разрешить конкретный URL
from django.urls import resolve
try:
    result = resolve('/api/sign-in/')
    print(f"✓ URL /api/sign-in/ найден!")
    print(f"  Имя: {result.url_name}")
    print(f"  Функция: {result.func}")
except:
    print("✗ URL /api/sign-in/ НЕ найден!")
    
print("\n" + "=" * 50)
