# services/scheduler.py - ПОЛНАЯ ЗАМЕНА существующего файла
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Callable, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class JobType(Enum):
    DAILY_POST = "daily_post"
    INTERVAL_POST = "interval_post"
    CUSTOM = "custom"


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledJob:
    """Упрощенная версия для быстрой интеграции"""
    id: str
    name: str
    job_type: JobType
    func_name: str
    func_args: Dict[str, Any]
    next_run: datetime
    interval_seconds: Optional[int] = None
    max_retries: int = 3
    is_active: bool = True
    current_retries: int = 0
    status: JobStatus = JobStatus.PENDING


class PostScheduler:
    """Улучшенный планировщик с базовой персистентностью"""

    def __init__(self, content_manager, db=None):
        self.content_manager = content_manager
        self.db = db
        self.running = False
        self.jobs: Dict[str, ScheduledJob] = {}
        self._scheduler_task: Optional[asyncio.Task] = None

        # Регистрируем доступные функции
        self._function_registry = {
            'process_and_publish_news': self.content_manager.process_and_publish_news,
        }

        logger.info("✅ Новый планировщик инициализирован")

    def start(self):
        """Запуск планировщика"""
        if self.running:
            logger.warning("Планировщик уже запущен")
            return

        self.running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("🚀 Планировщик запущен с улучшенной логикой")

    def stop(self):
        """Остановка планировщика"""
        self.running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
        logger.info("⏹ Планировщик остановлен")

    def schedule_daily_posts(self, times: List[str]) -> List[str]:
        """Планирование ежедневных постов"""
        job_ids = []

        for time_str in times:
            try:
                hour, minute = map(int, time_str.split(':'))

                # Вычисляем следующее время запуска
                now = datetime.now()
                next_run = datetime.combine(now.date(), datetime.min.time().replace(hour=hour, minute=minute))

                # Если время уже прошло сегодня, планируем на завтра
                if next_run <= now:
                    next_run += timedelta(days=1)

                job_id = str(uuid.uuid4())

                job = ScheduledJob(
                    id=job_id,
                    name=f"Ежедневная публикация в {time_str}",
                    job_type=JobType.DAILY_POST,
                    func_name='process_and_publish_news',
                    func_args={},
                    next_run=next_run,
                    interval_seconds=24 * 3600  # 24 часа
                )

                self.jobs[job_id] = job
                job_ids.append(job_id)

                logger.info(f"📅 Запланирована ежедневная публикация в {time_str} (ID: {job_id[:8]})")

            except ValueError as e:
                logger.error(f"❌ Неверный формат времени {time_str}: {e}")

        return job_ids

    def schedule_interval_posts(self, interval_hours: int) -> str:
        """Планирование постов через интервалы"""
        job_id = str(uuid.uuid4())
        interval_seconds = interval_hours * 3600

        job = ScheduledJob(
            id=job_id,
            name=f"Публикация каждые {interval_hours} ч",
            job_type=JobType.INTERVAL_POST,
            func_name='process_and_publish_news',
            func_args={},
            next_run=datetime.now() + timedelta(hours=interval_hours),
            interval_seconds=interval_seconds
        )

        self.jobs[job_id] = job
        logger.info(f"⏰ Запланирована публикация каждые {interval_hours} часов (ID: {job_id[:8]})")

        return job_id

    def get_scheduled_jobs(self) -> List[Dict]:
        """Получение списка запланированных задач"""
        return [
            {
                'id': job.id[:8] + '...',  # Короткий ID для отображения
                'name': job.name,
                'type': job.job_type.value,
                'next_run': job.next_run.isoformat() if job.next_run else None,
                'status': job.status.value,
                'active': job.is_active
            }
            for job in self.jobs.values()
        ]

    def cancel_job(self, job_id: str) -> bool:
        """Отмена задачи"""
        # Поддерживаем как полный ID, так и короткий
        matching_jobs = [jid for jid in self.jobs.keys() if jid.startswith(job_id) or jid == job_id]

        if matching_jobs:
            full_job_id = matching_jobs[0]
            self.jobs[full_job_id].status = JobStatus.CANCELLED
            self.jobs[full_job_id].is_active = False
            logger.info(f"❌ Задача {full_job_id[:8]} отменена")
            return True
        return False

    async def _scheduler_loop(self):
        """Основной цикл планировщика"""
        logger.info("🔄 Запущен основной цикл планировщика")

        while self.running:
            try:
                now = datetime.now()

                # Находим задачи для выполнения
                jobs_to_run = [
                    job for job in self.jobs.values()
                    if (job.status == JobStatus.PENDING and
                        job.is_active and
                        job.next_run <= now)
                ]

                # Выполняем задачи
                for job in jobs_to_run:
                    asyncio.create_task(self._execute_job(job))

                # Сохраняем состояние каждые 10 минут
                if now.minute % 10 == 0 and now.second < 30:
                    await self._save_jobs_to_db()

                await asyncio.sleep(30)  # Проверяем каждые 30 секунд

            except Exception as e:
                logger.error(f"❌ Ошибка в цикле планировщика: {e}")
                await asyncio.sleep(60)

    async def _execute_job(self, job: ScheduledJob):
        """Выполнение задачи"""
        job.status = JobStatus.RUNNING
        start_time = datetime.now()

        try:
            logger.info(f"⚡ Выполняется задача: {job.name}")

            # Получаем функцию
            if job.func_name not in self._function_registry:
                raise ValueError(f"Функция {job.func_name} не зарегистрирована")

            func = self._function_registry[job.func_name]

            # Выполняем функцию
            if asyncio.iscoroutinefunction(func):
                await func(**job.func_args)
            else:
                await asyncio.get_event_loop().run_in_executor(None, lambda: func(**job.func_args))

            # Успешное выполнение
            job.status = JobStatus.COMPLETED
            job.current_retries = 0

            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Задача {job.name} выполнена за {duration:.1f}с")

        except Exception as e:
            job.current_retries += 1

            if job.current_retries < job.max_retries:
                job.status = JobStatus.PENDING
                job.next_run = datetime.now() + timedelta(minutes=5)  # Retry через 5 минут
                logger.warning(f"⚠️ Задача {job.name} провалилась, попытка {job.current_retries}/{job.max_retries}")
            else:
                job.status = JobStatus.FAILED
                job.is_active = False
                logger.error(f"❌ Задача {job.name} провалилась окончательно: {e}")

        finally:
            # Планируем следующий запуск для повторяющихся задач
            if job.status == JobStatus.COMPLETED and job.interval_seconds and job.is_active:
                job.next_run = datetime.now() + timedelta(seconds=job.interval_seconds)
                job.status = JobStatus.PENDING
                logger.info(f"📅 Следующий запуск задачи {job.name}: {job.next_run.strftime('%H:%M %d.%m')}")

    async def _save_jobs_to_db(self):
        """Сохранение задач в БД"""
        if not self.db:
            return

        try:
            jobs_data = {}
            for job_id, job in self.jobs.items():
                if job.status not in [JobStatus.CANCELLED, JobStatus.FAILED]:
                    jobs_data[job_id] = {
                        'id': job.id,
                        'name': job.name,
                        'job_type': job.job_type.value,
                        'func_name': job.func_name,
                        'func_args': job.func_args,
                        'next_run': job.next_run.isoformat() if job.next_run else None,
                        'interval_seconds': job.interval_seconds,
                        'max_retries': job.max_retries,
                        'is_active': job.is_active,
                        'current_retries': job.current_retries,
                        'status': job.status.value
                    }

            await self.db.set_setting('scheduler_jobs', json.dumps(jobs_data))
            logger.debug(f"💾 Сохранено {len(jobs_data)} задач в БД")

        except Exception as e:
            logger.error(f"❌ Ошибка сохранения задач: {e}")

    async def restore_jobs_from_db(self):
        """Восстановление задач из БД"""
        if not self.db:
            return

        try:
            jobs_json = await self.db.get_setting('scheduler_jobs')
            if not jobs_json:
                logger.info("📝 Нет сохраненных задач в БД")
                return

            jobs_data = json.loads(jobs_json)
            restored_count = 0

            for job_id, job_data in jobs_data.items():
                try:
                    job = ScheduledJob(
                        id=job_data['id'],
                        name=job_data['name'],
                        job_type=JobType(job_data['job_type']),
                        func_name=job_data['func_name'],
                        func_args=job_data['func_args'],
                        next_run=datetime.fromisoformat(job_data['next_run']) if job_data['next_run'] else None,
                        interval_seconds=job_data.get('interval_seconds'),
                        max_retries=job_data['max_retries'],
                        is_active=job_data['is_active'],
                        current_retries=job_data['current_retries'],
                        status=JobStatus(job_data['status'])
                    )

                    # Сбрасываем статус RUNNING задач при перезапуске
                    if job.status == JobStatus.RUNNING:
                        job.status = JobStatus.PENDING

                    self.jobs[job_id] = job
                    restored_count += 1

                except Exception as e:
                    logger.error(f"❌ Ошибка восстановления задачи {job_id}: {e}")

            logger.info(f"🔄 Восстановлено {restored_count} задач из БД")

        except Exception as e:
            logger.error(f"❌ Ошибка восстановления задач из БД: {e}")

    def get_scheduler_status(self) -> Dict[str, Any]:
        """Получение статуса планировщика"""
        active_jobs = [job for job in self.jobs.values() if job.is_active]
        pending_jobs = [job for job in active_jobs if job.status == JobStatus.PENDING]

        next_job = None
        if pending_jobs:
            next_job = min(pending_jobs, key=lambda j: j.next_run)

        return {
            'running': self.running,
            'total_jobs': len(self.jobs),
            'active_jobs': len(active_jobs),
            'pending_jobs': len(pending_jobs),
            'next_execution': next_job.next_run.isoformat() if next_job else None,
            'next_job_name': next_job.name if next_job else None
        }