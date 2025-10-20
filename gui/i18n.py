from PySide6.QtCore import QObject, Signal
from __future__ import annotations
from typing import Dict

# Простой словарный i18n. Ключи стабильные (snake_case)
_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {"app_title": "Resend Mailing Console","""section_campaigns": "Campaigns","""section_recipients": "Recipients","""section_templates": "Templates","""section_logs": "Logs","""section_settings": "Settings","""toggle_theme": "Toggle Theme","""start_campaign_demo": "Start campaign (demo)","""placeholder_section": "Section: {name}\n(Placeholder UI)","""sending": "Sending","""ready": "Done","""cancelled": "Cancelled","""language": "Language","""log_level": "Level","""recipients_file": "Recipients file","""template_file": "Template file","""subject": "Subject","""concurrency": "Concurrency","""dry_run": "Dry run","""start": "Start","""cancel": "Cancel","""idle": "Idle","""finished": "Finished","""cancelling": "Cancelling...","""no_file": "No file selected","""empty_recipients": "Recipients list is empty","""no_subject": "No subject","""select": "Select","""loaded_n_recipients": "Loaded: {n} recipients","""progress_stats": "{sent}/{total} OK:{ok} ERR:{err}","""filter_placeholder": "Filter emails...","""recipients_stats": "Total: {total}  Valid: {valid}  Invalid: {invalid}","""others_domains": "Others","""template_preview": "Template Preview","""open_template": "Open Template","""raw_mode": "Raw","""rendered_mode": "Rendered","""placeholders": "Placeholders","""variables": "Variables","""no_template_loaded": "No template loaded","""watching": "Watching: {path}","""stats_total": "Total","""stats_sent": "Sent","""stats_success": "Success","""stats_failed": "Failed","""stats_rate": "Rate","""stats_elapsed": "Elapsed","""stats_eta": "ETA","""stats_per_sec": "/s","""settings_title": "Settings","""theme_light": "Light","""theme_dark": "Dark","""theme_auto": "Auto","""ui_scale": "UI Scale","""language_label": "Language","""daily_quota": "Daily quota",},"
            ""ru": {"app_title": "Resend Консоль Рассылки","""section_campaigns": "Кампании","""section_recipients": "Получатели","""section_templates": "Шаблоны","""section_logs": "Логи","""section_settings": "Настройки","""toggle_theme": "Тема","""start_campaign_demo": "Запустить рассылку (демо)","""placeholder_section": "Раздел: {name}\n(Временная заглушка)","""sending": "Отправка","""ready": "Готово","""cancelled": "Отменено","""language": "Язык","""log_level": "Уровень","""recipients_file": "Файл получателей","""template_file": "Файл шаблона","""subject": "Тема письма","""concurrency": "Параллелизм","""dry_run": "Тест (без отправки)","""start": "Старт","""cancel": "Отмена","""idle": "Ожидание","""finished": "Завершено","""cancelling": "Отмена...","""no_file": "Файл не выбран","""empty_recipients": "Список получателей пуст","""no_subject": "Без темы","""select": "Выбрать","""loaded_n_recipients": "Загружено: {n} получателей","""progress_stats": "{sent}/{total} OK:{ok} ERR:{err}","""filter_placeholder": "Фильтр email...","""recipients_stats": "Всего: {total}  Валидных: {valid}  Невалидных: {invalid}","""others_domains": "Прочие","""template_preview": "Предпросмотр шаблона","""open_template": "Открыть шаблон","""raw_mode": "Исходник","""rendered_mode": "Рендер","""placeholders": "Плейсхолдеры","""variables": "Переменные","""no_template_loaded": "Шаблон не загружен","""watching": "Отслеживается: {path}","""stats_total": "Всего","""stats_sent": "Отправлено","""stats_success": "Успешно","""stats_failed": "Ошибки","""stats_rate": "Скорость","""stats_elapsed": "Прошло","""stats_eta": "Осталось","""stats_per_sec": "/с","""settings_title": "Настройки","""theme_light": "Светлая","""theme_dark": "Тёмная","""theme_auto": "Авто","""ui_scale": "Масштаб UI","""language_label": "Язык","""daily_quota": "Дневной лимит",},"
            "}
DEFAULT_LANG = "ru"


class LanguageManager(QObject):"""Класс LanguageManager наследующий от QObject."""
    """Класс LanguageManager."""
    languageChanged = Signal(str)

    def __init__(self, lang: str | None = None):"""Внутренний метод для  init  .
        """Инициализирует объект."""

    Args:
        lang: Параметр для lang"""
        super().__init__()
        self._lang = lang or DEFAULT_LANG

    def set_language(self, lang: str):"""выполняет set language.
        """Выполняет set language."""

    Args:
        lang: Параметр для lang"""
        if lang not in _TRANSLATIONS:
            return
        if lang != self._lang:
            self._lang = lang
            self.languageChanged.emit(lang)

    def language(self) -> str:"""выполняет language.
        """Выполняет language."""

    Args:

    Returns:
        str: Результат выполнения операции"""
        return self._lang

    def t(self, key: str, **kwargs) -> str:"""выполняет t.
        """Выполняет t."""

    Args:
        key: Параметр для key

    Returns:
        str: Результат выполнения операции"""
        bundle = _TRANSLATIONS.get(self._lang, {})
        text = bundle.get(key, key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text

    def available_languages(self):"""выполняет available languages.

    Args:"""
        return list(_TRANSLATIONS.keys())
