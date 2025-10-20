from __future__ import annotations
from pathlib import Path
from typing import Optional
import asyncio, threading

import customtkinter as ctk
import tkinter as tk

from .theme import set_theme, apply_font, SPACING_MD, SPACING_LG
from .visual_fx import FadeInController, PulseBar
from data_loader.csv_loader import CSVLoader
from data_loader.excel_loader import ExcelLoader
from data_loader.json_loader import JSONLoader
from gui.i18n import LanguageManager
from mailing.sender import run_campaign, CampaignController
from stats.aggregator import StatsAggregator
from validation.email_validator import validate_email_list

LOADERS = {".csv": CSVLoader(), ".xlsx": ExcelLoader(), ".json": JSONLoader()}

class CampaignThread(threading.Thread):
    """Класс CampaignThread."""
    def __init__(
    """Инициализирует объект."""
    self,app: "App",
    recipients,
    template_name: str,
    subject: str,
    dry_run: bool,
    concurrency: int,
    ):
    super().__init__(daemon = True)
    self.app = app
    self.recipients = recipients
    self.template_name = template_name
    self.subject = subject
    self.dry_run = dry_run
    self.concurrency = concurrency
    self.controller = CampaignController()
    self.stats = StatsAggregator()

    def run(self):
    """Выполняет run."""
    asyncio.run(self._run())

    async def _run(self):
    """Выполняет  run."""
        try:
            async for event in run_campaign(
            recipients = self.recipients,
            template_name = self.template_name,
            subject = self.subject,
            dry_run = self.dry_run,
            concurrency = self.concurrency,
            controller = self.controller,
            ):if event["type"] == "progress":res = event["result"]
                self.stats.add(res)
                snap = self.stats.snapshot()
                    self.app.after(0, lambda s = snap: self.app.update_progress(s))elif event["type"] == "finished":
                snap = self.stats.snapshot()
                    self.app.after(0, lambda s = snap: self.app.finish_campaign(s))elif event["type"] == "error":
                self.app.after(0,lambda: self.app.finish_campaign(event.get("stats", {}))
                )
        except Exception as e:  # noqaself.app.after(0, lambda: self.app.finish_campaign({"error": str(e)}))

class App(ctk.CTk):
    """Класс App."""
    def __init__(self, lang: Optional[str] = None):
    """Инициализирует объект."""
    super().__init__()
    self.lang_manager = LanguageManager(lang)self.title(self.lang_manager.t("app_title"))self.geometry("1100x760")set_theme("system")ctk.set_default_color_theme("blue")
    self._campaign_thread: Optional[CampaignThread] = None
    self._build_ui()
    self.after(
        50, lambda: apply_font(self)
    )  # попытка применить SF Pro немного позже
    # начальная прозрачность и плавное появление
        try:self.attributes("-alpha", 0.85)
        FadeInController(self).start()
        except Exception:
        pass
    self._pulse = None
    self._overlay = None

    def _build_ui(self):
    """Выполняет  build ui."""
    self.grid_rowconfigure(0, weight = 1)
    self.grid_columnconfigure(1, weight = 1)

    sidebar = ctk.CTkFrame(self,width = 200,corner_radius = 0)sidebar.grid(row = 0,
        column = 0, sticky="nswe")
    sidebar.grid_rowconfigure(10, weight = 1)

    self.lang_option = ctk.CTkOptionMenu(
        sidebar,
        values = self.lang_manager.available_languages(),
        command = self._change_lang,
    )
    self.lang_option.set(self.lang_manager.language())
    self.lang_option.grid(row = 0,column = 0,padx = SPACING_MD,pady=(SPACING_MD,6), sticky="ew"
    )
self.file_entry = ctk.CTkEntry(sidebar,
    placeholder_text="recipients.csv")self.file_entry.grid(row = 1,column = 0,
    padx = SPACING_MD,pady = 6,sticky="ew")self.template_entry = ctk.CTkEntry(sidebar,
    placeholder_text="template.html.j2")self.template_entry.grid(row = 2,column = 0,
    padx = SPACING_MD,pady = 6,sticky="ew")self.subject_entry = ctk.CTkEntry(sidebar,
    placeholder_text="Subject")self.subject_entry.grid(row = 3,column = 0,
    padx = SPACING_MD,pady = 6, sticky="ew")
    self.concurrency_slider = ctk.CTkSlider(
        sidebar, from_ = 1, to = 50, number_of_steps = 49
    )
    self.concurrency_slider.set(10)
    self.concurrency_slider.grid(row = 4,column = 0,padx = SPACING_MD,pady = 6, sticky="ew"
    )
    self.dry_var = ctk.BooleanVar(value = False)
    self.dry_check = ctk.CTkCheckBox(sidebar,text="🧪 Dry-run", variable = self.dry_var
    )self.dry_check.grid(row = 5,column = 0,padx = SPACING_MD,pady = 6, sticky="w")

    self.start_btn = ctk.CTkButton(sidebar,text="▶️ Start", command = self._start_campaign
    )self.start_btn.grid(row = 6,column = 0,padx = SPACING_MD,pady = 12, sticky="ew")
    self.cancel_btn = ctk.CTkButton(sidebar,text="⏹ Cancel",state="disabled", command = self._cancel_campaign
    )self.cancel_btn.grid(row = 7,column = 0,padx = SPACING_MD,pady = 6, sticky="ew")
