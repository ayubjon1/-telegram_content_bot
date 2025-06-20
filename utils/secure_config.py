import os
import json
import base64
import hashlib
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)


class SecureConfigManager:
    """Менеджер для работы с зашифрованной конфигурацией"""

    def __init__(self, config_file: str = "config.encrypted", password: str = None):
        self.config_file = config_file
        self.password = password or os.getenv('CONFIG_PASSWORD')
        self.salt_file = f"{config_file}.salt"

    def _generate_key(self, password: str, salt: bytes) -> bytes:
        """Генерация ключа шифрования из пароля"""
        password_bytes = password.encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        return key

    def _get_or_create_salt(self) -> bytes:
        """Получение или создание соли"""
        salt_path = Path(self.salt_file)

        if salt_path.exists():
            with open(salt_path, 'rb') as f:
                return f.read()
        else:
            salt = os.urandom(16)
            with open(salt_path, 'wb') as f:
                f.write(salt)
            return salt

    def encrypt_config(self, config_data: dict, password: str) -> bool:
        """Шифрование конфигурации"""
        try:
            # Генерируем соль и ключ
            salt = self._get_or_create_salt()
            key = self._generate_key(password, salt)
            fernet = Fernet(key)

            # Конвертируем конфиг в JSON и шифруем
            json_data = json.dumps(config_data, indent=2)
            encrypted_data = fernet.encrypt(json_data.encode())

            # Сохраняем зашифрованные данные
            with open(self.config_file, 'wb') as f:
                f.write(encrypted_data)

            logger.info(f"Конфигурация зашифрована и сохранена в {self.config_file}")
            return True

        except Exception as e:
            logger.error(f"Ошибка шифрования конфигурации: {str(e)}")
            return False

    def decrypt_config(self, password: str = None) -> dict:
        """Расшифровка конфигурации"""
        password = password or self.password

        if not password:
            raise ValueError("Пароль для расшифровки не указан")

        if not Path(self.config_file).exists():
            raise FileNotFoundError(f"Файл конфигурации {self.config_file} не найден")

        try:
            # Загружаем соль и генерируем ключ
            salt = self._get_or_create_salt()
            key = self._generate_key(password, salt)
            fernet = Fernet(key)

            # Читаем и расшифровываем данные
            with open(self.config_file, 'rb') as f:
                encrypted_data = f.read()

            decrypted_data = fernet.decrypt(encrypted_data)
            config_data = json.loads(decrypted_data.decode())

            logger.info("Конфигурация успешно расшифрована")
            return config_data

        except Exception as e:
            logger.error(f"Ошибка расшифровки конфигурации: {str(e)}")
            raise

    def create_encrypted_config_from_env(self, password: str):
        """Создание зашифрованной конфигурации из переменных окружения"""
        config_data = {
            "BOT_TOKEN": os.getenv('BOT_TOKEN'),
            "OPENAI_API_KEY": os.getenv('OPENAI_API_KEY'),
            "ADMIN_ID": int(os.getenv('ADMIN_ID', 0)),
            "NEWS_API_KEY": os.getenv('NEWS_API_KEY', ''),
            "RSS_FEEDS": os.getenv('RSS_FEEDS', '').split(',') if os.getenv('RSS_FEEDS') else [],
            "DATABASE_PATH": os.getenv('DATABASE_PATH', 'data/bot.db'),
            "OPENAI_MODEL": os.getenv('OPENAI_MODEL', 'gpt-4'),
            "MAX_TOKENS": int(os.getenv('OPENAI_MAX_TOKENS', 800)),
            "TEMPERATURE": float(os.getenv('OPENAI_TEMPERATURE', 0.7))
        }

        return self.encrypt_config(config_data, password)


