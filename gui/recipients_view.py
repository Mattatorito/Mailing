from __future__ import annotations
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QSize, QSortFilterProxyModel, Signal
from PySide6.QtGui import QColor, QPainter, QFont, QPen
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel, QTableView, QFileDialog,
    QStyleOptionViewItem, QStyledItemDelegate, QHeaderView, QFrame
)
import hashlib
from dataclasses import dataclass
from typing import List, Dict, Sequence
from validation.email_validator import validate_email_list
from data_loader.csv_loader import CSVLoader
from data_loader.excel_loader import ExcelLoader
from data_loader.json_loader import JSONLoader
from pathlib import Path
import logging

@dataclass
class RecipientRow:
    email: str
    name: str | None = None
    valid: bool = True

class RecipientsTableModel(QAbstractTableModel):
    COLS = ["email", "name", "valid", "domain"]

    def __init__(self, rows: List[RecipientRow] | None = None):
        super().__init__()
        self._rows: List[RecipientRow] = rows or []

    def rowCount(self, parent=QModelIndex()):
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()):
        return len(self.COLS)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = self._rows[index.row()]
        col = self.COLS[index.column()]
        if role == Qt.DisplayRole:
            if col == 'email':
                return row.email
            if col == 'name':
                return row.name or ''
            if col == 'valid':
                return '✓' if row.valid else '✕'
            if col == 'domain':
                return row.email.split('@')[-1] if '@' in row.email else ''
        if role == Qt.TextAlignmentRole and col == 'valid':
            return Qt.AlignCenter
        if role == Qt.ForegroundRole and col == 'valid' and not row.valid:
            return QColor('#d9544d')
        return None

    def headerData(self, section: int, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self.COLS[section].title()
        return section + 1

    def setRows(self, rows: List[RecipientRow]):
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

    def rows(self) -> Sequence[RecipientRow]:
        return self._rows

class DomainDistributionBar(QWidget):
    def __init__(self):
        super().__init__()
        self._counts: Dict[str, int] = {}
        self.setMinimumHeight(34)
        self.setToolTip('')

    def setCounts(self, counts: Dict[str, int]):
        self._counts = dict(sorted(counts.items(), key=lambda kv: kv[1], reverse=True))
        self.update()

    def sizeHint(self):
        return QSize(200, 34)

    def _color_for_domain(self, domain: str) -> QColor:
        h = int(hashlib.sha1(domain.encode()).hexdigest(), 16)
        # generate pastel color
        r = 150 + (h % 100)
        g = 120 + ((h >> 8) % 100)
        b = 140 + ((h >> 16) % 100)
        return QColor(r % 255, g % 255, b % 255)

    def mouseMoveEvent(self, event):
        if not self._counts:
            return super().mouseMoveEvent(event)
        total = sum(self._counts.values())
        if not total:
            return
        x = event.position().x()
        w = self.width()
        acc = 0
        for d, c in self._counts.items():
            seg_w = w * (c / total)
            if acc <= x <= acc + seg_w:
                pct = (c / total) * 100
                self.setToolTip(f"{d}: {c} ({pct:.1f}%)")
                break
            acc += seg_w
        super().mouseMoveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        r = self.rect().adjusted(4, 8, -4, -8)
        total = sum(self._counts.values()) or 1
        x = r.x()
        for domain, count in self._counts.items():
            frac = count / total
            w = max(2, int(r.width() * frac))
            color = self._color_for_domain(domain)
            painter.fillRect(x, r.y(), w, r.height(), color)
            if w > 40:
                painter.setPen(Qt.black if color.lightness() > 160 else Qt.white)
                painter.drawText(x + 4, r.center().y() + 5, domain[:18])
            x += w
        # border
        painter.setPen(QPen(QColor('#666'), 1))
        painter.drawRoundedRect(r, 6, 6)
        painter.end()

class ValidityDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        super().paint(painter, option, index)
        if index.column() == 2:  # valid col
            val = index.data(Qt.DisplayRole)
            if val == '✕':
                painter.save()
                painter.setPen(QPen(QColor('#d9544d'), 2))
                r = option.rect.adjusted(6, 6, -6, -6)
                painter.drawLine(r.topLeft(), r.bottomRight())
                painter.drawLine(r.bottomLeft(), r.topRight())
                painter.restore()

class RecipientsView(QWidget):
    recipientsLoaded = Signal(list)

    def __init__(self, lang_manager):
        super().__init__()
        self.lang = lang_manager
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        toolbar = QHBoxLayout()
        self.load_btn = QPushButton(self.lang.t('select'))
        self.load_btn.clicked.connect(self._choose_file)
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText(self.lang.t('filter_placeholder'))
        self.filter_edit.textChanged.connect(self._on_filter_changed)
        self.stats_label = QLabel('')
        toolbar.addWidget(self.load_btn)
        toolbar.addWidget(self.filter_edit, 1)
        toolbar.addWidget(self.stats_label)
        layout.addLayout(toolbar)

        self.distribution = DomainDistributionBar()
        layout.addWidget(self.distribution)

        self.model = RecipientsTableModel([])
        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy.setFilterKeyColumn(-1)

        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setItemDelegate(ValidityDelegate())
        layout.addWidget(self.table, 1)

    def _choose_file(self):
        path, _ = QFileDialog.getOpenFileName(self, self.lang.t('select'), '', 'Data (*.csv *.xlsx *.json)')
        if not path:
            return
        self._load(path)

    def _load(self, path: str):
        loaders = {'.csv': CSVLoader(), '.xlsx': ExcelLoader(), '.json': JSONLoader()}
        ext = Path(path).suffix.lower()
        loader = loaders.get(ext)
        if not loader:
            return
        data = loader.load(path)
        valid_emails, errors = validate_email_list(r.email for r in data)
        valid_set = set(valid_emails)
        rows = [RecipientRow(email=r.email, name=getattr(r, 'name', ''), valid=r.email in valid_set) for r in data]
        self.model.setRows(rows)
        self._update_stats(rows)
        self._update_distribution(rows)
        self.recipientsLoaded.emit(rows)
        logging.getLogger('mailing.gui').info('Recipients loaded: %d (invalid %d)', len(rows), len(errors))

    def _update_stats(self, rows: Sequence[RecipientRow]):
        total = len(rows)
        invalid = len([r for r in rows if not r.valid])
        valid = total - invalid
        self.stats_label.setText(self.lang.t('recipients_stats', total=total, valid=valid, invalid=invalid))

    def _update_distribution(self, rows: Sequence[RecipientRow]):
        counts: Dict[str, int] = {}
        for r in rows:
            if '@' in r.email:
                d = r.email.split('@')[-1]
                counts[d] = counts.get(d, 0) + 1
        # top 12 + others collapsed
        if len(counts) > 12:
            sorted_items = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
            top = dict(sorted_items[:11])
            others = sum(c for _, c in sorted_items[11:])
            top[self.lang.t('others_domains')] = others
            counts = top
        self.distribution.setCounts(counts)

    def _on_filter_changed(self, text: str):
        # Filter in all columns: override filterAcceptsRow via dynamic regex
        self.proxy.setFilterFixedString(text)

    def retranslate(self):
        self.load_btn.setText(self.lang.t('select'))
        self.filter_edit.setPlaceholderText(self.lang.t('filter_placeholder'))
        # stats_label динамически при следующей загрузке
        # distribution others label handled in update_distribution
        self._update_distribution(self.model.rows())

    def apply_theme(self, dark: bool):
        """Apply theme styling to the recipients view."""
        # Update table styling based on theme
        if dark:
            self.table.setStyleSheet("""
                QTableView {
                    gridline-color: #444;
                    selection-background-color: rgba(0, 122, 255, 0.25);
                }
                QTableView::item:alternate {
                    background-color: rgba(255, 255, 255, 0.05);
                }
            """)
        else:
            self.table.setStyleSheet("""
                QTableView {
                    gridline-color: #ddd;
                    selection-background-color: rgba(0, 122, 255, 0.18);
                }
                QTableView::item:alternate {
                    background-color: rgba(0, 0, 0, 0.03);
                }
            """)
        
        # Update distribution bar
        self.distribution.update()
