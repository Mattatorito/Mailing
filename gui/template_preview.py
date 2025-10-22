from __future__ import annotations
from PySide6.QtCore import Qt, QFileSystemWatcher, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextBrowser, QListWidget, QSplitter, QButtonGroup, QRadioButton, QFileDialog
)
from jinja2 import meta
from templating.engine import TemplateEngine
from pathlib import Path
import re
import logging

PLACEHOLDER_REGEX = re.compile(r"{{\s*([a-zA-Z0-9_\.]+)\s*}}")

class TemplatePreview(QWidget):
    def __init__(self, lang_manager, templates_dir: str | None = None):
        super().__init__()
        self.lang = lang_manager
        self.templates_dir = templates_dir or str(Path.cwd() / 'samples')
        self.engine = TemplateEngine(self.templates_dir)
        self._current_path: Path | None = None
        self._raw_source = ''
        self._watcher = QFileSystemWatcher()
        self._watcher.fileChanged.connect(self._on_file_changed)
        self._pending_reload = False
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        self.open_btn = QPushButton(self.lang.t('open_template'))
        self.open_btn.clicked.connect(self._open_file)
        self.mode_group = QButtonGroup(self)
        self.raw_radio = QRadioButton(self.lang.t('raw_mode'))
        self.rendered_radio = QRadioButton(self.lang.t('rendered_mode'))
        self.mode_group.addButton(self.raw_radio)
        self.mode_group.addButton(self.rendered_radio)
        self.raw_radio.setChecked(True)
        self.raw_radio.toggled.connect(self._update_view_mode)
        top.addWidget(self.open_btn)
        top.addWidget(self.raw_radio)
        top.addWidget(self.rendered_radio)
        top.addStretch(1)
        self.status_label = QLabel(self.lang.t('no_template_loaded'))
        top.addWidget(self.status_label)
        layout.addLayout(top)

        splitter = QSplitter()
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        side_panel = QVBoxLayout()
        self.vars_label = QLabel(self.lang.t('variables'))
        self.vars_list = QListWidget()
        self.placeholders_label = QLabel(self.lang.t('placeholders'))
        self.placeholders_list = QListWidget()
        sp_widget = QWidget()
        sp_widget.setLayout(side_panel)
        side_panel.addWidget(self.vars_label)
        side_panel.addWidget(self.vars_list, 1)
        side_panel.addWidget(self.placeholders_label)
        side_panel.addWidget(self.placeholders_list, 1)
        splitter.addWidget(self.browser)
        splitter.addWidget(sp_widget)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter, 1)

    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, self.lang.t('open_template'), self.templates_dir, 'Templates (*.j2 *.html *.txt)')
        if not path:
            return
        self._load_template(Path(path))

    def _load_template(self, path: Path):
        try:
            text = path.read_text(encoding='utf-8')
        except Exception as e:
            logging.getLogger('mailing.gui').error('Failed to read template: %s', e)
            return
        self._current_path = path
        self._raw_source = text
        # watcher
        if path.as_posix() not in self._watcher.files():
            self._watcher.addPath(path.as_posix())
        self.status_label.setText(self.lang.t('watching', path=path.name))
        self._extract_meta()
        self._render()

    def _extract_meta(self):
        # find placeholders manually (quick) + jinja variables
        self.placeholders_list.clear()
        for m in PLACEHOLDER_REGEX.finditer(self._raw_source):
            self.placeholders_list.addItem(m.group(1))
        # jinja parse
        try:
            ast = self.engine.env.parse(self._raw_source)
            vars_ = sorted(meta.find_undeclared_variables(ast))
        except Exception:
            vars_ = []
        self.vars_list.clear()
        for v in vars_:
            self.vars_list.addItem(v)

    def _render(self):
        if self.raw_radio.isChecked():
            # highlight placeholders
            html = self._raw_source
            def repl(m):
                return f"<span style='background:#264653;color:#e9c46a;padding:1px 3px;border-radius:3px;'>{{{{ {m.group(1)} }}}}</span>"
            html = PLACEHOLDER_REGEX.sub(repl, html)
            self.browser.setHtml(f"<pre style='font-family: SF Mono, Menlo, monospace;'>{html}</pre>")
        else:
            # Produce a dummy context using vars list
            ctx = {item.text(): f"demo_{i}" for i, item in enumerate([self.vars_list.item(j) for j in range(self.vars_list.count())])}
            try:
                rendered = self.engine.render(self._current_path.name if self._current_path else '', ctx).body_html
            except Exception as e:
                rendered = f"<b style='color:#d9544d'>Render error:</b> {e}" if self._current_path else ''
            self.browser.setHtml(rendered)

    def _update_view_mode(self):
        self._render()

    def _on_file_changed(self, path: str):
        # debounce to avoid duplicate events
        if self._pending_reload:
            return
        self._pending_reload = True
        QTimer.singleShot(250, lambda: self._reload_path(path))

    def _reload_path(self, path: str):
        self._pending_reload = False
        if not self._current_path or self._current_path.as_posix() != path:
            return
        try:
            new_text = self._current_path.read_text(encoding='utf-8')
        except Exception:
            return
        if new_text != self._raw_source:
            self._raw_source = new_text
            self._extract_meta()
            self._render()

    def retranslate(self):
        self.open_btn.setText(self.lang.t('open_template'))
        self.raw_radio.setText(self.lang.t('raw_mode'))
        self.rendered_radio.setText(self.lang.t('rendered_mode'))
        self.vars_label.setText(self.lang.t('variables'))
        self.placeholders_label.setText(self.lang.t('placeholders'))
        if not self._current_path:
            self.status_label.setText(self.lang.t('no_template_loaded'))
        else:
            self.status_label.setText(self.lang.t('watching', path=self._current_path.name))
        self._render()

    def apply_theme(self, dark: bool):
        """Apply theme styling to the template preview."""
        # Update browser styling based on theme
        if dark:
            self.browser.setStyleSheet("""
                QTextBrowser {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                    border: 1px solid #444;
                }
            """)
        else:
            self.browser.setStyleSheet("""
                QTextBrowser {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #ddd;
                }
            """)
        
        # Update list widgets styling
        list_style = """
            QListWidget {
                background-color: transparent;
                border: 1px solid %s;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 4px;
                border-radius: 3px;
            }
            QListWidget::item:selected {
                background-color: rgba(0, 122, 255, 0.2);
            }
        """ % ("#444" if dark else "#ddd")
        
        self.vars_list.setStyleSheet(list_style)
        self.placeholders_list.setStyleSheet(list_style)
        
        # Re-render to update syntax highlighting colors
        self._render()
