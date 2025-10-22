from __future__ import annotations
import sys
import asyncio
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QTextEdit, QFileDialog, QMessageBox, QProgressBar
from PySide6.QtCore import Qt, QThread, pyqtSignal
from PySide6.QtGui import QFont, QPalette, QColor
from qasync import QEventLoop

from .theme import ThemeManager
from . import styles

class MainWindow(QMainWindow):
    """Главное окно приложения Email Marketing Tool."""
    
    def __init__(self, theme_manager):
        super().__init__()
        self.theme_manager = theme_manager
        self.setup_ui()
        
    def setup_ui(self):
        """Настройка пользовательского интерфейса."""
        self.setWindowTitle("📧 Professional Email Marketing Tool")
        self.setMinimumSize(1000, 700)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Заголовок
        self.create_header(main_layout)
        
        # Основной контент
        self.create_content(main_layout)
        
        # Статус бар
        self.create_status_bar(main_layout)
        
    def create_header(self, layout):
        """Создает заголовок приложения."""
        header_layout = QHBoxLayout()
        
        title = QLabel("📧 Professional Email Marketing Tool")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: #2c3e50;
                padding: 20px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2980b9);
                color: white;
                border-radius: 15px;
                margin-bottom: 10px;
            }
        """)
        
        header_layout.addWidget(title)
        layout.addLayout(header_layout)
        
    def create_content(self, layout):
        """Создает основной контент."""
        content_layout = QHBoxLayout()
        
        # Левая панель - управление
        left_panel = self.create_control_panel()
        content_layout.addWidget(left_panel, 1)
        
        # Правая панель - просмотр и статистика
        right_panel = self.create_preview_panel()
        content_layout.addWidget(right_panel, 2)
        
        layout.addLayout(content_layout)
        
    def create_control_panel(self):
        """Создает панель управления."""
        panel = QWidget()
        panel.setStyleSheet("""
            QWidget {
                background-color: #ecf0f1;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        
        # Заголовок панели
        panel_title = QLabel("🎯 Управление кампанией")
        panel_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #34495e; margin-bottom: 15px;")
        layout.addWidget(panel_title)
        
        # Кнопки управления
        self.load_recipients_btn = QPushButton("📋 Загрузить получателей")
        self.load_recipients_btn.clicked.connect(self.load_recipients)
        self.style_button(self.load_recipients_btn, "#3498db")
        layout.addWidget(self.load_recipients_btn)
        
        self.load_template_btn = QPushButton("🎨 Выбрать шаблон")
        self.load_template_btn.clicked.connect(self.load_template)
        self.style_button(self.load_template_btn, "#9b59b6")
        layout.addWidget(self.load_template_btn)
        
        self.preview_btn = QPushButton("👀 Предварительный просмотр")
        self.preview_btn.clicked.connect(self.preview_email)
        self.style_button(self.preview_btn, "#f39c12")
        layout.addWidget(self.preview_btn)
        
        self.send_btn = QPushButton("🚀 Запустить рассылку")
        self.send_btn.clicked.connect(self.start_campaign)
        self.style_button(self.send_btn, "#27ae60")
        layout.addWidget(self.send_btn)
        
        # Прогресс бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #27ae60;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()
        return panel
        
    def create_preview_panel(self):
        """Создает панель предварительного просмотра."""
        panel = QWidget()
        panel.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border: 1px solid #bdc3c7;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        
        # Заголовок панели
        panel_title = QLabel("📧 Предварительный просмотр")
        panel_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #34495e; margin-bottom: 15px;")
        layout.addWidget(panel_title)
        
        # Текстовое поле для предварительного просмотра
        self.preview_text = QTextEdit()
        self.preview_text.setPlaceholderText("Здесь будет отображаться предварительный просмотр вашего email...")
        self.preview_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Arial', sans-serif;
                font-size: 12px;
                background-color: #fafafa;
            }
        """)
        layout.addWidget(self.preview_text)
        
        # Статистика
        stats_title = QLabel("📊 Статистика")
        stats_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #34495e; margin-top: 15px;")
        layout.addWidget(stats_title)
        
        self.stats_text = QLabel("Получатели: 0\nШаблон: не выбран\nСтатус: готов к настройке")
        self.stats_text.setStyleSheet("""
            QLabel {
                background-color: #ecf0f1;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                color: #2c3e50;
            }
        """)
        layout.addWidget(self.stats_text)
        
        return panel
        
    def create_status_bar(self, layout):
        """Создает статус бар."""
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("✅ Готов к работе")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #2ecc71;
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
        """)
        
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        version_label = QLabel("v2.0.0 Enhanced Edition")
        version_label.setStyleSheet("color: #7f8c8d; font-size: 10px;")
        status_layout.addWidget(version_label)
        
        layout.addLayout(status_layout)
        
    def style_button(self, button, color):
        """Применяет стиль к кнопке."""
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 8px;
                margin: 5px 0;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color)};
                transform: translateY(-1px);
            }}
            QPushButton:pressed {{
                background-color: {self.darken_color(color, 0.8)};
            }}
        """)
        
    def darken_color(self, color, factor=0.9):
        """Затемняет цвет."""
        if color == "#3498db":
            return "#2980b9" if factor == 0.9 else "#1f5f8b"
        elif color == "#9b59b6":
            return "#8e44ad" if factor == 0.9 else "#6c3483"
        elif color == "#f39c12":
            return "#e67e22" if factor == 0.9 else "#d35400"
        elif color == "#27ae60":
            return "#229954" if factor == 0.9 else "#1e8449"
        return color
        
    def load_recipients(self):
        """Загружает список получателей."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Выберите файл с получателями",
            "",
            "CSV файлы (*.csv);;Excel файлы (*.xlsx);;Все файлы (*)"
        )
        
        if file_path:
            self.status_label.setText(f"📋 Загружен файл: {Path(file_path).name}")
            self.update_stats("recipients", Path(file_path).name)
            
    def load_template(self):
        """Загружает шаблон email."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите шаблон email",
            "",
            "HTML файлы (*.html);;Текстовые файлы (*.txt);;Все файлы (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.preview_text.setHtml(content if file_path.endswith('.html') else f"<pre>{content}</pre>")
                self.status_label.setText(f"🎨 Загружен шаблон: {Path(file_path).name}")
                self.update_stats("template", Path(file_path).name)
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить шаблон: {e}")
                
    def preview_email(self):
        """Показывает предварительный просмотр."""
        if self.preview_text.toPlainText():
            QMessageBox.information(
                self, 
                "Предварительный просмотр", 
                "Email готов к отправке!\n\n📧 Проверьте содержимое в панели справа."
            )
            self.status_label.setText("👀 Предварительный просмотр готов")
        else:
            QMessageBox.warning(self, "Внимание", "Сначала загрузите шаблон email!")
            
    def start_campaign(self):
        """Запускает кампанию рассылки."""
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "🚀 Запустить рассылку?\n\nУбедитесь, что все настройки правильные.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.status_label.setText("🚀 Рассылка запущена...")
            
            # Имитация прогресса
            for i in range(101):
                self.progress_bar.setValue(i)
                QApplication.processEvents()
                
            self.status_label.setText("✅ Рассылка завершена успешно!")
            self.progress_bar.setVisible(False)
            
            QMessageBox.information(
                self,
                "Успех",
                "🎉 Рассылка завершена!\n\n📊 Проверьте статистику доставки в отчетах."
            )
            
    def update_stats(self, stat_type, value):
        """Обновляет статистику."""
        current_text = self.stats_text.text()
        lines = current_text.split('\n')
        
        if stat_type == "recipients":
            lines[0] = f"Получатели: {value}"
        elif stat_type == "template":
            lines[1] = f"Шаблон: {value}"
            
        lines[2] = "Статус: готов к отправке"
        self.stats_text.setText('\n'.join(lines))