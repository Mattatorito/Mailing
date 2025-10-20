from PySide6.QtCore import QRegularExpression
from __future__ import annotations

from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont

class HtmlHighlighter(QSyntaxHighlighter):
    """Простая подсветка HTML/templating конструкций.
    Подсвечивает:
      - теги <tag>
      - закрывающие теги </tag>
      - атрибуты и их значения
      - строки
      - HTML комментарии
      - Jinja-подобные {{ ... }} и {% ... %}"""

    def __init__(self, document):"""Инициализирует объект.
        """Инициализирует объект."""

        Args:
            document: Параметр для document"""
        super().__init__(document)
        self.rules = []

        # Форматы
        tag_format = QTextCharFormat()tag_format.setForeground(QColor("#60A5FA"))  # голубой
        tag_format.setFontWeight(QFont.Bold)

        attr_format = QTextCharFormat()attr_format.setForeground(QColor("#FBBF24"))  # янтарный

        value_format = QTextCharFormat()value_format.setForeground(QColor("#34D399"))  # зеленый

        comment_format = QTextCharFormat()comment_format.setForeground(QColor("#6B7280"))  # серый
        comment_format.setFontItalic(True)

        string_format = QTextCharFormat()string_format.setForeground(QColor("#F472B6"))  # розовый

        jinja_format = QTextCharFormat()jinja_format.setForeground(QColor("#A78BFA"))  # сиреневый
        jinja_format.setFontWeight(QFont.Bold)

        # Паттерны
        self.rules.append((QRegularExpression(r"</?\b[\w:-]+"), tag_format)
        )  # начало тегаself.rules.append((QRegularExpression(r"/>"),
            tag_format))  # self-closeself.rules.append((QRegularExpression(r">"), tag_format))  # конец тега
        self.rules.append((QRegularExpression(r"\b[\w:-]+(?==)"), attr_format)
        )  # имя атрибута
        self.rules.append((QRegularExpression(r"=\s*\"[^\"]*\""), value_format))  # значение в "+"
        self.rules.append((QRegularExpression(r"=\s*'[^']*'"), value_format)
        )  # значение в ''
        self.rules.append(
            (QRegularExpression(r"\{{2}[^}]*\}{2}"), jinja_format)
        )  # {{ ... }}
        self.rules.append((QRegularExpression(r"\{%[^%]*%\}"), jinja_format)
        )  # {% ... %}
self.comment_start = QRegularExpression(r"<!--")self.comment_end = QRegularExpression(r"-->")
        self.comment_format = comment_format
        self.string_format = string_format

    def highlightBlock(self, text: str):"""выполняет highlightBlock.
        """Выполняет highlightBlock."""

        Args:
            text: Параметр для text"""
        # Правила одиночных паттернов
        for pattern, fmt in self.rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)
# Подсветка строк ("...") и ('...') отдельно, чтобы не конфликтовалоfor quote_pat in (r'"([^"\\]|\\.)*"', r"'([^'\\]|\\.)*'"):
            it = QRegularExpression(quote_pat).globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(
                    m.capturedStart(), m.capturedLength(), self.string_format
                )

        # Многострочные комментарии <!-- -->
        self.setCurrentBlockState(0)
        start = 0
        if self.previousBlockState() != 1:
            start_match = self.comment_start.match(text)
            start = start_match.capturedStart() if start_match.hasMatch() else -1
        else:
            start = 0
        while start >= 0:
            end_match = self.comment_end.match(text, start + 4)
            if not end_match.hasMatch():
                # до конца
                length = len(text) - start
                self.setFormat(start, length, self.comment_format)
                self.setCurrentBlockState(1)
                break
            else:
                end = end_match.capturedStart()
                length = end - start + 3
                self.setFormat(start, length, self.comment_format)
                start_match = self.comment_start.match(text, end + 3)
                start = start_match.capturedStart() if start_match.hasMatch() else -1
