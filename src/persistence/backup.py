#!/usr/bin/env python3
"""
Система резервного копирования для SQLite базы данных.
Поддерживает автоматические, инкрементальные и scheduled бэкапы.
"""

import os
import shutil
import sqlite3
import gzip
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

@dataclass
class BackupConfig:
    """Конфигурация бэкапов."""
    enabled: bool = True
    backup_dir: str = "/app/backups"
    max_backups: int = 30  # Максимальное количество бэкапов
    compress: bool = True
    schedule_hours: List[int] = None  # Часы для автоматических бэкапов
    retention_days: int = 30
    verify_backup: bool = True
    
    def __post_init__(self):
        if self.schedule_hours is None:
            self.schedule_hours = [2, 14]  # 02:00 и 14:00

@dataclass
class BackupInfo:
    """Информация о бэкапе."""
    filename: str
    timestamp: datetime
    size_bytes: int
    compressed: bool
    verified: bool
    db_version: str
    tables_count: int
    records_count: int

class SQLiteBackupManager:
    """Менеджер резервного копирования SQLite."""
    
    def __init__(self, db_path: str, config: Optional[BackupConfig] = None):
        self.db_path = Path(db_path)
        self.config = config or self._load_config()
        self.backup_dir = Path(self.config.backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    def _load_config(self) -> BackupConfig:
        """Загружает конфигурацию из переменных окружения."""
        return BackupConfig(
            enabled=os.getenv('BACKUP_ENABLED', 'true').lower() == 'true',
            backup_dir=os.getenv('BACKUP_DIR', '/app/backups'),
            max_backups=int(os.getenv('MAX_BACKUPS', '30')),
            compress=os.getenv('BACKUP_COMPRESS', 'true').lower() == 'true',
            retention_days=int(os.getenv('BACKUP_RETENTION_DAYS', '30')),
            verify_backup=os.getenv('BACKUP_VERIFY', 'true').lower() == 'true',
            schedule_hours=[int(h) for h in os.getenv('BACKUP_SCHEDULE_HOURS', '2,14').split(',')]
        )
    
    async def create_backup(self, backup_type: str = "manual") -> Optional[BackupInfo]:
        """Создает резервную копию базы данных."""
        if not self.config.enabled:
            logger.info("Backup disabled in configuration")
            return None
        
        if not self.db_path.exists():
            logger.error(f"Database file not found: {self.db_path}")
            return None
        
        timestamp = datetime.now()
        backup_filename = f"mailing_backup_{timestamp.strftime('%Y%m%d_%H%M%S')}_{backup_type}.db"
        
        if self.config.compress:
            backup_filename += ".gz"
        
        backup_path = self.backup_dir / backup_filename
        
        try:
            # Создаем бэкап в отдельном потоке
            loop = asyncio.get_event_loop()
            backup_info = await loop.run_in_executor(
                self.executor, 
                self._create_backup_sync, 
                backup_path, 
                timestamp
            )
            
            if backup_info:
                logger.info(f"Backup created successfully: {backup_filename}")
                
                # Очистка старых бэкапов
                await self._cleanup_old_backups()
                
                # Сохраняем метаданные
                await self._save_backup_metadata(backup_info)
            
            return backup_info
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            # Удаляем частично созданный файл
            if backup_path.exists():
                backup_path.unlink()
            return None
    
    def _create_backup_sync(self, backup_path: Path, timestamp: datetime) -> Optional[BackupInfo]:
        """Синхронное создание бэкапа."""
        try:
            # Используем SQLite BACKUP API для консистентного бэкапа
            with sqlite3.connect(self.db_path) as source_conn:
                # Получаем информацию о БД
                cursor = source_conn.cursor()
                cursor.execute("SELECT sqlite_version()")
                db_version = cursor.fetchone()[0]
                
                # Считаем таблицы и записи
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                tables_count = len(tables)
                
                records_count = 0
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                    records_count += cursor.fetchone()[0]
                
                # Создаем временный файл для бэкапа
                temp_backup = backup_path.with_suffix('.tmp')
                
                # Выполняем бэкап
                with sqlite3.connect(temp_backup) as backup_conn:
                    source_conn.backup(backup_conn)
                
                # Сжимаем если нужно
                if self.config.compress:
                    with open(temp_backup, 'rb') as f_in:
                        with gzip.open(backup_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    temp_backup.unlink()
                else:
                    temp_backup.rename(backup_path)
                
                # Проверяем бэкап
                verified = False
                if self.config.verify_backup:
                    verified = self._verify_backup(backup_path)
                
                return BackupInfo(
                    filename=backup_path.name,
                    timestamp=timestamp,
                    size_bytes=backup_path.stat().st_size,
                    compressed=self.config.compress,
                    verified=verified,
                    db_version=db_version,
                    tables_count=tables_count,
                    records_count=records_count
                )
                
        except Exception as e:
            logger.error(f"Sync backup creation failed: {e}")
            return None
    
    def _verify_backup(self, backup_path: Path) -> bool:
        """Проверяет целостность бэкапа."""
        try:
            if self.config.compress:
                # Проверяем сжатый файл
                with gzip.open(backup_path, 'rb') as f:
                    # Создаем временный файл для проверки
                    temp_db = backup_path.parent / "temp_verify.db"
                    with open(temp_db, 'wb') as temp_f:
                        shutil.copyfileobj(f, temp_f)
                    
                    # Проверяем SQLite файл
                    verified = self._check_sqlite_integrity(temp_db)
                    temp_db.unlink()
                    return verified
            else:
                return self._check_sqlite_integrity(backup_path)
                
        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            return False
    
    def _check_sqlite_integrity(self, db_path: Path) -> bool:
        """Проверяет целостность SQLite файла."""
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()[0]
                return result == "ok"
        except Exception:
            return False
    
    async def _cleanup_old_backups(self):
        """Удаляет старые бэкапы."""
        try:
            # Получаем все файлы бэкапов
            backup_files = []
            for file_path in self.backup_dir.glob("mailing_backup_*.db*"):
                try:
                    stat = file_path.stat()
                    backup_files.append((file_path, stat.st_mtime))
                except OSError:
                    continue
            
            # Сортируем по времени (новые первые)
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # Удаляем лишние по количеству
            if len(backup_files) > self.config.max_backups:
                for file_path, _ in backup_files[self.config.max_backups:]:
                    logger.info(f"Removing old backup: {file_path.name}")
                    file_path.unlink()
            
            # Удаляем старые по времени
            cutoff_time = datetime.now() - timedelta(days=self.config.retention_days)
            cutoff_timestamp = cutoff_time.timestamp()
            
            for file_path, mtime in backup_files:
                if mtime < cutoff_timestamp:
                    logger.info(f"Removing expired backup: {file_path.name}")
                    file_path.unlink()
                    
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    async def _save_backup_metadata(self, backup_info: BackupInfo):
        """Сохраняет метаданные бэкапа."""
        try:
            metadata_file = self.backup_dir / f"{backup_info.filename}.json"
            metadata = asdict(backup_info)
            metadata['timestamp'] = backup_info.timestamp.isoformat()
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Failed to save backup metadata: {e}")
    
    async def list_backups(self) -> List[BackupInfo]:
        """Возвращает список всех бэкапов."""
        backups = []
        
        for metadata_file in self.backup_dir.glob("*.json"):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                # Восстанавливаем timestamp
                metadata['timestamp'] = datetime.fromisoformat(metadata['timestamp'])
                
                backup_info = BackupInfo(**metadata)
                
                # Проверяем что файл бэкапа существует
                backup_file = self.backup_dir / backup_info.filename
                if backup_file.exists():
                    backups.append(backup_info)
                else:
                    # Удаляем метаданные для несуществующего файла
                    metadata_file.unlink()
                    
            except Exception as e:
                logger.warning(f"Failed to load backup metadata from {metadata_file}: {e}")
        
        return sorted(backups, key=lambda x: x.timestamp, reverse=True)
    
    async def restore_backup(self, backup_filename: str, target_path: Optional[str] = None) -> bool:
        """Восстанавливает базу данных из бэкапа."""
        backup_path = self.backup_dir / backup_filename
        
        if not backup_path.exists():
            logger.error(f"Backup file not found: {backup_filename}")
            return False
        
        target_path = Path(target_path) if target_path else self.db_path
        
        try:
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                self.executor,
                self._restore_backup_sync,
                backup_path,
                target_path
            )
            
            if success:
                logger.info(f"Database restored from backup: {backup_filename}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False
    
    def _restore_backup_sync(self, backup_path: Path, target_path: Path) -> bool:
        """Синхронное восстановление из бэкапа."""
        try:
            # Создаем резервную копию текущей БД
            if target_path.exists():
                backup_current = target_path.with_suffix('.backup_before_restore')
                shutil.copy2(target_path, backup_current)
            
            if self.config.compress and backup_path.suffix == '.gz':
                # Распаковываем
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(target_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                # Копируем напрямую
                shutil.copy2(backup_path, target_path)
            
            # Проверяем восстановленную БД
            if self._check_sqlite_integrity(target_path):
                return True
            else:
                logger.error("Restored database failed integrity check")
                # Восстанавливаем оригинал если есть
                backup_current = target_path.with_suffix('.backup_before_restore')
                if backup_current.exists():
                    shutil.copy2(backup_current, target_path)
                return False
                
        except Exception as e:
            logger.error(f"Restore operation failed: {e}")
            return False

class BackupScheduler:
    """Планировщик автоматических бэкапов."""
    
    def __init__(self, backup_manager: SQLiteBackupManager):
        self.backup_manager = backup_manager
        self._running = False
        self._task = None
    
    async def start(self):
        """Запускает планировщик."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info("Backup scheduler started")
    
    async def stop(self):
        """Останавливает планировщик."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Backup scheduler stopped")
    
    async def _scheduler_loop(self):
        """Основной цикл планировщика."""
        last_backup_date = None
        
        while self._running:
            try:
                now = datetime.now()
                current_hour = now.hour
                current_date = now.date()
                
                # Проверяем нужно ли делать бэкап
                should_backup = (
                    current_hour in self.backup_manager.config.schedule_hours and
                    current_date != last_backup_date
                )
                
                if should_backup:
                    logger.info(f"Starting scheduled backup at {now}")
                    backup_info = await self.backup_manager.create_backup("scheduled")
                    
                    if backup_info:
                        last_backup_date = current_date
                        logger.info("Scheduled backup completed successfully")
                    else:
                        logger.error("Scheduled backup failed")
                
                # Ждем до следующей проверки (каждые 30 минут)
                await asyncio.sleep(1800)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(300)  # Ждем 5 минут при ошибке

# Глобальный экземпляр для использования в приложении
backup_manager: Optional[SQLiteBackupManager] = None
backup_scheduler: Optional[BackupScheduler] = None

def initialize_backup_system(db_path: str):
    """Инициализирует систему бэкапов."""
    global backup_manager, backup_scheduler
    
    backup_manager = SQLiteBackupManager(db_path)
    backup_scheduler = BackupScheduler(backup_manager)
    
    return backup_manager, backup_scheduler

async def start_backup_scheduler():
    """Запускает планировщик бэкапов."""
    if backup_scheduler:
        await backup_scheduler.start()

async def stop_backup_scheduler():
    """Останавливает планировщик бэкапов."""
    if backup_scheduler:
        await backup_scheduler.stop()