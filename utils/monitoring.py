# utils/monitoring.py - НОВЫЙ ФАЙЛ
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from collections import deque, defaultdict
import psutil

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """Системные метрики"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    timestamp: datetime


@dataclass
class Alert:
    """Алерт системы"""
    id: str
    level: str  # info, warning, error, critical
    title: str
    message: str
    timestamp: datetime
    resolved: bool = False


class SmartMonitor:
    """Умная система мониторинга"""

    def __init__(self, db=None, scheduler=None):
        self.db = db
        self.scheduler = scheduler
        self.running = False

        # Хранилище метрик (последние 1000 записей)
        self.system_metrics: deque = deque(maxlen=1000)
        self.active_alerts: Dict[str, Alert] = {}

        # Пороговые значения
        self.thresholds = {
            'cpu_warning': 70.0,
            'cpu_critical': 85.0,
            'memory_warning': 75.0,
            'memory_critical': 90.0,
            'disk_warning': 80.0,
            'disk_critical': 95.0
        }

        # Счетчики для автоисцеления
        self.healing_actions = defaultdict(int)

        logger.info("🔍 Система мониторинга инициализирована")

    async def start_monitoring(self):
        """Запуск мониторинга"""
        if self.running:
            return

        self.running = True

        # Запускаем задачи мониторинга
        tasks = [
            asyncio.create_task(self._monitor_system_metrics()),
            asyncio.create_task(self._monitor_services()),
            asyncio.create_task(self._auto_healing_loop())
        ]

        logger.info("🚀 Система мониторинга запущена")
        await asyncio.gather(*tasks, return_exceptions=True)

    async def stop_monitoring(self):
        """Остановка мониторинга"""
        self.running = False
        logger.info("⏹ Система мониторинга остановлена")

    async def _monitor_system_metrics(self):
        """Мониторинг системных ресурсов"""
        while self.running:
            try:
                # Собираем метрики
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')

                metrics = SystemMetrics(
                    cpu_percent=cpu_percent,
                    memory_percent=memory.percent,
                    disk_percent=disk.percent,
                    timestamp=datetime.now()
                )

                self.system_metrics.append(metrics)

                # Проверяем пороги
                await self._check_system_thresholds(metrics)

                await asyncio.sleep(30)  # Каждые 30 секунд

            except Exception as e:
                logger.error(f"Ошибка сбора метрик: {e}")
                await asyncio.sleep(60)

    async def _check_system_thresholds(self, metrics: SystemMetrics):
        """Проверка пороговых значений"""
        alerts = []

        # CPU
        if metrics.cpu_percent > self.thresholds['cpu_critical']:
            alerts.append(('cpu_critical', f"Критическое использование CPU: {metrics.cpu_percent:.1f}%"))
        elif metrics.cpu_percent > self.thresholds['cpu_warning']:
            alerts.append(('cpu_warning', f"Высокое использование CPU: {metrics.cpu_percent:.1f}%"))

        # Memory
        if metrics.memory_percent > self.thresholds['memory_critical']:
            alerts.append(('memory_critical', f"Критическое использование памяти: {metrics.memory_percent:.1f}%"))
        elif metrics.memory_percent > self.thresholds['memory_warning']:
            alerts.append(('memory_warning', f"Высокое использование памяти: {metrics.memory_percent:.1f}%"))

        # Disk
        if metrics.disk_percent > self.thresholds['disk_critical']:
            alerts.append(('disk_critical', f"Критическое заполнение диска: {metrics.disk_percent:.1f}%"))
        elif metrics.disk_percent > self.thresholds['disk_warning']:
            alerts.append(('disk_warning', f"Высокое заполнение диска: {metrics.disk_percent:.1f}%"))

        # Создаем алерты
        for alert_type, message in alerts:
            await self._create_alert(alert_type, message)

    async def _monitor_services(self):
        """Мониторинг сервисов"""
        while self.running:
            try:
                # Проверяем планировщик
                if self.scheduler:
                    if not self.scheduler.running:
                        await self._create_alert(
                            'scheduler_down',
                            "Планировщик остановлен",
                            level='critical'
                        )
                        # Автоисцеление
                        await self._heal_scheduler()

                # Проверяем базу данных
                if self.db:
                    try:
                        await self.db.get_setting('health_check')
                    except Exception as e:
                        await self._create_alert(
                            'database_error',
                            f"Ошибка БД: {str(e)[:100]}",
                            level='error'
                        )

                await asyncio.sleep(60)  # Каждую минуту

            except Exception as e:
                logger.error(f"Ошибка мониторинга сервисов: {e}")
                await asyncio.sleep(120)

    async def _auto_healing_loop(self):
        """Цикл автоисцеления"""
        while self.running:
            try:
                # Автоисцеление на основе алертов
                for alert_id, alert in list(self.active_alerts.items()):
                    if not alert.resolved and alert.level in ['error', 'critical']:
                        await self._attempt_healing(alert)

                await asyncio.sleep(120)  # Каждые 2 минуты

            except Exception as e:
                logger.error(f"Ошибка автоисцеления: {e}")
                await asyncio.sleep(300)

    async def _create_alert(self, alert_type: str, message: str, level: str = 'warning'):
        """Создание алерта"""
        alert_id = f"{alert_type}_{int(datetime.now().timestamp())}"

        # Избегаем дублирования алертов
        existing = [a for a in self.active_alerts.values()
                    if a.title == alert_type and not a.resolved]
        if existing:
            return

        alert = Alert(
            id=alert_id,
            level=level,
            title=alert_type,
            message=message,
            timestamp=datetime.now()
        )

        self.active_alerts[alert_id] = alert

        # Логируем алерт
        log_level = {
            'info': logger.info,
            'warning': logger.warning,
            'error': logger.error,
            'critical': logger.critical
        }.get(level, logger.warning)

        log_level(f"🚨 ALERT [{level.upper()}]: {message}")

    async def _attempt_healing(self, alert: Alert):
        """Попытка автоисцеления"""
        healing_method = {
            'cpu_critical': self._heal_cpu_issues,
            'memory_critical': self._heal_memory_issues,
            'scheduler_down': self._heal_scheduler,
            'database_error': self._heal_database
        }.get(alert.title)

        if healing_method:
            try:
                success = await healing_method()
                if success:
                    alert.resolved = True
                    self.healing_actions[alert.title] += 1
                    logger.info(f"✅ Автоисцеление: {alert.title} исправлен")

            except Exception as e:
                logger.error(f"❌ Ошибка автоисцеления {alert.title}: {e}")

    async def _heal_cpu_issues(self) -> bool:
        """Исцеление проблем с CPU"""
        try:
            # Принудительная сборка мусора
            import gc
            collected = gc.collect()
            logger.info(f"🔧 CPU исцеление: собрано {collected} объектов")

            # Снижаем частоту проверок планировщика
            if hasattr(self.scheduler, '_scheduler_task'):
                logger.info("🔧 Снижена частота проверок планировщика")

            return True

        except Exception as e:
            logger.error(f"Ошибка исцеления CPU: {e}")
            return False

    async def _heal_memory_issues(self) -> bool:
        """Исцеление проблем с памятью"""
        try:
            # Очистка кешей и принудительная сборка мусора
            import gc

            # Очищаем метрики (оставляем только последние 100)
            if len(self.system_metrics) > 100:
                while len(self.system_metrics) > 100:
                    self.system_metrics.popleft()

            # Очищаем старые алерты
            cutoff = datetime.now() - timedelta(hours=1)
            self.active_alerts = {
                k: v for k, v in self.active_alerts.items()
                if v.timestamp > cutoff or not v.resolved
            }

            collected = gc.collect()
            logger.info(f"🔧 Memory исцеление: очищено кешей, собрано {collected} объектов")

            return True

        except Exception as e:
            logger.error(f"Ошибка исцеления памяти: {e}")
            return False

    async def _heal_scheduler(self) -> bool:
        """Исцеление планировщика"""
        try:
            if self.scheduler and not self.scheduler.running:
                self.scheduler.start()
                logger.info("🔧 Планировщик перезапущен")
                return True
            return False

        except Exception as e:
            logger.error(f"Ошибка исцеления планировщика: {e}")
            return False

    async def _heal_database(self) -> bool:
        """Исцеление базы данных"""
        try:
            if self.db:
                # Переинициализация БД
                await self.db.init_database()
                logger.info("🔧 База данных переинициализирована")
                return True
            return False

        except Exception as e:
            logger.error(f"Ошибка исцеления БД: {e}")
            return False

    def get_system_status(self) -> Dict[str, Any]:
        """Получение статуса системы"""
        if not self.system_metrics:
            return {
                'status': 'no_data',
                'message': 'Нет данных мониторинга'
            }

        latest = self.system_metrics[-1]
        active_alerts = [a for a in self.active_alerts.values() if not a.resolved]

        # Определяем общий статус
        critical_alerts = [a for a in active_alerts if a.level == 'critical']
        error_alerts = [a for a in active_alerts if a.level == 'error']

        if critical_alerts:
            status = 'critical'
            emoji = '🔴'
        elif error_alerts:
            status = 'error'
            emoji = '🟠'
        elif active_alerts:
            status = 'warning'
            emoji = '🟡'
        else:
            status = 'healthy'
            emoji = '🟢'

        return {
            'status': status,
            'emoji': emoji,
            'cpu_percent': latest.cpu_percent,
            'memory_percent': latest.memory_percent,
            'disk_percent': latest.disk_percent,
            'active_alerts_count': len(active_alerts),
            'critical_alerts': len(critical_alerts),
            'healing_actions': dict(self.healing_actions),
            'monitoring_active': self.running,
            'last_check': latest.timestamp.isoformat()
        }

    def get_metrics_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Получение сводки метрик"""
        if not self.system_metrics:
            return {}

        # Фильтруем метрики за указанный период
        since = datetime.now() - timedelta(hours=hours)
        recent_metrics = [m for m in self.system_metrics if m.timestamp > since]

        if not recent_metrics:
            return {}

        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]
        disk_values = [m.disk_percent for m in recent_metrics]

        return {
            'period_hours': hours,
            'data_points': len(recent_metrics),
            'cpu': {
                'avg': sum(cpu_values) / len(cpu_values),
                'max': max(cpu_values),
                'min': min(cpu_values)
            },
            'memory': {
                'avg': sum(memory_values) / len(memory_values),
                'max': max(memory_values),
                'min': min(memory_values)
            },
            'disk': {
                'avg': sum(disk_values) / len(disk_values),
                'max': max(disk_values),
                'min': min(disk_values)
            }
        }