from __future__ import annotations
import sys
import os
import json
import subprocess
import threading
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QPushButton, QStackedWidget, QComboBox, QTextEdit, QFrame,
    QLineEdit, QFileDialog, QSpinBox, QCheckBox, QProgressBar, QGraphicsOpacityEffect, 
    QApplication, QTableWidget, QTableWidgetItem, QTabWidget, QSplitter, QGroupBox,
    QGridLayout, QMessageBox, QDialog, QFormLayout, QScrollArea, QTreeWidget, QTreeWidgetItem,
    QSizePolicy, QHeaderView
)

from PySide6.QtWidgets import QStyledItemDelegate

class ErrorDotDelegate(QStyledItemDelegate):
    """Делегат рисует цветной кружок и число ошибок в ячейке."""
    def paint(self, painter, option, index):
        value = index.data()
        try:
            num = int(value)
        except (TypeError, ValueError):
            num = 0

        # Определяем цвет по количеству
        if num == 0:
            color = QColor('#10B981')  # зеленый - нет ошибок
        elif num < 20:
            color = QColor('#F59E0B')  # оранжевый - немного
        elif num < 60:
            color = QColor('#F97316')  # ярко-оранжевый
        else:
            color = QColor('#EF4444')  # красный - много

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        r = option.rect
        dot_size = min(r.height()-8, 14)
        dot_x = r.x() + 6
        dot_y = r.y() + (r.height() - dot_size) // 2
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(dot_x, dot_y, dot_size, dot_size)

        # Текст числа правее
        painter.setPen(QColor('#FFFFFF'))
        painter.drawText(dot_x + dot_size + 6, r.y(), r.width()-dot_size-12, r.height(), Qt.AlignVCenter | Qt.AlignLeft, str(num))
        painter.restore()

    def sizeHint(self, option, index):
        base = super().sizeHint(option, index)
        if base.height() < 28:
            base.setHeight(28)
        return base
from PySide6.QtCore import Qt, QPropertyAnimation, QTimer, Signal, QThread, QSize, QRect
from PySide6.QtGui import QFont, QPixmap, QIcon, QColor, QPainter, QPen, QPainterPath, QPalette
import logging
import asyncio
import httpx

# Импорты из существующих модулей
from .theme import ThemeManager
from .log_handler import QtLogHandler, install_qt_log_handler
from .mailer_service import MailerService
from .components import ModernButton
from .progress_ring import ProgressRing
from .text_field import FloatingTextField
from .switch import IOSSwitch
from .stats_card import StatsCard
from .segmented_control import SegmentedControl
from .layout_utils import apply_margins, apply_spacing, margins
from .typography import apply_heading_style, apply_text_style, make_page_title
from templating.html_highlighter import HtmlHighlighter

# Импорты для работы с системой
from mailing.config import settings
from persistence.repository import DeliveryRepository, EventRepository
from mailing.limits.daily_quota import DailyQuota
from data_loader.csv_loader import CSVLoader
from data_loader.excel_loader import ExcelLoader
from data_loader.json_loader import JSONLoader
from validation.email_validator import validate_email_list

# Расширенные секции
ENHANCED_SECTION_KEYS = [
    "section_dashboard",
    "section_campaigns", 
    "section_webhook_manager",
    "section_system_monitor",
    "section_config_manager",
    "section_template_editor",
    "section_statistics",
    "section_recipients",
    "section_logs",
    "section_settings",
]

class WebhookServerManager(QThread):
    """Менеджер для запуска/остановки webhook сервера"""
    server_started = Signal()
    server_stopped = Signal()
    server_error = Signal(str)
    server_output = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.process = None
        self.running = False
        
    def start_server(self, port=8000):
        """Запуск webhook сервера"""
        if self.running:
            return
            
        try:
            cmd = [
                sys.executable, "-m", "uvicorn", 
                "mailing.webhook_server:app",
                "--host", "0.0.0.0",
                "--port", str(port),
                "--reload"
            ]
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=Path(__file__).parent.parent
            )
            
            self.running = True
            self.server_started.emit()
            self.start()  # Запуск потока для мониторинга
            
        except Exception as e:
            self.server_error.emit(f"Ошибка запуска сервера: {e}")
    
    def stop_server(self):
        """Остановка webhook сервера"""
        if self.process and self.running:
            self.process.terminate()
            self.process.wait()
            self.running = False
            self.server_stopped.emit()
    
    def run(self):
        """Мониторинг вывода сервера"""
        if not self.process:
            return
            
        while self.running and self.process.poll() is None:
            line = self.process.stdout.readline()
            if line:
                self.server_output.emit(line.strip())
        
        # Если процесс завершился неожиданно
        if self.process.poll() is not None and self.running:
            self.running = False
            self.server_stopped.emit()

class SystemMonitorWidget(QWidget):
    """Виджет для мониторинга системы"""
    
    def __init__(self, theme_manager: ThemeManager):
        super().__init__()
        self.theme_manager = theme_manager
        self.delivery_repo = DeliveryRepository()
        self.event_repo = EventRepository()
        self.quota = DailyQuota()
        self.quota.load()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(5000)  # Обновление каждые 5 секунд
        
        self.init_ui()
        self.update_stats()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)  # Уменьшаем отступы
        layout.setSpacing(16)  # Уменьшаем промежутки
        
        # Заголовок страницы (унифицированный)
        title = make_page_title("📊 System Monitor")
        layout.addWidget(title)
        
        # Карточки основной статистики
        cards_layout = QHBoxLayout()

        self.db_card = StatsCard("База данных", "Загрузка...", 0.0, accent=QColor('#8B5CF6'), parent=None, theme_manager=self.theme_manager, glyph="🗄")  # Фиолетовый
        self.quota_card = StatsCard("Квоты", "Загрузка...", 0.0, accent=QColor('#F59E0B'), parent=None, theme_manager=self.theme_manager, glyph="📊")  # Янтарный
        self.webhook_card = StatsCard("Webhook сервер", "Загрузка...", 0.0, accent=QColor('#06B6D4'), parent=None, theme_manager=self.theme_manager, glyph="🔔")  # Циан

        cards_layout.addWidget(self.db_card)
        cards_layout.addWidget(self.quota_card)
        cards_layout.addWidget(self.webhook_card)

        layout.addLayout(cards_layout)
        
        # Подробная информация
        details_splitter = QSplitter(Qt.Horizontal)
        
        # Таблица последних доставок
        deliveries_group = QGroupBox("Последние доставки")
        deliveries_group.setStyleSheet("""
            QGroupBox {
                background-color: #2D3748;
                border: 1px solid #4A5568;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: 600;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 2px 8px;
                top: -2px;
                left: 10px;
                background-color: #2D3748;
                color: white;
                border-radius: 4px;
                font-weight: 600;
            }
        """)
        deliveries_layout = QVBoxLayout(deliveries_group)
        deliveries_layout.setContentsMargins(0, 0, 0, 0)  # Убираем отступы
        deliveries_layout.setSpacing(0)  # Убираем промежутки
        
        self.deliveries_table = QTableWidget()
        self.deliveries_table.setColumnCount(3)
        self.deliveries_table.setHorizontalHeaderLabels([
            "Email", "Успех", "Ошибка"
        ])
        # Настройка размеров столбцов для растягивания на весь блок
        header = self.deliveries_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Email растягивается
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Успех по содержимому
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Ошибка растягивается
        # Устанавливаем минимальные размеры
        self.deliveries_table.setColumnWidth(0, 300)  # Email - основная колонка
        self.deliveries_table.setColumnWidth(1, 80)   # Успех
        self.deliveries_table.setColumnWidth(2, 250)  # Ошибка
        # Настройка стилей для полного растягивания
        self.deliveries_table.setStyleSheet("""
            QTableWidget {
                background-color: #2D3748;
                border: 1px solid #4A5568;
                border-radius: 8px;
                color: white;
                gridline-color: #4A5568;
            }
            QTableWidget::item {
                padding: 12px;
                border-bottom: 1px solid #4A5568;
            }
            QTableWidget::item:selected {
                background-color: #6366F1;
            }
            QHeaderView::section {
                background-color: #374151;
                color: white;
                padding: 12px;
                border: none;
                font-weight: bold;
            }
            QTableCornerButton::section {
                background-color: #2D3748;
                border: 1px solid #4A5568;
            }
        """)
        self.deliveries_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        deliveries_layout.addWidget(self.deliveries_table)
        
        # Таблица webhook событий
        events_group = QGroupBox("Webhook события")
        events_group.setStyleSheet("""
            QGroupBox {
                background-color: #2D3748;
                border: 1px solid #4A5568;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: 600;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 2px 8px;
                top: -2px;
                left: 10px;
                background-color: #2D3748;
                color: white;
                border-radius: 4px;
                font-weight: 600;
            }
        """)
        events_layout = QVBoxLayout(events_group)
        events_layout.setContentsMargins(0, 0, 0, 0)  # Убираем отступы
        events_layout.setSpacing(0)  # Убираем промежутки
        
        self.events_table = QTableWidget()
        # Уменьшаем до 3 столбцов: Email, Подпись, Время
        self.events_table.setColumnCount(3)
        self.events_table.setHorizontalHeaderLabels([
            "Email", "Подпись", "Время"
        ])
        header = self.events_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Email растягивается полностью
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Подпись
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Время
        self.events_table.setColumnWidth(0, 300)
        self.events_table.setColumnWidth(1, 80)
        self.events_table.setColumnWidth(2, 160)
        # Скрываем вертикальный header (левый черный прямоугольник)
        self.events_table.verticalHeader().setVisible(False)
        self.events_table.setShowGrid(False)
        # Настройка стилей для полного растягивания
        self.events_table.setStyleSheet("""
            QTableWidget {
                background-color: #2D3748;
                border: 1px solid #4A5568;
                border-radius: 8px;
                color: white;
                gridline-color: #4A5568;
            }
            QTableWidget::item {
                padding: 10px;
                border-bottom: 1px solid #4A5568;
            }
            QTableWidget::item:selected {
                background-color: #6366F1;
            }
            QHeaderView::section {
                background-color: #374151;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
            QTableCornerButton::section {
                background-color: #2D3748;
                border: 1px solid #4A5568;
            }
        """)
        self.events_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        events_layout.addWidget(self.events_table)
        
        details_splitter.addWidget(deliveries_group)
        details_splitter.addWidget(events_group)
        
        layout.addWidget(details_splitter)
        
        # Системная информация
        system_info_group = QGroupBox("Информация о системе")
        system_info_layout = QVBoxLayout(system_info_group)

        self.system_info_text = QTextEdit()
        self.system_info_text.setReadOnly(True)
        # Удалено ограничение по высоте – растягивается вместе с группой
        self.system_info_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.system_info_text.setLineWrapMode(QTextEdit.WidgetWidth)
        self.system_info_text.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.system_info_text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.system_info_text.setStyleSheet("QTextEdit { background: #1E2530; border: 1px solid #2F3A46; border-radius: 8px; padding: 16px; font-size: 13px; }")
        system_info_layout.addWidget(self.system_info_text, 1)

        layout.addWidget(system_info_group)
    
    def update_stats(self):
        """Обновление статистики"""
        try:
            # Статистика БД
            stats = self.delivery_repo.stats()
            total = stats['total']
            success_rate = (stats['success'] / max(total, 1)) * 100
            self.db_card.setValue(f"{total} доставок")
            self.db_card.setProgress(success_rate / 100)
            
            # Квоты
            used = self.quota.used()
            limit = self.quota.limit
            quota_percent = (used / limit) * 100
            self.quota_card.setValue(f"{used}/{limit}")
            self.quota_card.setProgress(quota_percent / 100)
            
            # Проверка webhook сервера
            try:
                import httpx
                with httpx.Client(timeout=1.0) as client:
                    response = client.get("http://localhost:8000/health")
                    if response.status_code == 200:
                        self.webhook_card.setValue("Работает")
                        self.webhook_card.setProgress(1.0)
                    else:
                        self.webhook_card.setValue("Ошибка")
                        self.webhook_card.setProgress(0.0)
            except:
                self.webhook_card.setValue("Остановлен")
                self.webhook_card.setProgress(0.0)
            
            # Обновление таблиц
            self.update_deliveries_table()
            self.update_events_table()
            self.update_system_info()
            
        except Exception as e:
            logging.error(f"Ошибка обновления статистики: {e}")
    
    def update_deliveries_table(self):
        """Обновление таблицы доставок"""
        try:
            # Получаем последние доставки из репозитория
            deliveries = self.delivery_repo.get_recent_deliveries(50)
            
            self.deliveries_table.setRowCount(len(deliveries))
            
            for row, delivery in enumerate(deliveries):
                # Email
                self.deliveries_table.setItem(row, 0, QTableWidgetItem(delivery['email']))
                
                # Status
                status = "✅ Успешно" if delivery['success'] else "❌ Ошибка"
                status_item = QTableWidgetItem(status)
                if delivery['success']:
                    status_item.setBackground(QColor('#10B981'))
                else:
                    status_item.setBackground(QColor('#EF4444'))
                self.deliveries_table.setItem(row, 1, status_item)
                
                # Error
                error_text = delivery['error'] or '-'
                if len(error_text) > 80:
                    error_text = error_text[:77] + '...'
                self.deliveries_table.setItem(row, 2, QTableWidgetItem(error_text))
            
        except Exception as e:
            logging.error(f"Ошибка обновления таблицы доставок: {e}")
    
    def update_events_table(self):
        """Обновление таблицы событий"""
        try:
            events = self.event_repo.get_recent_events(15)
            self.events_table.setRowCount(len(events))

            for row, event in enumerate(events):
                # Колонки: Email (тип события), Подпись (валидна/нет), Время
                self.events_table.setItem(row, 0, QTableWidgetItem(str(event.get('recipient') or event.get('event_type') or '')))
                self.events_table.setItem(row, 1, QTableWidgetItem("✅" if event.get('signature_valid') else "❌"))
                self.events_table.setItem(row, 2, QTableWidgetItem(str(event.get('created_at', ''))))
                
        except Exception as e:
            logging.error(f"Ошибка обновления таблицы событий: {e}")
    
    def update_system_info(self):
        """Обновление системной информации"""
        try:
            info_text = f"""
Конфигурация:
• Resend API: {'✅' if settings.resend_api_key else '❌'}
• Дневной лимит: {settings.daily_email_limit}
• Параллельность: {settings.concurrency}
• Лимит скорости: {settings.rate_limit_per_minute}/мин

База данных:
• Путь: {settings.sqlite_db_path}
• Всего доставок: {self.delivery_repo.stats()['total']}
• Всего событий: {len(self.event_repo.get_recent_events(1000))}

Квоты:
• Использовано сегодня: {self.quota.used()}/{self.quota.limit}
• Дата: {self.quota.current_day()}
"""
            self.system_info_text.setPlainText(info_text.strip())
            
        except Exception as e:
            logging.error(f"Ошибка обновления системной информации: {e}")

