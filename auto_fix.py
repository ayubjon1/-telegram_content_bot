#!/usr/bin/env python3
# auto_fix.py - Автоматическое исправление
import os
import subprocess
import sys

def install_dependencies():
    deps = ["aiogram==3.3.0", "aiohttp", "aiosqlite", "python-dotenv", "psutil"]
    for dep in deps:
        subprocess.check_call([sys.executable, "-m", "pip", "install", dep])

def create_directories():
    dirs = ["data", "logs", "handlers", "services", "utils", "database"]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def create_init_files():
    init_files = ["handlers/__init__.py", "services/__init__.py", "utils/__init__.py", "database/__init__.py"]
    for f in init_files:
        with open(f, "w") as file:
            file.write("# Auto-generated __init__.py\n")

if __name__ == "__main__":
    print("🔧 Автоисправление...")
    try:
        install_dependencies()
        create_directories()
        create_init_files()
        print("✅ Исправление завершено!")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
