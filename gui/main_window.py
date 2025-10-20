from PySide6.QtCore import Qt, QEasingCurve, QPropertyAnimation
from __future__ import annotations
from pathlib import Path
import asyncio

from PySide6.QtWidgets import (
import logging

            from . import styles
from . import styles
from .apple_table import AppleTableView
from .components import ModernButton
from .log_handler import QtLogHandler, install_qt_log_handler
from .mailer_service import MailerService
from .progress_ring import ProgressRing
from .recipients_view import RecipientsView
from .segmented_control import SegmentedControl
from .settings_panel import SettingsPanel
from .stats_card import StatsCard
from .stats_panel import StatsPanel
from .switch import IOSSwitch
from .template_preview import TemplatePreview
from .text_field import FloatingTextField
from .theme import ThemeManager
from .vibrancy import VibrantWidget
from data_loader.csv_loader import CSVLoader
from data_loader.excel_loader import ExcelLoader
from data_loader.json_loader import JSONLoader
from validation.email_validator import validate_email_list

    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QPushButton,
    QStackedWidget,
    QComboBox,
    QTextEdit,
    QHBoxLayout as QHBox,
    QFrame,
    QLineEdit,
    QFileDialog,
    QSpinBox,
    QCheckBox,
    QProgressBar,
    QGraphicsOpacityEffect,
    QApplication,
)