class ConfigSetup:
    """Утилита для первоначальной настройки конфигурации"""

    @staticmethod
    def setup_config_interactive():
        """Интерактивная настройка конфигурации"""
        print("🔧 Настройка конфигурации Content Manager Bot")
        print("=" * 50)

        config_data = {}

        # Основные токены
        print("\n📝 Основные настройки:")
        config_data['BOT_TOKEN'] = input("Telegram Bot Token: ").strip()
        config_data['OPENAI_API_KEY'] = input("OpenAI API Key: ").strip()
        config_data['ADMIN_ID'] = int(input("Ваш Telegram ID: ").strip())

        # Дополнительные настройки
        print("\n⚙️ Дополнительные настройки:")
        config_data['NEWS_API_KEY'] = input("News API Key (опционально): ").strip()

        # RSS ленты
        print("\n📰 RSS источники (через запятую):")
        rss_input = input("RSS ленты (Enter для источников по умолчанию): ").strip()
        if rss_input:
            config_data['RSS_FEEDS'] = [url.strip() for url in rss_input.split(',')]
        else:
            config_data['RSS_FEEDS'] = [
                "https://lenta.ru/rss",
                "https://ria.ru/export/rss2/archive/index.xml",
                "https://tass.ru/rss/v2.xml"
            ]

        # OpenAI настройки
        print("\n🤖 Настройки OpenAI:")
        config_data['OPENAI_MODEL'] = input("Модель OpenAI (gpt-4): ").strip() or "gpt-4"
        config_data['MAX_TOKENS'] = int(input("Максимум токенов (800): ").strip() or "800")
        config_data['TEMPERATURE'] = float(input("Температура (0.7): ").strip() or "0.7")

        # Выбор типа сохранения
        print("\n💾 Выберите способ сохранения:")
        print("1. .env файл (рекомендуется)")
        print("2. config.json")
        print("3. Зашифрованный файл")

        choice = input("Ваш выбор (1-3): ").strip()

        if choice == "1":
            ConfigSetup._save_to_env(config_data)
        elif choice == "2":
            ConfigSetup._save_to_json(config_data)
        elif choice == "3":
            password = input("Введите пароль для шифрования: ")
            ConfigSetup._save_encrypted(config_data, password)
        else:
            print("❌ Неверный выбор, сохраняю в .env")
            ConfigSetup._save_to_env(config_data)

        # Создаем .gitignore
        ConfigSetup._create_gitignore()

        print("\n✅ Конфигурация создана успешно!")
        print("🚀 Теперь можете запустить: python main.py")

    @staticmethod
    def _save_to_env(config_data: dict):
        """Сохранение в .env файл"""
        env_content = f"""# Content Manager Bot Configuration
# НЕ ДОБАВЛЯТЬ В GIT!

BOT_TOKEN={config_data['BOT_TOKEN']}
OPENAI_API_KEY={config_data['OPENAI_API_KEY']}
ADMIN_ID={config_data['ADMIN_ID']}
NEWS_API_KEY={config_data['NEWS_API_KEY']}
RSS_FEEDS={','.join(config_data['RSS_FEEDS'])}
OPENAI_MODEL={config_data['OPENAI_MODEL']}
OPENAI_MAX_TOKENS={config_data['MAX_TOKENS']}
OPENAI_TEMPERATURE={config_data['TEMPERATURE']}
"""

        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)

        print("✅ Конфигурация сохранена в .env")

    @staticmethod
    def _save_to_json(config_data: dict):
        """Сохранение в JSON файл"""
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        print("✅ Конфигурация сохранена в config.json")

    @staticmethod
    def _save_encrypted(config_data: dict, password: str):
        """Сохранение в зашифрованном виде"""
        secure_config = SecureConfigManager()
        if secure_config.encrypt_config(config_data, password):
            print("✅ Конфигурация зашифрована и сохранена")
        else:
            print("❌ Ошибка шифрования, сохраняю в .env")
            ConfigSetup._save_to_env(config_data)

    @staticmethod
    def _create_gitignore():
        """Создание .gitignore файла"""
        gitignore_content = """# Конфигурационные файлы
.env
config.json
config.encrypted
config.encrypted.salt
keys.py

# Логи
*.log
logs/

# База данных
data/*.db
data/*.sqlite

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
.pytest_cache/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
"""

        with open('.gitignore', 'w', encoding='utf-8') as f:
            f.write(gitignore_content)

        print("✅ Создан .gitignore файл")


if __name__ == "__main__":
    # Запуск интерактивной настройки
    ConfigSetup.setup_config_interactive()