class ConfigManagerWidget(QWidget):
    """Виджет для управления конфигурацией"""
    
    def __init__(self, theme_manager: ThemeManager):
        super().__init__()
        self.theme_manager = theme_manager
        self.env_file_path = Path(".env")
        self.init_ui()
        self.load_config()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)  # Уменьшаем отступы
        layout.setSpacing(16)  # Уменьшаем промежутки
        
        # Заголовок страницы
        title = make_page_title("⚙️ Config Manager")
        layout.addWidget(title)
        
        # Предупреждение
        warning = QLabel("⚠️ Изменения требуют перезапуска приложения")
        warning.setStyleSheet("color: orange; margin-bottom: 20px;")
        layout.addWidget(warning)
        
        # Прокручиваемая область с настройками
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QFormLayout(scroll_widget)
        
        # Поля конфигурации
        self.config_fields = {}
        
        config_sections = [
            ("Resend настройки", [
                ("RESEND_API_KEY", "API ключ Resend", "password"),
                ("RESEND_FROM_EMAIL", "Email отправителя Resend", "text"),
                ("RESEND_FROM_NAME", "Имя отправителя Resend", "text"),
            ]),
            ("Общие настройки", [
                ("DAILY_EMAIL_LIMIT", "Дневной лимит писем", "number"),
                ("RATE_LIMIT_PER_MINUTE", "Лимит в минуту", "number"),
                ("MAX_RETRIES", "Максимум повторов", "number"),
                ("CONCURRENCY", "Параллельность", "number"),
                ("SQLITE_DB_PATH", "Путь к БД", "text"),
                ("LOG_LEVEL", "Уровень логирования", "combo"),
            ])
        ]
        
        for section_name, fields in config_sections:
            # Разделитель секции
            section_label = QLabel(section_name)
            section_label.setStyleSheet("font-weight: bold; color: #0066cc; margin-top: 15px;")
            scroll_layout.addRow(section_label)
            
            for env_key, label, field_type in fields:
                if field_type == "password":
                    field = QLineEdit()
                    field.setEchoMode(QLineEdit.Password)
                elif field_type == "number":
                    field = QSpinBox()
                    field.setRange(0, 100000)
                elif field_type == "combo" and env_key == "LOG_LEVEL":
                    field = QComboBox()
                    field.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
                else:
                    field = QLineEdit()
                
                self.config_fields[env_key] = field
                scroll_layout.addRow(label + ":", field)
        
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        self.load_button = ModernButton("Перезагрузить", variant="secondary", theme_manager=self.theme_manager)
        self.load_button.clicked.connect(self.load_config)
        
        self.save_button = ModernButton("Сохранить", variant="primary", theme_manager=self.theme_manager)
        self.save_button.clicked.connect(self.save_config)
        
        self.reset_button = ModernButton("Сброс", variant="tertiary", theme_manager=self.theme_manager)
        self.reset_button.clicked.connect(self.reset_config)
        
        buttons_layout.addWidget(self.load_button)
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.reset_button)
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
    
    def load_config(self):
        """Загрузка текущей конфигурации"""
        try:
            # Загружаем из .env файла
            env_vars = {}
            if self.env_file_path.exists():
                with open(self.env_file_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            env_vars[key.strip()] = value.strip().strip('"\'')
            
            # Заполняем поля
            for env_key, field in self.config_fields.items():
                value = env_vars.get(env_key, "")
                
                if isinstance(field, QLineEdit):
                    field.setText(value)
                elif isinstance(field, QSpinBox):
                    try:
                        field.setValue(int(value) if value else 0)
                    except ValueError:
                        field.setValue(0)
                elif isinstance(field, QComboBox):
                    index = field.findText(value)
                    if index >= 0:
                        field.setCurrentIndex(index)
            
            QMessageBox.information(self, "Успех", "Конфигурация загружена")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки конфигурации: {e}")
    
    def save_config(self):
        """Сохранение конфигурации в .env файл"""
        try:
            lines = []
            lines.append("# Конфигурация системы массовой рассылки")
            lines.append("# Создано GUI приложением")
            lines.append("")
            
            current_section = ""
            for env_key, field in self.config_fields.items():
                # Определяем секцию
                if env_key.startswith("RESEND_") and current_section != "RESEND":
                    lines.append("# Resend настройки")
                    current_section = "RESEND"
                elif not env_key.startswith(("RESEND_",)) and current_section != "GENERAL":
                    lines.append("# Общие настройки")
                    current_section = "GENERAL"
                
                # Получаем значение
                if isinstance(field, QLineEdit):
                    value = field.text().strip()
                elif isinstance(field, QSpinBox):
                    value = str(field.value())
                elif isinstance(field, QComboBox):
                    value = field.currentText()
                else:
                    value = ""
                
                # Добавляем в файл только если есть значение
                if value:
                    lines.append(f"{env_key}={value}")
            
            # Сохраняем файл
            with open(self.env_file_path, 'w') as f:
                f.write("\\n".join(lines))
            
            QMessageBox.information(self, "Успех", 
                "Конфигурация сохранена!\\n\\nПерезапустите приложение для применения изменений.")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения конфигурации: {e}")
    
    def reset_config(self):
        """Сброс конфигурации к значениям по умолчанию"""
        reply = QMessageBox.question(self, "Подтверждение", 
            "Вы уверены, что хотите сбросить все настройки?",
            QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            for field in self.config_fields.values():
                if isinstance(field, QLineEdit):
                    field.clear()
                elif isinstance(field, QSpinBox):
                    field.setValue(0)
                elif isinstance(field, QComboBox):
                    field.setCurrentIndex(0)

class WebhookManagerWidget(QWidget):
    """Виджет для управления webhook сервером"""
    
    def __init__(self, theme_manager: ThemeManager):
        super().__init__()
        self.theme_manager = theme_manager
        self.server_manager = WebhookServerManager()
        self.server_manager.server_started.connect(self.on_server_started)
        self.server_manager.server_stopped.connect(self.on_server_stopped)
        self.server_manager.server_error.connect(self.on_server_error)
        self.server_manager.server_output.connect(self.on_server_output)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)  # Уменьшаем отступы
        layout.setSpacing(16)  # Уменьшаем промежутки
        
        # Заголовок страницы
        title = make_page_title("🔗 Webhook Manager")
        layout.addWidget(title)
        
        # Управление сервером
        server_group = QGroupBox("Управление Webhook сервером")
        server_layout = QVBoxLayout(server_group)
        
        # Статус и кнопки
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("Статус: Остановлен")
        self.status_label.setStyleSheet("font-weight: bold;")
        
        self.start_button = ModernButton("Запустить", variant="primary", theme_manager=self.theme_manager)
        self.start_button.clicked.connect(self.start_server)
        
        self.stop_button = ModernButton("Остановить", variant="secondary", theme_manager=self.theme_manager)
        self.stop_button.clicked.connect(self.stop_server)
        self.stop_button.setEnabled(False)
        
        self.test_button = ModernButton("Тест", variant="tertiary", theme_manager=self.theme_manager)
        self.test_button.clicked.connect(self.test_server)
        
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.start_button)
        status_layout.addWidget(self.stop_button)
        status_layout.addWidget(self.test_button)
        
        server_layout.addLayout(status_layout)
        
        # Настройки порта
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Порт:"))
        
        self.port_spinbox = QSpinBox()
        self.port_spinbox.setRange(1000, 65535)
        self.port_spinbox.setValue(8000)
        port_layout.addWidget(self.port_spinbox)
        port_layout.addStretch()
        
        server_layout.addLayout(port_layout)
        
        # Лог сервера
        self.server_log = QTextEdit()
        self.server_log.setReadOnly(True)
        self.server_log.setMaximumHeight(200)
        server_layout.addWidget(QLabel("Лог сервера:"))
        server_layout.addWidget(self.server_log)
        
        layout.addWidget(server_group)
        
        # Тестирование endpoints
        test_group = QGroupBox("Тестирование Webhook Endpoints")
        test_layout = QVBoxLayout(test_group)
        
        # Кнопки тестирования
        test_buttons_layout = QHBoxLayout()
        
        self.test_health_button = ModernButton("Health Check", theme_manager=self.theme_manager)
        self.test_health_button.clicked.connect(self.test_health)
        
        self.test_resend_button = ModernButton("Resend Webhook", theme_manager=self.theme_manager)
        self.test_resend_button.clicked.connect(self.test_resend_webhook)
        
        
        self.view_events_button = ModernButton("Просмотр событий", theme_manager=self.theme_manager)
        self.view_events_button.clicked.connect(self.view_events)
        
        test_buttons_layout.addWidget(self.test_health_button)
        test_buttons_layout.addWidget(self.test_resend_button)
        test_buttons_layout.addWidget(self.view_events_button)
        
        test_layout.addLayout(test_buttons_layout)
        
        # Результаты тестов
        self.test_results = QTextEdit()
        self.test_results.setReadOnly(True)
        self.test_results.setMaximumHeight(150)
        test_layout.addWidget(QLabel("Результаты тестов:"))
        test_layout.addWidget(self.test_results)
        
        layout.addWidget(test_group)
    
    def start_server(self):
        """Запуск сервера"""
        port = self.port_spinbox.value()
        self.server_manager.start_server(port)
        self.server_log.append(f"Запуск сервера на порту {port}...")
    
    def stop_server(self):
        """Остановка сервера"""
        self.server_manager.stop_server()
        self.server_log.append("Остановка сервера...")
    
    def test_server(self):
        """Тест доступности сервера"""
        threading.Thread(target=self._test_server_async, daemon=True).start()
    
    def _test_server_async(self):
        """Асинхронный тест сервера"""
        try:
            port = self.port_spinbox.value()
            try:
                import httpx
                with httpx.Client(timeout=5.0) as client:
                    response = client.get(f"http://localhost:{port}/health")
                    if response.status_code == 200:
                        QTimer.singleShot(0, lambda: self.test_results.append("✅ Сервер доступен"))
                    else:
                        QTimer.singleShot(0, lambda: self.test_results.append(f"❌ Сервер вернул статус: {response.status_code}"))
            except ImportError:
                # Используем стандартную библиотеку если httpx недоступен
                import urllib.request
                import urllib.error
                try:
                    with urllib.request.urlopen(f"http://localhost:{port}/health", timeout=5) as response:
                        if response.status == 200:
                            QTimer.singleShot(0, lambda: self.test_results.append("✅ Сервер доступен"))
                        else:
                            QTimer.singleShot(0, lambda: self.test_results.append(f"❌ Сервер вернул статус: {response.status}"))
                except urllib.error.URLError as e:
                    QTimer.singleShot(0, lambda: self.test_results.append(f"❌ Ошибка подключения: {e}"))
        except Exception as e:
            QTimer.singleShot(0, lambda: self.test_results.append(f"❌ Неожиданная ошибка: {e}"))
            import traceback
            traceback.print_exc()
    
    def test_health(self):
        """Тест health endpoint"""
        threading.Thread(target=self._test_health_async, daemon=True).start()
    
    def _test_health_async(self):
        """Асинхронный тест health"""
        try:
            port = self.port_spinbox.value()
            try:
                import httpx
                with httpx.Client(timeout=5.0) as client:
                    response = client.get(f"http://localhost:{port}/health")
                    message = f"Health: {response.status_code} - {response.text}"
                    QTimer.singleShot(0, lambda msg=message: self.test_results.append(msg))
            except ImportError:
                import urllib.request
                import urllib.error
                try:
                    with urllib.request.urlopen(f"http://localhost:{port}/health", timeout=5) as response:
                        data = response.read().decode('utf-8')
                        self.test_results.append(f"Health: {response.status} - {data}")
                except urllib.error.URLError as e:
                    self.test_results.append(f"Health test error: {e}")
        except Exception as e:
            self.test_results.append(f"Health test error: {e}")
            import traceback
            traceback.print_exc()
    
    def test_resend_webhook(self):
        """Тест Resend webhook"""
        threading.Thread(target=self._test_resend_async, daemon=True).start()
    
    def _test_resend_async(self):
        """Асинхронный тест Resend webhook"""
        try:
            port = self.port_spinbox.value()
            test_data = {
                "type": "email.delivered",
                "data": {
                    "email_id": "gui_test_123",
                    "to": "test@example.com"
                }
            }
            
            try:
                import httpx
                with httpx.Client(timeout=5.0) as client:
                    response = client.post(
                        f"http://localhost:{port}/resend/webhook",
                        json=test_data,
                        headers={"Content-Type": "application/json"}
                    )
                    self.test_results.append(f"Resend webhook: {response.status_code} - {response.text}")
            except ImportError:
                import urllib.request
                import urllib.error
                import json
                try:
                    data = json.dumps(test_data).encode('utf-8')
                    req = urllib.request.Request(
                        f"http://localhost:{port}/resend/webhook",
                        data=data,
                        headers={'Content-Type': 'application/json'}
                    )
                    with urllib.request.urlopen(req, timeout=5) as response:
                        result = response.read().decode('utf-8')
                        self.test_results.append(f"Resend webhook: {response.status} - {result}")
                except urllib.error.URLError as e:
                    self.test_results.append(f"Resend webhook error: {e}")
        except Exception as e:
            self.test_results.append(f"Resend webhook error: {e}")
            import traceback
            traceback.print_exc()
    
    
    def view_events(self):
        """Просмотр событий"""
        threading.Thread(target=self._view_events_async, daemon=True).start()
    
    def _view_events_async(self):
        """Асинхронный просмотр событий"""
        try:
            port = self.port_spinbox.value()
            try:
                import httpx
                with httpx.Client(timeout=5.0) as client:
                    response = client.get(f"http://localhost:{port}/events?limit=5")
                    if response.status_code == 200:
                        events = response.json()
                        self.test_results.append(f"События ({len(events)}):")
                        for event in events[:3]:
                            self.test_results.append(f"  • {event.get('event_type')} - {event.get('recipient')}")
                    else:
                        self.test_results.append(f"Ошибка получения событий: {response.status_code}")
            except ImportError:
                import urllib.request
                import urllib.error
                import json
                try:
                    with urllib.request.urlopen(f"http://localhost:{port}/events?limit=5", timeout=5) as response:
                        data = response.read().decode('utf-8')
                        events = json.loads(data)
                        self.test_results.append(f"События ({len(events)}):")
                        for event in events[:3]:
                            self.test_results.append(f"  • {event.get('event_type')} - {event.get('recipient')}")
                except urllib.error.URLError as e:
                    self.test_results.append(f"Events error: {e}")
                except json.JSONDecodeError as e:
                    self.test_results.append(f"JSON decode error: {e}")
        except Exception as e:
            self.test_results.append(f"Events error: {e}")
            import traceback
            traceback.print_exc()
    
    def on_server_started(self):
        """Обработчик запуска сервера"""
        self.status_label.setText("Статус: Запущен")
        self.status_label.setStyleSheet("font-weight: bold; color: green;")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
    
    def on_server_stopped(self):
        """Обработчик остановки сервера"""
        self.status_label.setText("Статус: Остановлен")
        self.status_label.setStyleSheet("font-weight: bold; color: red;")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
    
    def on_server_error(self, error_msg):
        """Обработчик ошибки сервера"""
        self.server_log.append(f"❌ Ошибка: {error_msg}")
    
    def on_server_output(self, output):
        """Обработчик вывода сервера"""
        self.server_log.append(output)

