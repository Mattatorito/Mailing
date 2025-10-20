from PySide6.QtCore import Qt, Signal
from __future__ import annotations

from PySide6.QtWidgets import (

    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QSlider,
    QFrame,
)


class SettingsPanel(QWidget):
    """Класс SettingsPanel наследующий от QWidget."""
    themeModeChanged = Signal(str)  # 'light' | 'dark' | 'auto'
    scaleChanged = Signal(float)
    languageChanged = Signal(str)

    def __init__(self, lang_manager, theme_manager):
    """Внутренний метод для  init  .

    Args:
        lang_manager: Параметр для lang manager
        theme_manager: Параметр для theme manager"""
        super().__init__()
        self.lang = lang_manager
        self.theme_manager = theme_manager
        self._init_ui()

    def _init_ui(self):"""Внутренний метод для init ui.

    Args:"""
        layout = QVBoxLayout(self)title = QLabel(self.lang.t("settings_title"))title.setObjectName("settingsTitle")
        layout.addWidget(title)

        # Theme mode
        theme_row = QHBoxLayout()theme_label = QLabel(self.lang.t("toggle_theme"))
        self.theme_combo = QComboBox()self.theme_combo.addItem(self.lang.t("theme_auto"),
            "auto")self.theme_combo.addItem(self.lang.t("theme_light"),
            "light")self.theme_combo.addItem(self.lang.t("theme_dark"), "dark")
        self.theme_combo.currentIndexChanged.connect(self._on_theme_mode)
        theme_row.addWidget(theme_label)
        theme_row.addWidget(self.theme_combo)
        layout.addLayout(theme_row)

        # Language
        lang_row = QHBoxLayout()lang_label = QLabel(self.lang.t("language_label"))
        self.lang_combo = QComboBox()
        for l in self.lang.available_languages():
            self.lang_combo.addItem(l, l)
        self.lang_combo.setCurrentText(self.lang.language())
        self.lang_combo.currentTextChanged.connect(self.languageChanged.emit)
        lang_row.addWidget(lang_label)
        lang_row.addWidget(self.lang_combo)
        layout.addLayout(lang_row)

        # UI Scale
        scale_row = QHBoxLayout()scale_label = QLabel(self.lang.t("ui_scale"))
        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setRange(80, 160)  # percent
        self.scale_slider.setValue(100)
        self.scale_slider.valueChanged.connect(self._on_scale)
        scale_row.addWidget(scale_label)
        scale_row.addWidget(self.scale_slider, 1)
        layout.addLayout(scale_row)

        layout.addStretch(1)

    def _on_theme_mode(self):"""Внутренний метод для on theme mode.

    Args:"""
        mode = self.theme_combo.currentData()
        self.themeModeChanged.emit(mode)

    def _on_scale(self, value: int):"""Внутренний метод для on scale.
        """Выполняет  on scale."""

    Args:
        value: Параметр для value"""
        self.scaleChanged.emit(value / 100.0)

    def retranslate(self):"""выполняет retranslate.

    Args:"""
        # Rebuild static texts (simple approach)self.findChild(QLabel, "settingsTitle").setText(self.lang.t("settings_title"))
        # For simplicity we won't rebuild combo contents fully here.
        ...

    def apply_theme(self, dark: bool):
        """Apply theme styling to the settings panel."""
        # Update combo box stylingcombo_style = """
            QComboBox {
                border: 1px solid %s;
                border-radius: 6px;
                padding: 4px 8px;
                background-color: %s;
                color: %s;
            }
            QComboBox:hover {
                border-color: rgba(0, 122, 255, 0.6);
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }""" % ("#444" if dark else "#ddd","""#2d2d2d" if dark else "#ffffff","""#d4d4d4" if dark else "#000000","")

        self.theme_combo.setStyleSheet(combo_style)
        self.lang_combo.setStyleSheet(combo_style)

        # Update slider styling
        slider_style = """
            QSlider::groove:horizontal {
                border: 1px solid %s;
                height: 6px;
                background: %s;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: rgba(0, 122, 255, 0.9);
                border: 1px solid rgba(0, 122, 255, 1.0);
                width: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: rgba(0, 132, 255, 1.0);
            }""" % ("#444" if dark else "#ddd","""#3d3d3d" if dark else "#f0f0f0",
        )

        self.scale_slider.setStyleSheet(slider_style)