self.progress_label = ctk.CTkLabel(sidebar,text="0 / 0")self.progress_label.grid(row = 8,
    column = 0,padx = SPACING_MD,pady = 6, sticky="w")

    self.progress_bar = ctk.CTkProgressBar(sidebar)
    self.progress_bar.set(0)self.progress_bar.grid(row = 9,column = 0,
        padx = SPACING_MD,pady = 12, sticky="ew")

    # main content placeholderself.content = ctk.CTkFrame(self, fg_color=("gray95", "gray14"))
    self.content.grid(row = 0,column = 1,sticky="nswe",padx=(0,SPACING_LG), pady = SPACING_MD
    )
    self.content.grid_rowconfigure(0, weight = 1)
    self.content.grid_columnconfigure(0, weight = 1)
    self.log_text = ctk.CTkTextbox(self.content)
    self.log_text.grid(row = 0,column = 0,sticky="nswe",padx = SPACING_LG, pady = SPACING_LG
    )
    # Имитация blur: градиентный overlay поверх контента (optionally)
    self._create_overlay()
    # Панель управления прозрачностью
    self.alpha_slider = ctk.CTkSlider(
        self.content,
        from_ = 0.7,
        to = 1.0,
        number_of_steps = 30,
        command = self._on_alpha_change,
    )
    self.alpha_slider.set(0.95)
    self.alpha_slider.grid(row = 1,column = 0,sticky="ew",padx = SPACING_LG,pady=(0, SPACING_LG)
    )

    def _change_lang(self, lang: str):
    """Выполняет  change lang."""
    self.lang_manager.set_language(lang)self.title(self.lang_manager.t("app_title"))

    def _create_overlay(self):
    """Выполняет  create overlay."""
        if self._overlay:
            return
    canvas = tk.Canvas(self.content,highlightthickness = 0,bd = 0,relief="flat", bg=""
    )
    canvas.place(relx = 0, rely = 0, relwidth = 1, relheight = 1)
    # рисуем простой вертикальный градиент (темный -> прозрачный)
    h = 200
        for i in range(h):
        # альфа имитируем подбором оттенка (Tk не умеет rgba напрямую здесь)
        shade = int(255 - (255 * (i / h) * 0.6))color = f"#{shade:02x}{shade:02x}{shade:02x}"
        canvas.create_line(0, i, 2000, i, fill = color)
    canvas.lower()  # оставить ниже текста логов? наоборот поднимем слегкаcanvas.configure(state="disabled")
    self._overlay = canvas

    def _on_alpha_change(self, value):
    """Выполняет  on alpha change."""
        try:self.attributes("-alpha", float(value))
        except Exception:
        pass

    def _start_campaign(self):
    """Выполняет  start campaign."""
        if self._campaign_thread and self._campaign_thread.is_alive():
            return
    file_path = self.file_entry.get().strip()
        if not file_path:
            return
    ext = Path(file_path).suffix.lower()
    loader = LOADERS.get(ext)
        if not loader:self._append_log(f"Unsupported file: {ext}")
            return
    recipients = loader.load(file_path)
        valid, errors = validate_email_list(r.email for r in recipients)
        email_to_rec = {r.email: r for r in recipients}
        recipients = [email_to_rec[v] for v in valid if v in email_to_rec]
        if errors:self._append_log(f"Filtered invalid: {len(errors)}")
    template_name = self.template_entry.get().strip()subject = self.subject_entry.get().strip() or "No subject"
    dry = self.dry_var.get()
    concurrency = int(self.concurrency_slider.get())
    self._campaign_thread = CampaignThread(
        self, recipients, template_name, subject, dry, concurrency
    )
    self._campaign_thread.start()
    self._total = len(recipients)
    self.progress_bar.set(0)self.progress_label.configure(text = f"0 / {self._total}")self.start_btn.configure(state="disabled")self.cancel_btn.configure(state="normal")
    # запуск пульса прогресс-бара
    self._pulse = PulseBar(self.progress_bar)
    self._pulse.start()

    def _cancel_campaign(self):
    """Выполняет  cancel campaign."""
        if self._campaign_thread and self._campaign_thread.is_alive():
        self._campaign_thread.controller.cancel()self._append_log("Cancel requested")

    def update_progress(self, snap):total = snap["total"] or 1done = snap["success"] + snap["failed"]
    """Выполняет update progress."""
    self.progress_bar.set(done / total)
    self.progress_label.configure(text = f"{done} / {total} | ✅ {snap['success']} ❌ {snap['failed']}"
    )

    def finish_campaign(self, snap):self.start_btn.configure(state="normal")self.cancel_btn.configure(state="disabled")if snap.get("error"):self._append_log(f"Error: {snap['error']}")
    """Выполняет finish campaign."""
    else:self._append_log("Finished")
        if self._pulse:
        self._pulse.stop()
        self._pulse = None

    def _append_log(self,text: str):self.log_text.insert("end", text + "\n")self.log_text.see("end")
    """Выполняет  append log."""

def main():
    """Выполняет main."""
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()