class SquareCheckBox(QCheckBox):
    """Кастомный чекбокс: пустой квадрат + белая галочка без заливки."""
    def __init__(self, text: str = '', parent=None, box_size: int = 18):
        super().__init__(text, parent)
        self._hover = False
        self._pressed = False
        self._box_size = box_size
        self.setCursor(Qt.PointingHandCursor)
        # Убираем стандартные отступы чтобы контролировать сами
        self.setStyleSheet("QCheckBox{spacing:8px;}")

    def enterEvent(self, e):
        self._hover = True
        self.update()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hover = False
        self.update()
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        self._pressed = True
        self.update()
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self._pressed = False
        self.update()
        super().mouseReleaseEvent(e)

    def sizeHint(self):
        fm = self.fontMetrics()
        text_w = fm.horizontalAdvance(self.text())
        h = max(self._box_size, fm.height()) + 4
        return QSize(self._box_size + 8 + text_w, h)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        box = self._box_size
        x = 0
        y = (rect.height() - box) // 2
        box_rect = QRect(x, y, box, box)

        # Цвета
        border_color = QColor('#4A5568')
        if self.isChecked():
            border_color = QColor('#6366F1')
        if self._hover:
            # Лёгкое подсвечивание границы при hover
            if not self.isChecked():
                border_color = QColor('#6366F1')
        fill_color = QColor(0,0,0,0)  # прозрачный
        if self._pressed:
            fill_color = QColor(255,255,255,20)

        # Рисуем фон (очень лёгкий при нажатии)
        if fill_color.alpha() > 0:
            p.setPen(Qt.NoPen)
            p.setBrush(fill_color)
            p.drawRoundedRect(box_rect, 4, 4)

        # Рамка
        pen = QPen(border_color, 2)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(box_rect.adjusted(1,1,-1,-1), 4, 4)

        # Галочка
        if self.isChecked():
            path = QPainterPath()
            # пропорциональная галочка
            path.moveTo(x + box*0.22, y + box*0.55)
            path.lineTo(x + box*0.45, y + box*0.78)
            path.lineTo(x + box*0.80, y + box*0.28)
            tick_pen = QPen(QColor('#FFFFFF'), 2.4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            p.setPen(tick_pen)
            p.drawPath(path)

        # Текст
        p.setPen(QColor('#FFFFFF'))
        fm = p.fontMetrics()
        text_x = x + box + 8
        text_y = (rect.height() + fm.ascent() - fm.descent()) // 2
        p.drawText(text_x, text_y, self.text())

        p.end()


class EnhancedMainWindow(QMainWindow):
    """Расширенное главное окно с полным управлением системой"""
    
    def __init__(self, theme_manager: ThemeManager):
        super().__init__()
        self.theme_manager = theme_manager
        self._mailer = MailerService()
        
        # Подключение сигналов mailer'а
        self._mailer.started.connect(self._on_mailer_started)
        self._mailer.progress.connect(self._on_mailer_progress)
        self._mailer.finished.connect(self._on_mailer_finished)
        self._mailer.error.connect(self._on_mailer_error)
        self._mailer.cancelled.connect(self._on_mailer_cancelled)
        
        self.setWindowTitle("Система массовой рассылки - Полное управление")
        self.setMinimumSize(1200, 800)  # Минимальный размер
        self.resize(1400, 900)
        
        self._init_ui()
        self._init_log_handler()
        
        # Подключение событий темы
        self.theme_manager.paletteChanged.connect(self._on_palette_changed)
    
    def _init_ui(self):
        """Инициализация интерфейса"""
        root = QWidget()
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)  # Убираем внешние отступы
        layout.setSpacing(0)  # Убираем отступы между элементами
        
        # Боковая панель навигации
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(280)  # Фиксированная ширина сайдбара
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(16, 16, 16, 16)  # Отступы внутри сайдбара
        side_layout.setSpacing(8)  # Отступы между элементами
        
        # Логотип/заголовок
        title_label = QLabel("📧 Mail System")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 20px; color: #6366F1;")
        side_layout.addWidget(title_label)
        
        # Список разделов
        self.list_widget = QListWidget()
        self.list_widget.setMinimumHeight(400)  # Минимальная высота списка
        
        section_items = [
            ("📊 Dashboard", "section_dashboard"),
            ("🚀 Рассылки", "section_campaigns"),
            ("🔗 Webhook", "section_webhook_manager"),
            ("📈 Мониторинг", "section_system_monitor"),
            ("⚙️ Конфигурация", "section_config_manager"),
            ("📝 Шаблоны", "section_template_editor"),
            ("📋 Статистика", "section_statistics"),
            ("👥 Получатели", "section_recipients"),
            ("📄 Логи", "section_logs"),
            ("🔧 Настройки", "section_settings"),
        ]
        
        for display_name, key in section_items:
            item = QListWidgetItem(display_name)
            item.setData(Qt.UserRole, key)
            self.list_widget.addItem(item)
        
        self.list_widget.currentRowChanged.connect(self._on_section_changed)
        side_layout.addWidget(self.list_widget)
        
        side_layout.addStretch(1)
        
        # Основная область контента
        self.stack = QStackedWidget()
        self.stack.setContentsMargins(0, 0, 0, 0)  # Убираем отступы стека
        
        # Создание страниц для каждого раздела
        self._create_pages()
        
        layout.addWidget(sidebar)
        layout.addWidget(self.stack, 1)  # Расширяемая область
        
        self.setCentralWidget(root)
        self.list_widget.setCurrentRow(0)
    
    def _create_pages(self):
        """Создание страниц для всех разделов"""
        
        # Dashboard
        dashboard_page = self._create_dashboard_page()
        self.stack.addWidget(dashboard_page)
        
        # Campaigns (используем существующую логику)
        campaigns_page = self._create_campaigns_page()
        self.stack.addWidget(campaigns_page)
        
        # Webhook Manager
        webhook_page = WebhookManagerWidget(self.theme_manager)
        self.stack.addWidget(webhook_page)
        
        # System Monitor
        monitor_page = SystemMonitorWidget(self.theme_manager)
        self.stack.addWidget(monitor_page)
        
        # Config Manager
        config_page = ConfigManagerWidget(self.theme_manager)
        self.stack.addWidget(config_page)
        
        # Template Editor
        template_page = self._create_template_editor_page()
        self.stack.addWidget(template_page)
        
        # Statistics 
        stats_page = self._create_statistics_page()
        self.stack.addWidget(stats_page)
        
        # Recipients
        recipients_page = self._create_recipients_page()
        self.stack.addWidget(recipients_page)
        
        # Logs
        logs_page = self._create_logs_page()
        self.stack.addWidget(logs_page)
        
        # Settings
        settings_page = self._create_advanced_settings_page()
        self.stack.addWidget(settings_page)
    
    def _create_dashboard_page(self):
        """Создание страницы Dashboard"""
        page = QWidget()
        layout = QVBoxLayout(page)
        apply_margins(layout, 'page')
        apply_spacing(layout, 'lg')
        
        # Заголовок
        title = QLabel("📊 Dashboard")
        apply_heading_style(title, 'h1')
        title.setStyleSheet("color: #6366F1; padding-bottom: 8px; margin-bottom: 16px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Карточки статистики в горизонтальном ряду
        cards_container = QWidget()
        cards_layout = QHBoxLayout(cards_container)
        cards_layout.setContentsMargins(0, 16, 0, 16)  # Отступы сверху и снизу
        cards_layout.setSpacing(20)
        
        self.dashboard_sent_card = StatsCard("Отправлено", "0", 0.0, accent=QColor('#6366F1'), parent=None, theme_manager=self.theme_manager)
        self.dashboard_success_card = StatsCard("Успешно", "0%", 0.0, accent=QColor('#10B981'), parent=None, theme_manager=self.theme_manager)
        self.dashboard_failed_card = StatsCard("Ошибок", "0", 0.0, accent=QColor('#EF4444'), parent=None, theme_manager=self.theme_manager)
        self.dashboard_quota_card = StatsCard("Квота", "0/100", 0.0, accent=QColor('#06B6D4'), parent=None, theme_manager=self.theme_manager)
        
        cards_layout.addWidget(self.dashboard_sent_card)
        cards_layout.addWidget(self.dashboard_success_card)
        cards_layout.addWidget(self.dashboard_failed_card)
        cards_layout.addWidget(self.dashboard_quota_card)
        
        layout.addWidget(cards_container)
        
        # Разделитель с увеличенным отступом
        layout.addSpacing(24)  # Увеличиваем отступ между карточками и быстрыми действиями
        
        # Быстрые действия с контейнером для отступов
        actions_container = QWidget()
        actions_container_layout = QVBoxLayout(actions_container)
        actions_container_layout.setContentsMargins(8, 8, 8, 8)  # Уменьшаем внешние отступы
        
        actions_group = QGroupBox("Быстрые действия")
        # Делаем заголовок видимым с небольшим отступом от границы
        actions_group.setStyleSheet("""
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 2px 8px;
                top: -2px;
                left: 10px;
                background-color: #2D3748;
                color: white;
                border-radius: 4px;
            }
        """)
        actions_layout = QHBoxLayout(actions_group)
        actions_layout.setContentsMargins(8, 8, 8, 8)  # Уменьшаем стандартные отступы
        actions_layout.setSpacing(12)
        
        quick_campaign_btn = ModernButton("🚀 Новая рассылка", variant="primary", theme_manager=self.theme_manager)
        quick_campaign_btn.clicked.connect(lambda: self.list_widget.setCurrentRow(1))
        
        webhook_status_btn = ModernButton("🔗 Webhook статус", variant="secondary", theme_manager=self.theme_manager)
        webhook_status_btn.clicked.connect(lambda: self.list_widget.setCurrentRow(2))
        
        view_logs_btn = ModernButton("📄 Просмотр логов", variant="tertiary", theme_manager=self.theme_manager)
        view_logs_btn.clicked.connect(lambda: self.list_widget.setCurrentRow(8))
        
        actions_layout.addWidget(quick_campaign_btn)
        actions_layout.addWidget(webhook_status_btn)
        actions_layout.addWidget(view_logs_btn)
        actions_layout.addStretch()
        
        actions_container_layout.addWidget(actions_group)
        layout.addWidget(actions_container)
        
        # Разделитель с увеличенным отступом
        layout.addSpacing(24)  # Увеличиваем отступ между быстрыми действиями и активностью
        
        # Последняя активность с контейнером для отступов
        activity_container = QWidget()
        activity_container_layout = QVBoxLayout(activity_container)
        activity_container_layout.setContentsMargins(8, 8, 8, 12)  # Уменьшаем внешние отступы
        
        # Последняя активность
        activity_group = QGroupBox("Последняя активность")
        # Делаем заголовок видимым с небольшим отступом от границы
        activity_group.setStyleSheet("""
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 2px 8px;
                top: -2px;
                left: 10px;
                background-color: #2D3748;
                color: white;
                border-radius: 4px;
            }
        """)
        activity_layout = QVBoxLayout(activity_group)
        activity_layout.setContentsMargins(8, 8, 8, 8)  # Уменьшаем стандартные отступы
        activity_layout.setSpacing(8)  # Отступ между элементами
        
        self.activity_list = QTextEdit()
        self.activity_list.setReadOnly(True)
        self.activity_list.setMaximumHeight(150)
        self.activity_list.setLineWrapMode(QTextEdit.WidgetWidth)
        self.activity_list.setStyleSheet("""
            QTextEdit {
                padding: 12px;
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                background-color: transparent;
                font-size: 13px;
                line-height: 1.5;
            }
        """)
        activity_layout.addWidget(self.activity_list)
        
        activity_container_layout.addWidget(activity_group)
        layout.addWidget(activity_container)
        layout.addStretch()
        
        # Обновление статистики
        self.dashboard_timer = QTimer()
        self.dashboard_timer.timeout.connect(self._update_dashboard)
        self.dashboard_timer.start(10000)
        self._update_dashboard()
        
        return page
    
    def _create_campaigns_page(self):
        """Создание страницы рассылок (упрощённая версия)"""
        page = QWidget()
        main_layout = QVBoxLayout(page)
        apply_margins(main_layout, 'section')
        apply_spacing(main_layout, 'md')
        
        title = QLabel("🚀 Управление рассылками")
        apply_heading_style(title, 'h1')
        title.setStyleSheet("color: #6366F1; padding-bottom: 8px; margin-bottom: 16px;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # Создаем scroll area для содержимого
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(32, 32, 32, 32)  # Увеличиваем отступы
        layout.setSpacing(24)
        
        # Форма рассылки (убираем GroupBox, растягиваем на всю страницу)
        form_layout = QVBoxLayout()
        form_layout.setSpacing(20)  # Увеличиваем расстояние между элементами
        
        # Поля формы с правильным выравниванием текста
        # Файл получателей
        rec_container = QWidget()
        rec_layout = QHBoxLayout(rec_container)
        rec_layout.setContentsMargins(0, 8, 0, 8)
        rec_layout.setSpacing(12)
        rec_layout.setAlignment(Qt.AlignVCenter)  # Выравниваем по вертикальному центру
        
        self.recipients_path = FloatingTextField("Файл получателей", "", "recipients.csv", parent=None, theme_manager=self.theme_manager)
        btn_choose_rec = ModernButton("Выбрать", variant="secondary", theme_manager=self.theme_manager)
        btn_choose_rec.clicked.connect(lambda: self._choose_file_ft(self.recipients_path, "CSV/XLSX/JSON (*.csv *.xlsx *.json)"))
        
        rec_layout.addWidget(self.recipients_path, 1)
        rec_layout.addWidget(btn_choose_rec)
        form_layout.addWidget(rec_container)
        
        # Файл шаблона
        tpl_container = QWidget()
        tpl_layout = QHBoxLayout(tpl_container)
        tpl_layout.setContentsMargins(0, 8, 0, 8)
        tpl_layout.setSpacing(12)
        tpl_layout.setAlignment(Qt.AlignVCenter)  # Выравниваем по вертикальному центру
        
        self.template_path = FloatingTextField("Файл шаблона", "", "template.html.j2", parent=None, theme_manager=self.theme_manager)
        btn_choose_tpl = ModernButton("Выбрать", variant="secondary", theme_manager=self.theme_manager)
        btn_choose_tpl.clicked.connect(lambda: self._choose_file_ft(self.template_path, "Templates (*.j2 *.html *.txt)"))
        
        tpl_layout.addWidget(self.template_path, 1)
        tpl_layout.addWidget(btn_choose_tpl)
        form_layout.addWidget(tpl_container)
        
        # Тема письма
        subject_container = QWidget()
        subject_layout = QVBoxLayout(subject_container)
        subject_layout.setContentsMargins(0, 8, 0, 8)
        
        self.subject_edit = FloatingTextField("Тема письма", parent=None, theme_manager=self.theme_manager)
        subject_layout.addWidget(self.subject_edit)
        form_layout.addWidget(subject_container)
        
        # Дополнительные настройки с темным фоном как у других блоков
        settings_container = QWidget()
        settings_layout = QHBoxLayout(settings_container)
        settings_layout.setContentsMargins(0, 24, 0, 24)  # Отступы
        settings_layout.setSpacing(24)  # Расстояние между блоками
        
        # Параллельность - компактный горизонтальный дизайн
        parallel_group = QWidget()
        parallel_group.setMinimumWidth(200)
        parallel_group.setMaximumHeight(80)  # Уменьшили высоту
        parallel_layout = QHBoxLayout(parallel_group)  # Горизонтальный layout
        parallel_layout.setContentsMargins(16, 16, 16, 16)
        parallel_layout.setSpacing(12)
        parallel_layout.setAlignment(Qt.AlignVCenter)
        
        parallel_label = QLabel("Параллельность:")
        parallel_label.setStyleSheet("font-weight: bold; color: white; font-size: 14px;")
        parallel_label.setAlignment(Qt.AlignVCenter)
        parallel_layout.addWidget(parallel_label)
        
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setRange(1, 100)
        self.concurrent_spin.setValue(10)
        self.concurrent_spin.setAlignment(Qt.AlignCenter)
        self.concurrent_spin.setMinimumHeight(32)  # Уменьшили высоту
        self.concurrent_spin.setMaximumWidth(80)   # Ограничили ширину
        self.concurrent_spin.setStyleSheet("""
            QSpinBox {
                border: 1px solid #4A5568;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
                font-weight: bold;
                background-color: transparent;
                color: white;
                min-width: 60px;
            }
            QSpinBox:focus {
                border-color: #6366F1;
                outline: none;
            }
            QSpinBox:hover {
                border-color: #718096;
                background-color: rgba(55, 65, 81, 0.3);
            }
            QSpinBox::up-button, QSpinBox::down-button {
                border: 1px solid #4A5568;
                width: 18px;
                border-radius: 3px;
                margin: 1px;
                background-color: rgba(74, 85, 104, 0.8);
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #6366F1;
                border-color: #6366F1;
            }
            QSpinBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 7px solid white;
                width: 0;
                height: 0;
                margin: 2px;
            }
        """)
        parallel_layout.addWidget(self.concurrent_spin)
        
        # Фон как у остальной страницы - без обводки
        parallel_group.setStyleSheet("""
            QWidget {
                border: none;
                border-radius: 0px;
                background-color: transparent;
            }
        """)
        settings_layout.addWidget(parallel_group)
        
        # Тестовый режим - компактный горизонтальный дизайн
        test_group = QWidget()
        test_group.setMinimumWidth(200)
        test_group.setMaximumHeight(80)  # Уменьшили высоту
        test_layout = QHBoxLayout(test_group)  # Горизонтальный layout
        test_layout.setContentsMargins(16, 16, 16, 16)
        test_layout.setSpacing(12)
        test_layout.setAlignment(Qt.AlignVCenter)
        
        test_label = QLabel("Тестовый режим:")
        test_label.setStyleSheet("font-weight: bold; color: white; font-size: 14px;")
        test_label.setAlignment(Qt.AlignVCenter)
        test_layout.addWidget(test_label)
        
        self.dry_run_switch = IOSSwitch(False, theme_manager=self.theme_manager)
        test_layout.addWidget(self.dry_run_switch, 0, Qt.AlignVCenter)
        
        # Фон как у остальной страницы - без обводки
        test_group.setStyleSheet("""
            QWidget {
                border: none;
                border-radius: 0px;
                background-color: transparent;
            }
        """)
        settings_layout.addWidget(test_group)
        
        settings_layout.addStretch()
        form_layout.addWidget(settings_container)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        self.start_btn = ModernButton("▶️ Запустить", variant="primary", theme_manager=self.theme_manager)
        self.start_btn.clicked.connect(self._start_campaign)
        
        self.cancel_btn = ModernButton("⏹ Остановить", variant="secondary", theme_manager=self.theme_manager)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel_campaign)
        
        buttons_layout.addWidget(self.start_btn)
        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addStretch()
        
        form_layout.addLayout(buttons_layout)
        
        # Прогресс
        progress_layout = QHBoxLayout()
        
        self.progress_ring = ProgressRing(size=36, thickness=4, theme_manager=self.theme_manager)
        self.progress_ring.setVisible(False)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        self.progress_label = QLabel("Готов к запуску")
        
        progress_layout.addWidget(self.progress_ring)
        progress_layout.addWidget(self.progress_bar, 1)
        progress_layout.addWidget(self.progress_label)
        
        form_layout.addLayout(progress_layout)
        
        # Добавляем форму напрямую в основной layout
        layout.addLayout(form_layout)
        layout.addStretch()
        
        # Устанавливаем содержимое в scroll area
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
        return page
    
    def _create_template_editor_page(self):
        """Создание страницы редактора шаблонов"""
        page = QWidget()
        layout = QVBoxLayout(page)
        apply_margins(layout, 'page')
        apply_spacing(layout, 'lg')
        # Заголовок (прижат к верху)
        title = QLabel("📝 Редактор шаблонов")
        apply_heading_style(title, 'h1')
        title.setStyleSheet("color: #6366F1; margin: 0 0 20px 0; padding: 0;")
        layout.addWidget(title, 0, Qt.AlignTop)
        
        # Основная область с разделением
        splitter = QSplitter(Qt.Horizontal)

        # Левая панель - список шаблонов
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        new_template_btn = ModernButton("+ Новый", variant="primary", theme_manager=self.theme_manager)
        delete_template_btn = ModernButton("Удалить", variant="secondary", theme_manager=self.theme_manager)
        buttons_layout.addWidget(new_template_btn)
        buttons_layout.addWidget(delete_template_btn)
        left_layout.addLayout(buttons_layout)
        
        # Список шаблонов
        self.templates_list = QListWidget()
        self.templates_list.setStyleSheet("""
            QListWidget {
                background-color: #2D3748;
                border: 1px solid #4A5568;
                border-radius: 8px;
                color: white;
                padding: 8px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
                margin: 2px;
            }
            QListWidget::item:selected {
                background-color: #6366F1;
            }
            QListWidget::item:hover {
                background-color: #374151;
            }
        """)
        left_layout.addWidget(self.templates_list)
        
        # Правая панель - редактор
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)
        
        # Поле для названия шаблона
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Название:"))
        self.template_name_edit = QLineEdit()
        self.template_name_edit.setStyleSheet("""
            QLineEdit {
                background-color: #2D3748;
                border: 1px solid #4A5568;
                border-radius: 6px;
                color: white;
                padding: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #6366F1;
            }
        """)
        name_layout.addWidget(self.template_name_edit)
        right_layout.addLayout(name_layout)
        
        # Поле для темы письма
        subject_layout = QHBoxLayout()
        subject_layout.addWidget(QLabel("Тема письма:"))
        self.template_subject_edit = QLineEdit()
        self.template_subject_edit.setStyleSheet(self.template_name_edit.styleSheet())
        subject_layout.addWidget(self.template_subject_edit)
        right_layout.addLayout(subject_layout)
        
        # Редактор содержимого
        content_label = QLabel("Содержимое (текст письма):")
        content_label.setStyleSheet("font-weight: bold; margin-top: 16px;")
        right_layout.addWidget(content_label)

        self.template_content_edit = QTextEdit()
        self.template_content_edit.setStyleSheet("""
            QTextEdit {
                background-color: #2D3748;
                border: 1px solid #4A5568;
                border-radius: 6px;
                color: white;
                padding: 12px;
                font-family: 'Monaco', 'Menlo', monospace;
                font-size: 13px;
                line-height: 1.4;
            }
            QTextEdit:focus {
                border-color: #6366F1;
            }
        """)
        self.template_content_edit.setPlainText("""Привет, {{name}}!

Это пример письма рассылки.

Переменные для подстановки:
  • {{name}} — имя получателя
  • {{email}} — email получателя
  • {{subject}} — тема письма
  • {{date}} — текущая дата

Напишите здесь текст вашего сообщения. Позже можно экспортировать как HTML.

С уважением,
Команда рассылки""")
        right_layout.addWidget(self.template_content_edit)
        # Подключаем подсветку HTML / Jinja
        self._template_highlighter = HtmlHighlighter(self.template_content_edit.document())
        
        # Кнопки управления шаблоном
        template_buttons_layout = QHBoxLayout()
        save_template_btn = ModernButton("💾 Сохранить", variant="primary", theme_manager=self.theme_manager)
        preview_template_btn = ModernButton("👁 Предпросмотр", variant="secondary", theme_manager=self.theme_manager)
        template_buttons_layout.addWidget(save_template_btn)
        template_buttons_layout.addWidget(preview_template_btn)
        template_buttons_layout.addStretch()
        right_layout.addLayout(template_buttons_layout)
        
        # Добавляем панели в splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([320, 780])
        layout.addWidget(splitter, 1)
        
        # Подключаем события
        new_template_btn.clicked.connect(self._create_new_template)
        delete_template_btn.clicked.connect(self._delete_template)
        save_template_btn.clicked.connect(self._save_template)
        preview_template_btn.clicked.connect(self._preview_template)
        self.templates_list.itemSelectionChanged.connect(self._load_template)
        
        # Загружаем существующие шаблоны
        self._load_templates()
        return page
    
    def _create_new_template(self):
        """Создание нового шаблона"""
        self.template_name_edit.setText("Новый шаблон")
        self.template_subject_edit.setText("Тема письма")
        self.template_content_edit.setPlainText("Содержимое шаблона...")
    
    def _delete_template(self):
        """Удаление выбранного шаблона"""
        current_item = self.templates_list.currentItem()
        if current_item:
            reply = QMessageBox.question(self, "Подтверждение", 
                                       f"Удалить шаблон '{current_item.text()}'?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                # Здесь будет логика удаления из файла/базы
                self.templates_list.takeItem(self.templates_list.row(current_item))
    
    def _save_template(self):
        """Сохранение текущего шаблона"""
        name = self.template_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название шаблона!")
            return
        
        # Здесь будет логика сохранения в файл/базу
        # Пока просто добавляем в список, если его там нет
        items = [self.templates_list.item(i).text() for i in range(self.templates_list.count())]
        if name not in items:
            self.templates_list.addItem(name)
        
        QMessageBox.information(self, "Успех", f"Шаблон '{name}' сохранен!")
    
    def _preview_template(self):
        """Предпросмотр шаблона"""
        content = self.template_content_edit.toPlainText()
        subject = self.template_subject_edit.text()
        
        # Простая подстановка переменных для демонстрации
        preview_content = content.replace("{{name}}", "Иван Петров")
        preview_content = preview_content.replace("{{email}}", "ivan@example.com") 
        preview_content = preview_content.replace("{{subject}}", subject)
        preview_content = preview_content.replace("{{date}}", "23 сентября 2025")
        
        # Создаем окно предпросмотра
        dialog = QDialog(self)
        dialog.setWindowTitle("Предпросмотр шаблона")
        dialog.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(dialog)
        
        preview_label = QLabel("Предпросмотр:")
        preview_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(preview_label)
        
        preview_text = QTextEdit()
        preview_text.setHtml(preview_content)
        preview_text.setReadOnly(True)
        layout.addWidget(preview_text)
        
        close_btn = ModernButton("Закрыть", variant="secondary", theme_manager=self.theme_manager)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec_()
    
    def _load_template(self):
        """Загрузка выбранного шаблона"""
        current_item = self.templates_list.currentItem()
        if current_item:
            # Здесь будет логика загрузки из файла/базы
            # Пока просто заполняем примерными данными
            template_name = current_item.text()
            self.template_name_edit.setText(template_name)
            self.template_subject_edit.setText(f"Тема для {template_name}")
    
    def _load_templates(self):
        """Загрузка списка существующих шаблонов"""
        # Здесь будет логика загрузки из файла/базы
        # Пока добавляем примерные шаблоны
        example_templates = [
            "Приветственное письмо",
            "Новости компании", 
            "Специальное предложение",
            "Подтверждение заказа"
        ]
        for template in example_templates:
            self.templates_list.addItem(template)
    
    def _create_statistics_page(self):
        """Создание страницы подробной статистики"""
        page = QWidget()
        layout = QVBoxLayout(page)
        apply_margins(layout, 'page')
        apply_spacing(layout, 'lg')
        
        # Заголовок
        title = QLabel("📋 Подробная статистика")
        apply_heading_style(title, 'h1')
        title.setStyleSheet("color: #6366F1; padding-bottom: 8px; margin-bottom: 16px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Фильтры периода
        filters_layout = QHBoxLayout()
        filters_layout.addWidget(QLabel("Период:"))
        
        self.stats_period_combo = QComboBox()
        self.stats_period_combo.addItems(["Сегодня", "За неделю", "За месяц", "За 3 месяца", "За год", "Все время"])
        self.stats_period_combo.setCurrentText("За месяц")
        self.stats_period_combo.setStyleSheet("""
            QComboBox {
                background-color: #2D3748;
                border: 1px solid #4A5568;
                border-radius: 6px;
                color: white;
                padding: 8px;
                min-width: 120px;
            }
            QComboBox:focus {
                border-color: #6366F1;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        filters_layout.addWidget(self.stats_period_combo)
        
        refresh_btn = ModernButton("🔄 Обновить", variant="secondary", theme_manager=self.theme_manager)
        filters_layout.addWidget(refresh_btn)
        filters_layout.addStretch()
        
        layout.addLayout(filters_layout)
        
        # Основные метрики в карточках
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(16)
        
        self.total_campaigns_card = StatsCard("Всего кампаний", "15", 12.5, accent=QColor('#8B5CF6'), parent=None, theme_manager=self.theme_manager)
        self.total_emails_card = StatsCard("Отправлено писем", "1,234", 8.3, accent=QColor('#06B6D4'), parent=None, theme_manager=self.theme_manager)
        self.avg_open_rate_card = StatsCard("Средний Open Rate", "24.7%", 2.1, accent=QColor('#10B981'), parent=None, theme_manager=self.theme_manager)
        self.avg_click_rate_card = StatsCard("Средний CTR", "3.2%", -0.8, accent=QColor('#F59E0B'), parent=None, theme_manager=self.theme_manager)
        
        # Компактные карточки
        for card in [self.total_campaigns_card, self.total_emails_card, self.avg_open_rate_card, self.avg_click_rate_card]:
            card.setMinimumHeight(110)
            card.setMaximumHeight(120)
            metrics_layout.addWidget(card)
        
        layout.addLayout(metrics_layout)
        
        # Область с графиками и таблицами
        content_splitter = QSplitter(Qt.Vertical)
        
        # Верхняя часть - графики
        charts_widget = QWidget()
        charts_layout = QHBoxLayout(charts_widget)
        
        # График отправок по времени (имитация)
        time_chart_group = QGroupBox("Динамика отправок")
        time_chart_layout = QVBoxLayout(time_chart_group)
        time_chart_layout.setContentsMargins(0,0,0,0)
        time_chart_layout.setSpacing(0)
        
        self.time_chart_area = QTextEdit()
        self.time_chart_area.setMaximumHeight(9999)
        self.time_chart_area.setStyleSheet("""
            QTextEdit {
                background-color: #1A202C;
                border: 1px solid #4A5568;
                border-radius: 8px;
                color: #10B981;
                font-family: monospace;
                padding: 12px;
            }
        """)
        self.time_chart_area.setPlainText("""📈 График отправок за последние 30 дней:

Пн  ████████████████ 156 писем
Вт  ██████████████████████ 234 писем  
Ср  ██████████ 89 писем
Чт  ████████████████████ 198 писем
Пт  ███████████████████████████ 287 писем
Сб  ██████ 45 писем
Вс  ████ 23 писем

📊 Всего за период: 1,032 писем
📈 Рост по сравнению с предыдущим периодом: +12.3%""")
        self.time_chart_area.setReadOnly(True)
        time_chart_layout.addWidget(self.time_chart_area)
        
        # Круговая диаграмма статусов
        status_chart_group = QGroupBox("Статусы доставки")
        status_chart_layout = QVBoxLayout(status_chart_group)
        status_chart_layout.setContentsMargins(0,0,0,0)
        status_chart_layout.setSpacing(0)
        
        self.status_chart_area = QTextEdit()
        self.status_chart_area.setMaximumHeight(9999)
        self.status_chart_area.setStyleSheet(self.time_chart_area.styleSheet().replace("#10B981", "#6366F1"))
        self.status_chart_area.setPlainText("""🔵 Статусы доставки:

✅ Доставлено успешно:     847 (82.1%)
❌ Ошибки доставки:        123 (11.9%) 
⏳ В очереди:              45 (4.4%)
🔄 Повторные попытки:      17 (1.6%)

📋 Основные ошибки:
• Неверный email адрес: 45%
• Переполнение почтового ящика: 28%
• Блокировка спам-фильтром: 19%  
• Временная недоступность: 8%""")
        self.status_chart_area.setReadOnly(True)
        status_chart_layout.addWidget(self.status_chart_area)
        
        charts_layout.addWidget(time_chart_group)
        charts_layout.addWidget(status_chart_group)
        
        # Нижняя часть - таблица кампаний
        campaigns_table_group = QGroupBox("История кампаний")
        campaigns_table_layout = QVBoxLayout(campaigns_table_group)
        campaigns_table_layout.setContentsMargins(0,0,0,0)
        campaigns_table_layout.setSpacing(0)
        
        self.campaigns_table = QTableWidget()
        self.campaigns_table.setColumnCount(6)
        self.campaigns_table.setHorizontalHeaderLabels([
            "Название", "Дата", "Получателей", "Отправлено", "Успешно", "Ошибок"
        ])
        
        # Добавляем примерные данные
        sample_campaigns = [
            ("Летняя акция", "2025-09-20", "500", "500", "467", "33"),
            ("Новости продукта", "2025-09-18", "1200", "1200", "1156", "44"),
            ("Напоминание о вебинаре", "2025-09-15", "300", "298", "289", "9"),
            ("Специальное предложение", "2025-09-12", "800", "800", "724", "76"),
            ("Ежемесячная рассылка", "2025-09-01", "2000", "1987", "1834", "153")
        ]
        
        self.campaigns_table.setRowCount(len(sample_campaigns))
        for row, campaign in enumerate(sample_campaigns):
            for col, value in enumerate(campaign):
                item = QTableWidgetItem(str(value))
                self.campaigns_table.setItem(row, col, item)
        
        self.campaigns_table.setStyleSheet("""
            QTableWidget {background-color:#2D3748;border:1px solid #4A5568;border-radius:8px;color:white;gridline-color:#4A5568;}
            QTableWidget::item {padding:8px;border-bottom:1px solid #4A5568;}
            QTableWidget::item:selected {background-color:#6366F1;}
            QHeaderView::section {background-color:#374151;color:white;padding:10px;border:none;font-weight:bold;}
            QTableCornerButton::section {background-color:#2D3748;border:1px solid #4A5568;}
        """)
        self.campaigns_table.verticalHeader().setVisible(False)
        # Убираем внешние рамки групп статистики
        common_group_style = (
            "QGroupBox { border: none; margin-top:0px; padding:0px;} "
            "QGroupBox::title {left:4px; top:-2px; padding:0 6px; color:#A0AEC0; background: transparent; font-weight:600;}"
        )
        campaigns_table_group.setStyleSheet(common_group_style)
        time_chart_group.setStyleSheet(common_group_style)
        status_chart_group.setStyleSheet(common_group_style)
        
        # Настройка размеров столбцов для растягивания на весь блок
        header = self.campaigns_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Название растягивается
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Дата по содержимому
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Получателей по содержимому
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Отправлено по содержимому
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Успешно по содержимому
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Ошибок по содержимому
        # Устанавливаем минимальные размеры
        self.campaigns_table.setColumnWidth(0, 200)  # Название - основная колонка
        self.campaigns_table.setColumnWidth(1, 120)  # Дата
        self.campaigns_table.setColumnWidth(2, 100)  # Получателей
        self.campaigns_table.setColumnWidth(3, 100)  # Отправлено
        self.campaigns_table.setColumnWidth(4, 100)  # Успешно
        self.campaigns_table.setColumnWidth(5, 80)   # Ошибок
        # Настройка для полного растягивания таблицы
        self.campaigns_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.campaigns_table.horizontalHeader().setMinimumSectionSize(80)
        
        # Устанавливаем делегат для последнего столбца (Ошибок)
        self.campaigns_table.setItemDelegateForColumn(5, ErrorDotDelegate(self.campaigns_table))
        campaigns_table_layout.addWidget(self.campaigns_table, 1)
        campaigns_table_layout.setStretchFactor(self.campaigns_table, 1)
        
        # Кнопки экспорта
        export_layout = QHBoxLayout()
        export_csv_btn = ModernButton("📄 Экспорт CSV", variant="secondary", theme_manager=self.theme_manager)
        export_pdf_btn = ModernButton("📑 Экспорт PDF", variant="secondary", theme_manager=self.theme_manager)
        export_layout.addWidget(export_csv_btn)
        export_layout.addWidget(export_pdf_btn)
        export_layout.addStretch()
        campaigns_table_layout.addLayout(export_layout)
        
        # Добавляем все в splitter
        content_splitter.addWidget(charts_widget)
        content_splitter.addWidget(campaigns_table_group)
        content_splitter.setSizes([320, 480])  # больше места нижнему блоку
        
        layout.addWidget(content_splitter)
        
        # Подключаем события
        refresh_btn.clicked.connect(self._refresh_statistics)
        self.stats_period_combo.currentTextChanged.connect(self._update_statistics_period)
        export_csv_btn.clicked.connect(self._export_statistics_csv)
        export_pdf_btn.clicked.connect(self._export_statistics_pdf)
        
        return page
    
    def _refresh_statistics(self):
        """Обновление статистики"""

        QMessageBox.information(self, "Обновление", "Статистика обновлена!")
    
    def _update_statistics_period(self, period):
        """Обновление статистики при изменении периода"""
        # Здесь будет логика обновления данных в зависимости от выбранного периода
        pass
    
    def _export_statistics_csv(self):
        """Экспорт статистики в CSV"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить статистику", "statistics.csv", "CSV Files (*.csv)"
        )
        if file_path:
            QMessageBox.information(self, "Экспорт", f"Статистика сохранена в {file_path}")
    
    def _export_statistics_pdf(self):
        """Экспорт статистики в PDF"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить отчет", "statistics_report.pdf", "PDF Files (*.pdf)"
        )
        if file_path:
            QMessageBox.information(self, "Экспорт", f"Отчет сохранен в {file_path}")
    
    def _create_recipients_page(self):
        """Создание страницы управления получателями"""
        page = QWidget()
        layout = QVBoxLayout(page)
        apply_margins(layout, 'page')
        apply_spacing(layout, 'lg')
        
        # Заголовок
        title = QLabel("👥 Управление получателями")
        apply_heading_style(title, 'h1')
        title.setStyleSheet("color: #6366F1; padding-bottom: 8px; margin-bottom: 16px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Панель управления
        controls_layout = QHBoxLayout()
        
        import_btn = ModernButton("📥 Импорт CSV", variant="primary", theme_manager=self.theme_manager)
        export_btn = ModernButton("📤 Экспорт CSV", variant="secondary", theme_manager=self.theme_manager)
        add_recipient_btn = ModernButton("➕ Добавить", variant="primary", theme_manager=self.theme_manager)
        delete_recipient_btn = ModernButton("🗑 Удалить", variant="secondary", theme_manager=self.theme_manager)
        
        controls_layout.addWidget(import_btn)
        controls_layout.addWidget(export_btn)
        controls_layout.addWidget(add_recipient_btn)
        controls_layout.addWidget(delete_recipient_btn)
        controls_layout.addStretch()
        
        # Поиск
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск:"))
        self.recipients_search = QLineEdit()
        self.recipients_search.setPlaceholderText("Введите email или имя...")
        self.recipients_search.setStyleSheet("""
            QLineEdit {
                background-color: #2D3748;
                border: 1px solid #4A5568;
                border-radius: 6px;
                color: white;
                padding: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #6366F1;
            }
        """)
        search_layout.addWidget(self.recipients_search)
        
        controls_layout.addLayout(search_layout)
        layout.addLayout(controls_layout)
        
        # Таблица получателей
        self.recipients_table = QTableWidget()
        self.recipients_table.setColumnCount(5)
        self.recipients_table.setHorizontalHeaderLabels([
            "Email", "Имя", "Группа", "Статус", "Дата добавления"
        ])
        
        # Примерные данные
        sample_recipients = [
            ("john.doe@example.com", "John Doe", "VIP клиенты", "Активен", "2025-09-01"),
            ("jane.smith@example.com", "Jane Smith", "Новостная рассылка", "Активен", "2025-09-05"),
            ("bob.wilson@example.com", "Bob Wilson", "Акции", "Отписался", "2025-08-20"),
            ("alice.brown@example.com", "Alice Brown", "VIP клиенты", "Активен", "2025-09-10"),
            ("charlie.davis@example.com", "Charlie Davis", "Новостная рассылка", "Заблокирован", "2025-08-15")
        ]
        
        self.recipients_table.setRowCount(len(sample_recipients))
        for row, recipient in enumerate(sample_recipients):
            for col, value in enumerate(recipient):
                item = QTableWidgetItem(str(value))
                # Подкрашиваем статусы
                if col == 3:  # Колонка статуса
                    if value == "Отписался":
                        item.setBackground(QColor('#FEE2E2'))  # Красный
                    elif value == "Заблокирован":
                        item.setBackground(QColor('#FEF3C7'))  # Желтый  
                    elif value == "Активен":
                        item.setBackground(QColor('#D1FAE5'))  # Зеленый
                self.recipients_table.setItem(row, col, item)
        
        self.recipients_table.setStyleSheet("""
            QTableWidget {
                background-color: #2D3748;
                border: 1px solid #4A5568;
                border-radius: 8px;
                color: white;
                gridline-color: #4A5568;
                alternate-background-color: #374151;
                selection-background-color: #6366F1;
            }
            QTableWidget::item {
                padding: 12px;
                border-bottom: 1px solid #4A5568;
                border-right: 1px solid #4A5568;
            }
            QTableWidget::item:selected {
                background-color: #6366F1;
                color: white;
            }
            QTableWidget::item:hover {
                background-color: #4A5568;
            }
            QHeaderView::section {
                background-color: #374151;
                color: white;
                padding: 12px;
                border: none;
                border-right: 1px solid #4A5568;
                font-weight: bold;
                text-align: left;
            }
            QHeaderView::section:hover {
                background-color: #4A5568;
            }
            QTableWidget QHeaderView::section:vertical {
                background-color: #2D3748; /* фон секций нумерации строк */
                border: none;
                border-right: 1px solid #4A5568;
                padding: 2px 6px; /* чуть больше ширина, чтобы не выглядело ужато */
                color: #A0AEC0;
            }
            /* Фон области под последним номером (пустое пространство вертикального header) */
            QTableWidget QHeaderView:vertical {
                background-color: #2D3748;
                border: none;
            }
            QTableWidget::item:first-column {
                background-color: #2D3748;
            }
            QScrollBar:vertical {
                background-color: #374151;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #6366F1;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #7C3AED;
            }
            QTableCornerButton::section {
                background-color: #2D3748;
                border: 1px solid #4A5568;
                border-top-left-radius: 8px;
            }
        """)
        # Палитра base чтобы убрать тёмные пустые области (правильная индентация)
        pal = self.recipients_table.palette()
        pal.setColor(QPalette.Base, QColor('#2D3748'))
        pal.setColor(QPalette.AlternateBase, QColor('#374151'))
        self.recipients_table.setPalette(pal)
        
        # Настройка размеров колонок для максимального растягивания на весь блок
        header = self.recipients_table.horizontalHeader()
        
        # Убираем setStretchLastSection и используем только setSectionResizeMode для лучшего контроля
        header.setStretchLastSection(False)
        
        # Настраиваем растягивание колонок для максимального использования пространства
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Email - основная растягивающаяся колонка
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Имя по содержимому
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Группа - дополнительная растягивающаяся
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Статус по содержимому
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Дата по содержимому
        
        # Устанавливаем минимальные размеры для оптимального отображения
        self.recipients_table.setColumnWidth(0, 280)  # Email - увеличена ширина
        self.recipients_table.setColumnWidth(1, 140)  # Имя - немного уменьшена
        self.recipients_table.setColumnWidth(2, 200)  # Группа - увеличена (будет растягиваться)
        self.recipients_table.setColumnWidth(3, 110)  # Статус - оптимизирована
        self.recipients_table.setColumnWidth(4, 120)  # Дата - оптимизирована
        
        layout.addWidget(self.recipients_table)
        
        # Статистика внизу
        stats_layout = QHBoxLayout()
        total_label = QLabel("Всего получателей: 1,234 | Активных: 1,156 | Отписались: 45 | Заблокированы: 33")
        total_label.setStyleSheet("color: #A0AEC0; font-size: 14px; padding: 8px;")
        stats_layout.addWidget(total_label)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        # Подключаем события
        import_btn.clicked.connect(self._import_recipients)
        export_btn.clicked.connect(self._export_recipients)
        add_recipient_btn.clicked.connect(self._add_recipient)
        delete_recipient_btn.clicked.connect(self._delete_recipient)
        self.recipients_search.textChanged.connect(self._search_recipients)
        
        # Дополнительные настройки для максимального растягивания таблицы
        self.recipients_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.recipients_table.horizontalHeader().setMinimumSectionSize(80)  # Уменьшен минимум
        self.recipients_table.horizontalHeader().setDefaultSectionSize(150)  # Размер по умолчанию
        
        # Включаем адаптивное растягивание при изменении размера окна
        self.recipients_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.recipients_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Убеждаемся, что таблица использует всё доступное пространство
        self.recipients_table.setMinimumHeight(300)  # Минимальная высота
        self.recipients_table.setAlternatingRowColors(True)  # Чередующиеся цвета строк для лучшей читаемости
        
        return page
    
    def _import_recipients(self):
        """Импорт получателей из CSV"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите CSV файл", "", "CSV Files (*.csv)"
        )
        if file_path:
            QMessageBox.information(self, "Импорт", f"Импорт из {file_path} завершен!")
    
    def _export_recipients(self):
        """Экспорт получателей в CSV"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить список получателей", "recipients.csv", "CSV Files (*.csv)"
        )
        if file_path:
            QMessageBox.information(self, "Экспорт", f"Список сохранен в {file_path}")
    
    def _add_recipient(self):
        """Добавление нового получателя"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить получателя")
        dialog.setMinimumWidth(400)
        
        layout = QFormLayout(dialog)
        
        email_edit = QLineEdit()
        name_edit = QLineEdit()
        group_combo = QComboBox()
        group_combo.addItems(["VIP клиенты", "Новостная рассылка", "Акции", "Партнеры"])
        
        layout.addRow("Email:", email_edit)
        layout.addRow("Имя:", name_edit)
        layout.addRow("Группа:", group_combo)
        
        buttons_layout = QHBoxLayout()
        save_btn = ModernButton("Сохранить", variant="primary", theme_manager=self.theme_manager)
        cancel_btn = ModernButton("Отмена", variant="secondary", theme_manager=self.theme_manager)
        
        save_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addRow(buttons_layout)
        
        if dialog.exec_() == QDialog.Accepted:
            # Здесь будет логика добавления в базу/файл
            QMessageBox.information(self, "Успех", "Получатель добавлен!")
    
    def _delete_recipient(self):
        """Удаление выбранного получателя"""
        current_row = self.recipients_table.currentRow()
        if current_row >= 0:
            email = self.recipients_table.item(current_row, 0).text()
            reply = QMessageBox.question(self, "Подтверждение", 
                                       f"Удалить получателя {email}?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.recipients_table.removeRow(current_row)
                QMessageBox.information(self, "Успех", "Получатель удален!")
    
    def _search_recipients(self, text):
        """Поиск получателей"""
        for row in range(self.recipients_table.rowCount()):
            match = False
            for col in range(self.recipients_table.columnCount()):
                item = self.recipients_table.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.recipients_table.setRowHidden(row, not match)
    
    def _create_advanced_settings_page(self):
        """Создание страницы дополнительных настроек"""
        page = QWidget()
        layout = QVBoxLayout(page)
        apply_margins(layout, 'page')
        apply_spacing(layout, 'lg')
        
        # Заголовок
        title = QLabel("🔧 Дополнительные настройки")
        apply_heading_style(title, 'h1')
        title.setStyleSheet("color: #6366F1; padding-bottom: 8px; margin-bottom: 16px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Scroll area для настроек
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setSpacing(20)
        
        # Группа: Внешний вид
        appearance_group = QGroupBox("🎨 Внешний вид")
        appearance_layout = QGridLayout(appearance_group)
        
        # Размер шрифта
        appearance_layout.addWidget(QLabel("Размер шрифта:"), 0, 0)
        font_size_spin = QSpinBox()
        font_size_spin.setRange(10, 20)
        font_size_spin.setValue(14)
        font_size_spin.setSuffix(" px")
        appearance_layout.addWidget(font_size_spin, 0, 1)
        
        settings_layout.addWidget(appearance_group)
        
        # Группа: Уведомления
        notifications_group = QGroupBox("🔔 Уведомления")
        notifications_layout = QGridLayout(notifications_group)
        
        # Системные уведомления
        notifications_layout.addWidget(QLabel("Системные уведомления:"), 0, 0)
        system_notifications_check = SquareCheckBox("Включить")
        system_notifications_check.setChecked(True)
        notifications_layout.addWidget(system_notifications_check, 0, 1)
        
        # Email уведомления
        notifications_layout.addWidget(QLabel("Email уведомления:"), 1, 0)
        email_notifications_check = SquareCheckBox("Включить")
        email_notifications_check.setChecked(False)
        notifications_layout.addWidget(email_notifications_check, 1, 1)
        
        # Email для уведомлений
        notifications_layout.addWidget(QLabel("Email для уведомлений:"), 2, 0)
        notification_email_edit = QLineEdit()
        notification_email_edit.setPlaceholderText("admin@example.com")
        notifications_layout.addWidget(notification_email_edit, 2, 1)
        
        settings_layout.addWidget(notifications_group)
        
        # Группа: Расписание
        schedule_group = QGroupBox("⏰ Автоматические рассылки")
        schedule_layout = QGridLayout(schedule_group)
        
        # Включить расписание
        schedule_layout.addWidget(QLabel("Автоматические рассылки:"), 0, 0)
        auto_send_check = SquareCheckBox("Включить")
        schedule_layout.addWidget(auto_send_check, 0, 1)
        
        # Интервал проверки
        schedule_layout.addWidget(QLabel("Интервал проверки:"), 1, 0)
        check_interval_spin = QSpinBox()
        check_interval_spin.setRange(1, 60)
        check_interval_spin.setValue(5)
        check_interval_spin.setSuffix(" мин")
        schedule_layout.addWidget(check_interval_spin, 1, 1)
        
        # Максимум рассылок в час
        schedule_layout.addWidget(QLabel("Максимум рассылок в час:"), 2, 0)
        max_per_hour_spin = QSpinBox()
        max_per_hour_spin.setRange(1, 1000)
        max_per_hour_spin.setValue(100)
        schedule_layout.addWidget(max_per_hour_spin, 2, 1)
        
        settings_layout.addWidget(schedule_group)
        
        # Группа: Безопасность
        security_group = QGroupBox("🔒 Безопасность")
        security_layout = QGridLayout(security_group)
        
        # Логирование
        security_layout.addWidget(QLabel("Подробное логирование:"), 0, 0)
        detailed_logging_check = SquareCheckBox("Включить")
        detailed_logging_check.setChecked(True)
        security_layout.addWidget(detailed_logging_check, 0, 1)
        
        # Хранить логи (дни)
        security_layout.addWidget(QLabel("Хранить логи:"), 1, 0)
        log_retention_spin = QSpinBox()
        log_retention_spin.setRange(1, 365)
        log_retention_spin.setValue(30)
        log_retention_spin.setSuffix(" дней")
        security_layout.addWidget(log_retention_spin, 1, 1)
        
        # API ключ защита
        security_layout.addWidget(QLabel("Проверять API ключи:"), 2, 0)
        api_check = SquareCheckBox("Включить")
        api_check.setChecked(True)
        security_layout.addWidget(api_check, 2, 1)
        
        settings_layout.addWidget(security_group)
        
        # Группа: Производительность
        performance_group = QGroupBox("⚡ Производительность")
        performance_layout = QGridLayout(performance_group)

        # Кэширование
        performance_layout.addWidget(QLabel("Кэширование шаблонов:"), 0, 0)
        template_cache_check = SquareCheckBox("Включить")
        template_cache_check.setChecked(True)
        performance_layout.addWidget(template_cache_check, 0, 1)

        # Размер кэша
        performance_layout.addWidget(QLabel("Размер кэша:"), 1, 0)
        cache_size_spin = QSpinBox()
        cache_size_spin.setRange(10, 1000)
        cache_size_spin.setValue(100)
        cache_size_spin.setSuffix(" МБ")
        performance_layout.addWidget(cache_size_spin, 1, 1)

        # Timeout соединений
        performance_layout.addWidget(QLabel("Timeout соединений:"), 2, 0)
        timeout_spin = QSpinBox()
        timeout_spin.setRange(5, 300)
        timeout_spin.setValue(30)
        timeout_spin.setSuffix(" сек")
        performance_layout.addWidget(timeout_spin, 2, 1)

        settings_layout.addWidget(performance_group)
        
        # Применяем стили к группам
        group_style = """
            QGroupBox {
                font-weight: bold;
                border: 2px solid #4A5568;
                border-radius: 8px;
                margin-top: 10px;
                padding: 16px;
                background-color: #2D3748;
                color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background-color: #374151;
                border-radius: 4px;
            }
            QLabel {
                color: white;
                font-weight: normal;
            }
            QComboBox, QSpinBox, QLineEdit {
                background-color: #374151;
                border: 1px solid #4A5568;
                border-radius: 4px;
                color: white;
                padding: 6px;
            }
            QComboBox:focus, QSpinBox:focus, QLineEdit:focus {
                border-color: #6366F1;
            }
            QCheckBox {
                color: white;
            }
            /* Кастомные чекбоксы рисуются вручную (SquareCheckBox), поэтому indicator не стилизуем */
        """
        
        for group in [appearance_group, notifications_group, schedule_group, security_group, performance_group]:
            group.setStyleSheet(group_style)

        # (Удалён хак с заменой текста чекбокса на символы галочки/квадрата)
        
        settings_layout.addStretch()
        scroll.setWidget(settings_widget)
        layout.addWidget(scroll)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        save_settings_btn = ModernButton("💾 Сохранить настройки", variant="primary", theme_manager=self.theme_manager)
        reset_settings_btn = ModernButton("🔄 Сбросить", variant="secondary", theme_manager=self.theme_manager)
        export_settings_btn = ModernButton("📤 Экспорт", variant="secondary", theme_manager=self.theme_manager)
        
        buttons_layout.addWidget(save_settings_btn)
        buttons_layout.addWidget(reset_settings_btn)
        buttons_layout.addWidget(export_settings_btn)
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        # Подключаем события
        save_settings_btn.clicked.connect(self._save_advanced_settings)
        reset_settings_btn.clicked.connect(self._reset_advanced_settings)
        export_settings_btn.clicked.connect(self._export_advanced_settings)
        
        return page
    
    def _save_advanced_settings(self):
        """Сохранение дополнительных настроек"""
        QMessageBox.information(self, "Сохранение", "Настройки сохранены!\nНекоторые изменения могут потребовать перезапуска приложения.")
    
    def _reset_advanced_settings(self):
        """Сброс настроек к значениям по умолчанию"""
        reply = QMessageBox.question(self, "Подтверждение", 
                                   "Сбросить все настройки к значениям по умолчанию?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            QMessageBox.information(self, "Сброс", "Настройки сброшены к значениям по умолчанию!")
    
    def _export_advanced_settings(self):
        """Экспорт настроек в файл"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить настройки", "mailing_settings.json", "JSON Files (*.json)"
        )
        if file_path:
            QMessageBox.information(self, "Экспорт", f"Настройки экспортированы в {file_path}")
    
    def _create_logs_page(self):
        """Создание страницы логов"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)
        
        title = QLabel("📄 Системные логи")
        title.setStyleSheet("""
            font-size: 28px; 
            font-weight: bold; 
            color: #6366F1; 
            padding-bottom: 8px;
            margin-bottom: 16px;
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Управление логами
        controls_layout = QHBoxLayout()
        
        controls_layout.addWidget(QLabel("Уровень:"))
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.log_level_combo.setCurrentText("INFO")
        self.log_level_combo.currentTextChanged.connect(self._on_log_level_changed)
        controls_layout.addWidget(self.log_level_combo)
        
        clear_logs_btn = ModernButton("Очистить", variant="tertiary", theme_manager=self.theme_manager)
        clear_logs_btn.clicked.connect(lambda: self.logs_view.clear())
        controls_layout.addWidget(clear_logs_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Область логов
        self.logs_view = QTextEdit()
        self.logs_view.setReadOnly(True)
        self.logs_view.setObjectName('LogsView')
        layout.addWidget(self.logs_view, 1)
        
        return page
    
    def _choose_file_ft(self, field: FloatingTextField, filter_: str = "All (*.*)"):
        """Выбор файла для FloatingTextField"""
        path, _ = QFileDialog.getOpenFileName(self, "Выберите файл", '', filter_)
        if path:
            field.setText(path)
    
    def _start_campaign(self):
        """Запуск рассылки"""
        if self._mailer.is_running():
            return
        
        file_path = self.recipients_path.text().strip()
        if not file_path:
            self.progress_label.setText("Не выбран файл получателей")
            return
        
        recipients = self._load_recipients(file_path)
        if not recipients:
            self.progress_label.setText("Список получателей пуст")
            return
        
        template = self.template_path.text().strip()
        subject = self.subject_edit.text().strip() or "Без темы"
        concurrency = self.concurrent_spin.value()
        dry = self.dry_run_switch.isChecked()
        
        self._mailer.start(
            recipients=recipients,
            template_name=template,
            subject=subject,
            dry_run=dry,
            concurrency=concurrency
        )
        
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_label.setText("Отправка...")
        self.progress_ring.setVisible(True)
        self.progress_ring.setIndeterminate(True)
    
    def _cancel_campaign(self):
        """Отмена рассылки"""
        if self._mailer.is_running():
            self._mailer.cancel()
            self.progress_label.setText("Отмена...")
    
    def _load_recipients(self, path: str):
        """Загрузка получателей из файла"""
        loaders = {
            '.csv': CSVLoader(),
            '.xlsx': ExcelLoader(),
            '.json': JSONLoader()
        }
        
        ext = Path(path).suffix.lower()
        loader = loaders.get(ext)
        if not loader:
            return []
        
        try:
            data = loader.load(path)
            valid, errors = validate_email_list(r.email for r in data)
            if errors:
                logging.getLogger('mailing.gui').warning(f'Отфильтровано некорректных адресов: {len(errors)}')
            
            email_map = {r.email: r for r in data}
            return [email_map[email] for email in valid if email in email_map]
        except Exception as e:
            logging.error(f"Ошибка загрузки получателей: {e}")
            return []
    
    def _update_dashboard(self):
        """Обновление статистики Dashboard"""
        try:
            # Статистика БД
            delivery_repo = DeliveryRepository()
            stats = delivery_repo.stats()
            
            total = stats['total']
            success = stats['success']
            failed = stats['failed']
            
            self.dashboard_sent_card.setValue(str(total))
            
            if total > 0:
                success_rate = (success / total) * 100
                self.dashboard_success_card.setValue(f"{success_rate:.1f}%")
                self.dashboard_success_card.setProgress(success_rate / 100)
            else:
                self.dashboard_success_card.setValue("0%")
                self.dashboard_success_card.setProgress(0)
            
            self.dashboard_failed_card.setValue(str(failed))
            
            # Квоты
            quota = DailyQuota()
            quota.load()
            used = quota.used()
            limit = quota.limit
            
            self.dashboard_quota_card.setValue(f"{used}/{limit}")
            self.dashboard_quota_card.setProgress(used / limit)
            
            # Обновление активности
            event_repo = EventRepository()
            recent_events = event_repo.get_recent_events(3)
            
            if recent_events:
                activity_text = "Последние события:\n\n"
                for event in recent_events:
                    event_type = event.get('event_type', 'unknown') or 'unknown'
                    recipient = event.get('recipient', 'unknown') or 'unknown'
                    activity_text += f"• {event_type} - {str(recipient)}\n"
            else:
                activity_text = "Нет последних событий"
            
            self.activity_list.setPlainText(activity_text)
            
        except Exception as e:
            logging.error(f"Ошибка обновления dashboard: {e}")
    
    def _on_section_changed(self, index: int):
        """Смена раздела"""
        self.stack.setCurrentIndex(index)
    
    def _retranslate(self):
        """Обновление переводов"""
        self.setWindowTitle("Система массовой рассылки - Полное управление")
    
    def _init_log_handler(self):
        """Инициализация обработчика логов"""
        if hasattr(self, '_qt_log_handler'):
            return
            
        handler = QtLogHandler()
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s')
        handler.setFormatter(formatter)
        
        self._qt_log_handler = install_qt_log_handler(handler)
        self._qt_log_handler.emitter.messageEmitted.connect(self._on_log_message)
        
        # Загружаем буферизованные сообщения
        for level, msg in self._qt_log_handler.buffer:
            self._append_log_line(level, msg)
    
    def _on_log_message(self, level: str, text: str):
        """Обработчик нового лог-сообщения"""
        if not hasattr(self, 'log_level_combo'):
            return
            
        order = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        current = self.log_level_combo.currentText()
        
        if order.index(level) < order.index(current):
            return
        
        self._append_log_line(level, text)
    
    def _append_log_line(self, level: str, text: str):
        """Добавление строки в лог"""
        if not hasattr(self, 'logs_view'):
            return
            
        colors = {
            'DEBUG': '#888888',
            'INFO': '#ffffff' if self.theme_manager.is_dark() else '#000000',
            'WARNING': '#e3b341',
            'ERROR': '#d9544d',
            'CRITICAL': '#ff0000'
        }
        
        color = colors.get(level, '#cccccc')
        self.logs_view.append(f"<span style='color:{color}'><b>{level}</b> {text}</span>")
        self.logs_view.verticalScrollBar().setValue(self.logs_view.verticalScrollBar().maximum())
    
    def _on_log_level_changed(self, level: str):
        """Смена уровня логирования"""
        if not hasattr(self, '_qt_log_handler'):
            return
            
        self.logs_view.clear()
        order = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        
        for lvl, msg in self._qt_log_handler.buffer:
            if order.index(lvl) < order.index(level):
                continue
            self._append_log_line(lvl, msg)
    
    # Обработчики событий MailerService
    def _on_mailer_started(self):
        """Обработчик запуска рассылки"""
        logging.getLogger('mailing.gui').info('Рассылка запущена')
    
    def _on_mailer_progress(self, event: dict):
        """Обработчик прогресса рассылки"""
        stats = event.get('stats', {})
        success = stats.get('success', 0)
        failed = stats.get('failed', 0)
        total = stats.get('total', 0)
        
        if total:
            progress = int(((success + failed) / total) * 100)
            self.progress_bar.setValue(progress)
            
            self.progress_ring.setIndeterminate(False)
            self.progress_ring.setMaximum(total)
            self.progress_ring.setValue(success + failed)
        
        self.progress_label.setText(f"Прогресс: {success + failed}/{total} | ✅ {success} ❌ {failed}")
    
    def _on_mailer_finished(self, stats: dict):
        """Обработчик завершения рассылки"""
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_label.setText("Завершено")
        self.progress_ring.setVisible(False)
        
        logging.getLogger('mailing.gui').info(f'Рассылка завершена: {stats}')
    
    def _on_mailer_error(self, msg: str, stats: dict):
        """Обработчик ошибки рассылки"""
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_label.setText(f"Ошибка: {msg}")
        self.progress_ring.setVisible(False)
        
        logging.getLogger('mailing.gui').error(f'Ошибка рассылки: {msg}')
    
    def _on_mailer_cancelled(self, stats: dict):
        """Обработчик отмены рассылки"""
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_label.setText("Отменено")
        self.progress_ring.setVisible(False)
        
        logging.getLogger('mailing.gui').info('Рассылка отменена')
    
    def _on_palette_changed(self, palette):
        """Обработчик смены палитры"""
        # Применяем глобальную палитру
        app = QApplication.instance()
        if app:
            from . import styles
            styles.apply_palette(app, self.theme_manager.is_dark())