class MainWindow(QMainWindow):
    """Класс MainWindow наследующий от QMainWindow."""
    def __init__(self, theme_manager: ThemeManager):"""Внутренний метод для  init  .
        """Инициализирует объект."""

    Args:
        theme_manager: Параметр для theme manager"""
        super().__init__()
        self.theme_manager = theme_manager
        self._mailer = MailerService()
        self._mailer.started.connect(self._on_mailer_started)
        self._mailer.progress.connect(self._on_mailer_progress)
        self._mailer.finished.connect(self._on_mailer_finished)
        self._mailer.error.connect(self._on_mailer_error)
        self._mailer.cancelled.connect(self._on_mailer_cancelled)self.setWindowTitle("Система массовой рассылки")
        self.resize(1200, 800)
        self._init_ui()
        self.theme_manager.paletteChanged.connect(self._on_palette_changed)

    # ---------------- UI Construction -----------------
    def _init_ui(self):"""Внутренний метод для init ui.

    Args:"""
        root = QWidget()
        layout = QHBoxLayout(root)

        # Sidebar
        sidebar = VibrantWidget()sidebar.setObjectName("Sidebar")
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(8, 8, 8, 8)

        self.list_widget = QListWidget()
        # Русские названия секцийsection_names = ["Отправка", "Получатели", "Шаблоны", "Статистика", "Настройки"]
        for name in section_names:
            QListWidgetItem(name, self.list_widget)
        self.list_widget.currentRowChanged.connect(self._on_section_changed)
        self.list_widget.setMaximumWidth(190)
        side_layout.addWidget(self.list_widget)
        side_layout.addStretch(1)

        # Stacked content
        self.stack = QStackedWidget()
        for key in SECTION_KEYS:
            page = QWidget()
            pv = QVBoxLayout(page)
            pv.setContentsMargins(12, 12, 12, 12)
            placeholder = QLabel(
                self.lang_manager.t("placeholder_section", name = self.lang_manager.t(key)
                )
            )
            placeholder.setAlignment(Qt.AlignCenter)
            pv.addWidget(placeholder)if key == "section_dashboard":
                pv.removeWidget(placeholder)
                placeholder.deleteLater()
                dash_layout = QVBoxLayout()
                self.dashboard_period = SegmentedControl(["Day", "Week", "Month"],
                    current = 1,theme_manager = self.theme_manager,"
            ")
                dash_layout.addWidget(self.dashboard_period)
                cards_row = QHBox()
                self.card_sent = StatsCard("Sent","0",0.0, theme_manager = self.theme_manager
                )
                self.card_open = StatsCard("Open %","0%",0.0, theme_manager = self.theme_manager
                )
                self.card_fail = StatsCard("Failed","0",0.0, theme_manager = self.theme_manager
                )
                cards_row.addWidget(self.card_sent)
                cards_row.addWidget(self.card_open)
                cards_row.addWidget(self.card_fail)
                dash_layout.addLayout(cards_row)
                chart_ph = QLabel(self.lang_manager.t("placeholder_section", name="Chart")
                )
                chart_ph.setAlignment(Qt.AlignCenter)
                dash_layout.addWidget(chart_ph, 1)
                pv.addLayout(dash_layout)if key == "section_campaigns":
                pv.removeWidget(placeholder)
                placeholder.deleteLater()
                form = QVBoxLayout()
                form.setSpacing(10)
                self.recipients_path = FloatingTextField(self.lang_manager.t("recipients_file"),"""","""recipients.csv",theme_manager = self.theme_manager,"
            ")
                btn_choose_rec = ModernButton(self.lang_manager.t("select"),
                    ""variant="secondary",theme_manager = self.theme_manager,"
            ")
                btn_choose_rec.clicked.connect(
                    lambda: self._choose_file_ft(self.recipients_path, "CSV/XLSX/JSON (*.csv *.xlsx *.json)"
                    )
                )
                form.addLayout(
                    self._form_row_component(self.recipients_path, btn_choose_rec)
                )
                self.template_path = FloatingTextField(self.lang_manager.t("template_file"),"""","""template.html.j2",theme_manager = self.theme_manager,"
            ")
                btn_choose_tpl = ModernButton(self.lang_manager.t("select"),
                    ""variant="secondary",theme_manager = self.theme_manager,"
            ")
                btn_choose_tpl.clicked.connect(
                    lambda: self._choose_file_ft(self.template_path, "Templates (*.j2 *.html *.txt)"
                    )
                )
                form.addLayout(
                    self._form_row_component(self.template_path, btn_choose_tpl)
                )
                self.subject_edit = FloatingTextField(self.lang_manager.t("subject"), theme_manager = self.theme_manager
                )
                form.addWidget(self.subject_edit)
                self.concurrent_spin = QSpinBox()
                self.concurrent_spin.setRange(1, 1000)
                self.concurrent_spin.setValue(10)
                form.addLayout(
                    self._form_row(self.lang_manager.t("concurrency"), self.concurrent_spin
                    )
                )
                dry_row = QHBox()self.dry_run_label = QLabel(self.lang_manager.t("dry_run"))
                self.dry_run_switch = IOSSwitch(False, theme_manager = self.theme_manager)
                dry_row.addWidget(self.dry_run_label)
                dry_row.addStretch(1)
                dry_row.addWidget(self.dry_run_switch)
                form.addLayout(dry_row)
                btn_row = QHBox()
                self.start_btn = ModernButton(self.lang_manager.t("start"),
                    ""variant="primary",theme_manager = self.theme_manager,"
            ")
                self.start_btn.clicked.connect(self._start_campaign)
                self.cancel_btn = ModernButton(self.lang_manager.t("cancel"),
                    ""variant="tertiary",theme_manager = self.theme_manager,"
            ")
                self.cancel_btn.setEnabled(False)
                self.cancel_btn.clicked.connect(self._cancel_campaign)
                btn_row.addWidget(self.start_btn)
                btn_row.addWidget(self.cancel_btn)
                form.addLayout(btn_row)
                prog_row = QHBox()
                self.progress_ring = ProgressRing(
                    size = 36, thickness = 4, theme_manager = self.theme_manager
                )
                self.progress_ring.setVisible(False)
                self.progress_bar = QProgressBar()
                self.progress_bar.setRange(0, 100)
                self.progress_bar.setValue(0)self.progress_label = QLabel(self.lang_manager.t("idle"))
                prog_row.addWidget(self.progress_ring)
                prog_row.addWidget(self.progress_bar, 1)
                prog_row.addWidget(self.progress_label)
                form.addLayout(prog_row)
                # Daily quota indicator (used / limit). Color thresholds: <80% normal, 80-94% warning, >=95% danger
                quota_row = QHBox()
                quota_row.setContentsMargins(0, 0, 0, 0)
                self.quota_bar = QProgressBar()
                self.quota_bar.setRange(0, 100)
                self.quota_bar.setValue(0)self.quota_bar.setFormat("0 / 100 (0%)")
                self.quota_bar.setTextVisible(True)
                self.quota_label = QLabel(self.lang_manager.t("daily_quota")if hasattr(self.lang_manager, "t")else "Daily quota"
                )
                quota_row.addWidget(self.quota_label)
                quota_row.addWidget(self.quota_bar, 1)
                form.addLayout(quota_row)
                self.stats_panel = StatsPanel(self.lang_manager)
                form.addWidget(self.stats_panel)
                pv.addLayout(form)if key == "section_logs":
                pv.removeWidget(placeholder)
                placeholder.deleteLater()
                logs_layout = QVBoxLayout()
                top_bar = QHBox()lvl_label = QLabel(self.lang_manager.t("log_level"))
                self.log_level_combo = QComboBox()
                self.log_level_combo.addItems(["DEBUG","INFO","WARNING","ERROR", "CRITICAL"]
                )self.log_level_combo.setCurrentText("INFO")
                self.log_level_combo.currentTextChanged.connect(
                    self._on_log_level_changed
                )
                top_bar.addWidget(lvl_label)
                top_bar.addWidget(self.log_level_combo)
                top_bar.addStretch(1)
                logs_layout.addLayout(top_bar)
                self.logs_view = QTextEdit()
                self.logs_view.setReadOnly(True)self.logs_view.setObjectName("LogsView")
                logs_layout.addWidget(self.logs_view, 1)
                pv.addLayout(logs_layout)
                self._init_log_handler()if key == "section_recipients":
                pv.removeWidget(placeholder)
                placeholder.deleteLater()
                self.recipients_view = RecipientsView(self.lang_manager)
                pv.addWidget(self.recipients_view, 1)if key == "section_templates":
                pv.removeWidget(placeholder)
                placeholder.deleteLater()
                self.template_preview = TemplatePreview(self.lang_manager)
                pv.addWidget(self.template_preview, 1)if key == "section_settings":
                pv.removeWidget(placeholder)
                placeholder.deleteLater()
                self.settings_panel = SettingsPanel(
                    self.lang_manager, self.theme_manager
                )
                self.settings_panel.themeModeChanged.connect(
                    self._on_theme_mode_changed
                )
                self.settings_panel.scaleChanged.connect(self._on_ui_scale_changed)
                self.settings_panel.languageChanged.connect(
                    self.lang_manager.set_language
                )
                pv.addWidget(self.settings_panel, 1)
            pv.addStretch(1)
            self.stack.addWidget(page)
        layout.addWidget(sidebar)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(root)
        self.list_widget.setCurrentRow(0)

    # ---------------- Sidebar / Navigation -----------------
    def _on_section_changed(self, index: int):"""Внутренний метод для on section changed.
        """Выполняет  on section changed."""

    Args:
        index: Параметр для index"""
        self.stack.setCurrentIndex(index)

    def apply_theme(self, dark: bool):"""Apply theme to the main window and all child components."""
        """Выполняет apply theme."""
        app = QApplication.instance()
        if app:

            styles.apply_palette(app, dark)

        # Apply theme to custom componentsif hasattr(self, "stats_panel"):
            self.stats_panel.apply_theme(dark)if hasattr(self, "settings_panel"):
            self.settings_panel.apply_theme(dark)if hasattr(self, "recipients_view"):
            self.recipients_view.apply_theme(dark)if hasattr(self, "template_preview"):
            self.template_preview.apply_theme(dark)

        # Update quota bar stylingif hasattr(self, "quota_bar"):
            self._update_quota_styling()

    def _update_quota_styling(self):"""Update quota bar styling based on current usage percentage."""if not hasattr(self, "quota_bar"):
        """Выполняет  update quota styling."""
            return

        current_value = self.quota_bar.value()
        if current_value >= 95:
            self.quota_bar.setStyleSheet("QProgressBar::chunk { background: #d9534f; } QProgressBar { text-align: center; }"
            )
        elif current_value >= 80:
            self.quota_bar.setStyleSheet("QProgressBar::chunk { background: #e3b341; } QProgressBar { text-align: center; }"
            )
        else:self.quota_bar.setStyleSheet("")

    # ---------------- Translation -----------------
    # ---------------- Logging -----------------
    def _init_log_handler(self):"""Внутренний метод для init log handler.

    Args:"""if hasattr(self, "_qt_log_handler"):
            return
        handler = QtLogHandler()
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
        handler.setFormatter(formatter)
        self._qt_log_handler = install_qt_log_handler(handler)
        self._qt_log_handler.emitter.messageEmitted.connect(self._on_log_message)
        for level, msg in self._qt_log_handler.buffer:
            self._append_log_line(level, msg)

    def _on_log_message(self, level: str, text: str):"""Внутренний метод для on log message.
        """Выполняет  on log message."""

    Args:
        level: Параметр для level
        text: Параметр для text"""if not hasattr(self, "log_level_combo"):
            returnorder = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        current = self.log_level_combo.currentText()
        if order.index(level) < order.index(current):
            return
        self._append_log_line(level, text)

    def _append_log_line(self, level: str, text: str):"""Внутренний метод для append log line.
        """Выполняет  append log line."""

    Args:
        level: Параметр для level
        text: Параметр для text"""if not hasattr(self, "logs_view"):
            return
        color = {"DEBUG": "#888888","""INFO": "#ffffff" if self.theme_manager.is_dark() else "#000000","""WARNING": "#e3b341","""ERROR": "#d9544d","""CRITICAL": "#ff0000",""}.get(level, "#cccccc")
        self.logs_view.append(f"<span style='color:{color}'><b>{level}</b> {text}</span>"
        )
        self.logs_view.verticalScrollBar().setValue(
            self.logs_view.verticalScrollBar().maximum()
        )

    def _on_log_level_changed(self, level: str):"""Внутренний метод для on log level changed.
        """Выполняет  on log level changed."""

    Args:
        level: Параметр для level"""if not hasattr(self, "_qt_log_handler"):
            return
        self.logs_view.clear()order = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for lvl, msg in self._qt_log_handler.buffer:
            if order.index(lvl) < order.index(level):
                continue
            self._append_log_line(lvl, msg)

    # ---------------- Campaign Form Helpers -----------------
    def _form_row(self, label_text: str, *widgets):"""Внутренний метод для form row.
        """Выполняет  form row."""

    Args:
        label_text: Параметр для label text"""
        row = QHBox()
        lbl = QLabel(label_text)
        row.addWidget(lbl)
        for w in widgets:
            stretch = 1 if isinstance(w, (QLineEdit, QSpinBox)) else 0
            row.addWidget(w, stretch)
        return row

    def _form_row_component(self, field_widget: QWidget, button_widget: QWidget):"""Внутренний метод для form row component.
        """Выполняет  form row component."""

    Args:
        field_widget: Параметр для field widget
        button_widget: Параметр для button widget"""
        row = QHBox()
        row.addWidget(field_widget, 1)
        row.addWidget(button_widget)
        return row
def _choose_file_ft(self, field: FloatingTextField, filter_: str = "All (*.*)"):"""Внутренний метод для choose file ft.
    """Выполняет  choose file ft."""

    Args:
        field: Параметр для field
        filter_: Параметр для filter """
        path,_ = QFileDialog.getOpenFileName(self,self.lang_manager.t("select"),"", filter_
        )
        if path:
            field.setText(path)
def _choose_file(self, line_edit: QLineEdit, filter_: str = "All (*.*)"):"""Внутренний метод для choose file.
    """Выполняет  choose file."""

    Args:
        line_edit: Параметр для line edit
        filter_: Параметр для filter """
        path,_ = QFileDialog.getOpenFileName(self,self.lang_manager.t("select"),"", filter_
        )
        if path:
            line_edit.setText(path)

    # ---------------- Campaign Logic -----------------
    def _start_campaign(self):"""Внутренний метод для start campaign.

    Args:"""
        if self._mailer.is_running():
            return
        file_path = self.recipients_path.text().strip()
        if not file_path:self.progress_label.setText(self.lang_manager.t("no_file"))
            return
        recipients = self._load_recipients(file_path)
        if not recipients:self.progress_label.setText(self.lang_manager.t("empty_recipients"))
            return
        template = self.template_path.text().strip()subject = self.subject_edit.text().strip() or self.lang_manager.t("no_subject")
        concurrency = self.concurrent_spin.value()
        dry = self.dry_run_switch.isChecked()
        total = len(recipients)
        self._current_total = total
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(total if total > 0 else 100)if hasattr(self, "stats_panel"):
            self.stats_panel.reset(total)
        self._mailer.start(
            recipients = recipients,
            template_name = template,
            subject = subject,
            dry_run = dry,concurrency = concurrency,"
            ")
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)self.progress_label.setText(self.lang_manager.t("sending"))
        self.progress_ring.setVisible(True)
        self.progress_ring.setIndeterminate(True)

    def _cancel_campaign(self):"""Внутренний метод для cancel campaign.

    Args:"""
        if self._mailer.is_running():
            self._mailer.cancel()self.progress_label.setText(self.lang_manager.t("cancelling"))
            self.progress_ring.setVisible(True)
            self.progress_ring.setIndeterminate(True)

    def _load_recipients(self, path: str):"""Внутренний метод для load recipients.
        """Выполняет  load recipients."""

    Args:
        path: Параметр для path"""loaders = {".csv": CSVLoader(), ".xlsx": ExcelLoader(), ".json": JSONLoader()}
        ext = Path(path).suffix.lower()
        loader = loaders.get(ext)
        if not loader:
            return []
        data = loader.load(path)
        valid, errors = validate_email_list(r.email for r in data)
        if errors:logging.getLogger("mailing.gui").warning("Filtered invalid: %d", len(errors)
            )
        m = {r.email: r for r in data}
        return [m[v] for v in valid if v in m]

    # ---------------- MailerService Callbacks -----------------
    def _on_mailer_started(self):"""Внутренний метод для on mailer started.

    Args:"""logging.getLogger("mailing.gui").info("Campaign started")

    def _on_mailer_progress(self, event: dict):"""Внутренний метод для on mailer progress.
        """Выполняет  on mailer progress."""

    Args:
        event: Параметр для event"""stats = event.get("stats", {})succ = stats.get("success", 0)fail = stats.get("failed", 0)total = stats.get("total", 0)
        if total:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(succ + fail)
            # determinate ring
            self.progress_ring.setIndeterminate(False)
            self.progress_ring.setMaximum(total)
            self.progress_ring.setValue(succ + fail)
        self.progress_label.setText(
            self.lang_manager.t("progress_stats",sent = succ + fail,total = total,
                ok = succ, err = fail
            )
        )if hasattr(self, "stats_panel"):
            self.stats_panel.update_stats(stats)
        # dashboard quick updateif hasattr(self, "card_sent"):
            self.card_sent.setValue(str(succ))
            # open % and fail can be updated if present in stats
            if total:open_p = stats.get("opened", 0)if hasattr(self, "card_open"):
                    perc = (open_p / total) * 100 if total else 0self.card_open.setValue(f"{perc:.0f}%")if hasattr(self, "card_fail"):
                    self.card_fail.setValue(str(fail))
        # daily quota updateif hasattr(self, "quota_bar"):used = stats.get("daily_used")limit = stats.get("daily_limit") or 100
            if used is not None and limit:
                pct = int((used / limit) * 100)
                self.quota_bar.setValue(min(pct, 100))self.quota_bar.setFormat(f"{used} / {limit} ({pct}%)")
                # Style thresholds
                if pct >= 95:
                    self.quota_bar.setStyleSheet("QProgressBar::chunk { background: #d9534f; } QProgressBar { text-align: center; }"
                    )
                elif pct >= 80:
                    self.quota_bar.setStyleSheet("QProgressBar::chunk { background: #e3b341; } QProgressBar { text-align: center; }"
                    )
                else:self.quota_bar.setStyleSheet("")

    def _on_mailer_finished(self, stats: dict):"""Внутренний метод для on mailer finished.
        """Выполняет  on mailer finished."""

    Args:
        stats: Параметр для stats"""
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)self.progress_label.setText(self.lang_manager.t("finished"))
        self.progress_ring.setVisible(False)if hasattr(self, "stats_panel"):
            self.stats_panel.update_stats(stats)logging.getLogger("mailing.gui").info("Campaign finished: %s", stats)

    def _on_mailer_error(self, msg: str, stats: dict):"""Внутренний метод для on mailer error.
        """Выполняет  on mailer error."""

    Args:
        msg: Параметр для msg
        stats: Параметр для stats"""
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)self.progress_label.setText(f"Error: {msg}")
        self.progress_ring.setVisible(False)logging.getLogger("mailing.gui").error("Campaign error: %s", msg)

    def _on_mailer_cancelled(self, stats: dict):"""Внутренний метод для on mailer cancelled.
        """Выполняет  on mailer cancelled."""

    Args:
        stats: Параметр для stats"""
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)self.progress_label.setText(self.lang_manager.t("cancelled"))
        self.progress_ring.setVisible(False)logging.getLogger("mailing.gui").info("Campaign cancelled")

    # ---------------- Theme / Settings -----------------
    def _on_theme_mode_changed(self, mode: str):"""Внутренний метод для on theme mode changed.
        """Выполняет  on theme mode changed."""

    Args:
        mode: Параметр для mode"""if mode == "auto":
            returnelif mode == "dark":
            self.theme_manager.set_dark(True)elif mode == "light":
            self.theme_manager.set_dark(False)

    def _on_ui_scale_changed(self, scale: float):"""Внутренний метод для on ui scale changed.
        """Выполняет  on ui scale changed."""

    Args:
        scale: Параметр для scale"""
        for w in self.findChildren(QWidget):
            f = w.font()
            base = f.pointSizeF() or 10
            f.setPointSizeF(base * scale)
            w.setFont(f)

    # -------- Theme palette changed (animate cross-fade) --------
    def _on_palette_changed(self, palette):"""Внутренний метод для on palette changed.
        """Выполняет  on palette changed."""

    Args:
        palette: Параметр для palette"""
        # обновляем глобальную Qt палитру + запускаем анимацию
        self._apply_global_palette()
        self._animate_theme_transition()

    def _animate_theme_transition(self):"""Внутренний метод для animate theme transition.

    Args:"""
        if not self.isVisible():
            return
        pix = self.grab()
        overlay = QLabel(self)
        overlay.setPixmap(pix)
        overlay.setScaledContents(False)
        overlay.setGeometry(self.rect())
        overlay.raise_()
        effect = QGraphicsOpacityEffect(overlay)
        overlay.setGraphicsEffect(effect)anim = QPropertyAnimation(effect,b"opacity", overlay)
        anim.setDuration(320)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)

        def _cleanup():"""Внутренний метод для cleanup."""
            """Выполняет  cleanup."""
            overlay.deleteLater()

        anim.finished.connect(_cleanup)
        anim.start(QPropertyAnimation.DeleteWhenStopped)
        self._theme_overlay = overlay  # type: ignore[attr-defined]
        self._theme_anim = anim  # type: ignore[attr-defined]

    def _apply_global_palette(self):"""Внутренний метод для apply global palette.

    Args:"""
        app = QApplication.instance()
        if not app:
            return
        styles.apply_palette(app, self.theme_manager.is_dark())
